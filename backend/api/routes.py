"""
DistriStore — FastAPI Routes
REST endpoints for upload, download, and status.
"""

import base64
import os
import tempfile
from typing import Optional

import uuid

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse

from backend.utils.logger import get_logger

logger = get_logger("api.routes")

router = APIRouter()

# These will be set by main.py at startup
_node = None
_local_store = None
_routing = None


def init_routes(node, local_store, routing):
    """Inject dependencies into routes."""
    global _node, _local_store, _routing
    _node = node
    _local_store = local_store
    _routing = routing


@router.get("/status")
async def get_status():
    """Get node status: peers, chunks, uptime."""
    if not _node:
        raise HTTPException(503, "Node not initialized")
    status = await _node.state.status()
    status["local_chunks"] = _local_store.list_chunks() if _local_store else []
    status["storage_used"] = _local_store.get_storage_size() if _local_store else 0
    
    from backend.utils.config import get_config
    config = get_config()
    status["storage_used_mb"] = round(status["storage_used"] / (1024 * 1024), 2)
    status["storage_max_mb"] = config.storage.max_storage_mb
    status["swarm_auth_active"] = True
    
    return status


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    password: str = Form(""),
):
    """Upload a file: chunk, encrypt, store locally, and replicate."""
    if not _node or not _local_store:
        raise HTTPException(503, "Node not initialized")

    from backend.file_engine.chunker import chunk_file, FileManifest, get_optimal_chunk_size
    from backend.strategies.replication import ReplicationEngine

    # Save uploaded file to temp location
    tmp_dir = tempfile.mkdtemp()
    tmp_path = os.path.join(tmp_dir, file.filename)
    content = await file.read()
    with open(tmp_path, "wb") as f:
        f.write(content)

    try:
        # Get optimal chunk size (Phase 13 Dynamic Chunking)
        file_size = os.path.getsize(tmp_path)
        opt_chunk_size = get_optimal_chunk_size(file_size)

        # Chunk + encrypt
        pwd = password if password else None
        manifest, chunks = chunk_file(tmp_path, chunk_size=opt_chunk_size, password=pwd)

        # Store all chunks locally
        for info, data in zip(manifest.chunks, chunks):
            _local_store.save_chunk(info.chunk_hash, data)
            await _node.state.register_chunk(info.chunk_hash, info.chunk_hash)

        # Save manifest
        _local_store.save_manifest(manifest.file_hash, manifest.to_dict())

        # Replicate to peers if available
        replicated = {}
        peers = await _node.state.get_alive_peers()
        if peers and _routing:
            engine = ReplicationEngine(
                _node.state, _node.conn_mgr, _routing, _local_store
            )
            replicated = await engine.replicate_chunks(manifest, chunks)

        logger.info(f"Uploaded '{file.filename}': {len(chunks)} chunks, hash={manifest.file_hash[:16]}...")

        return {
            "status": "success",
            "file_hash": manifest.file_hash,
            "filename": manifest.original_filename,
            "size": manifest.original_size,
            "chunks": len(manifest.chunks),
            "manifest": manifest.to_dict(),
            "replication": replicated,
        }
    finally:
        os.unlink(tmp_path)
        os.rmdir(tmp_dir)


@router.get("/download/{file_hash}")
async def download_file(
    file_hash: str,
    password: str = "",
    background_tasks: BackgroundTasks = None,
):
    """
    Download a file by its hash: load chunks, decrypt, merge to disk.
    If the manifest or chunks aren't stored locally, fetches them from
    discovered peers via their HTTP API — enabling true cross-node downloads.
    """
    if not _local_store or not _node:
        raise HTTPException(503, "Node not initialized")

    import httpx
    from backend.file_engine.chunker import merge_chunks_to_disk, FileManifest

    # ── Step 1: Load or fetch manifest ─────────────────────────────
    manifest_dict = _local_store.load_manifest(file_hash)

    if not manifest_dict:
        # Not local — ask peers
        logger.info(f"Manifest {file_hash[:16]}... not local, querying peers...")
        peers = await _node.state.get_alive_peers()
        for nid, peer in peers.items():
            peer_url = f"http://{peer.ip}:{peer.api_port}/manifest/{file_hash}"
            try:
                async with httpx.AsyncClient(timeout=10) as client:
                    resp = await client.get(peer_url)
                if resp.status_code == 200:
                    manifest_dict = resp.json()
                    # Cache it locally for next time
                    _local_store.save_manifest(file_hash, manifest_dict)
                    logger.info(f"Fetched manifest from peer {peer.name} ({peer.ip})")
                    break
            except Exception as e:
                logger.debug(f"Peer {peer.ip}:{peer.api_port} manifest fetch failed: {e}")
                continue

    if not manifest_dict:
        raise HTTPException(404, f"File not found on this node or any peer: {file_hash}")

    manifest = FileManifest.from_dict(manifest_dict)

    # ── Step 2: Load or fetch chunks ───────────────────────────────
    chunks = []
    peers = None  # Lazy-load peer list only if needed

    for info in manifest.chunks:
        data = _local_store.load_chunk(info.chunk_hash)

        if data is None:
            # Not local — fetch from peers
            if peers is None:
                peers = await _node.state.get_alive_peers()

            fetched = False
            for nid, peer in peers.items():
                chunk_url = f"http://{peer.ip}:{peer.api_port}/chunk/{info.chunk_hash}"
                try:
                    async with httpx.AsyncClient(timeout=30) as client:
                        resp = await client.get(chunk_url)
                    if resp.status_code == 200:
                        data = resp.content
                        # Cache chunk locally
                        _local_store.save_chunk(info.chunk_hash, data)
                        logger.debug(
                            f"Fetched chunk {info.chunk_hash[:12]}... from {peer.name} ({peer.ip})"
                        )
                        fetched = True
                        break
                except Exception as e:
                    logger.debug(f"Peer {peer.ip} chunk fetch failed: {e}")
                    continue

            if not fetched:
                raise HTTPException(404, f"Chunk {info.chunk_hash[:16]}... not found on any node")

        chunks.append(data)

    # ── Step 3: Merge + decrypt to disk ────────────────────────────
    # Check if file is encrypted and password is needed
    is_encrypted = any(info.encrypted for info in manifest.chunks)
    pwd = password if password else None

    if is_encrypted and not pwd:
        raise HTTPException(
            400,
            "This file is encrypted. Please provide the decryption password."
        )

    temp_dir = _local_store.storage_dir
    temp_file = os.path.join(str(temp_dir), f"temp_{uuid.uuid4().hex}.bin")

    try:
        merge_chunks_to_disk(manifest, chunks, temp_file, password=pwd)
    except ValueError as e:
        if os.path.exists(temp_file):
            os.unlink(temp_file)
        error_msg = str(e)
        if "integrity check failed" in error_msg.lower():
            if is_encrypted:
                error_msg += " (Wrong password? This file is encrypted.)"
        raise HTTPException(400, f"Decryption/integrity error: {error_msg}")

    # Schedule temp file deletion after response is sent
    if background_tasks:
        background_tasks.add_task(os.remove, temp_file)

    logger.info(
        f"Serving '{manifest.original_filename}' ({manifest.original_size} bytes) "
        f"via FileResponse [cross-node capable]"
    )

    return FileResponse(
        path=temp_file,
        media_type="application/octet-stream",
        filename=manifest.original_filename,
    )


@router.get("/files")
async def list_files(local_only: bool = False):
    """List all stored file manifests — local and from discovered peers."""
    if not _local_store:
        raise HTTPException(503, "Node not initialized")

    import json
    import httpx

    # Local files
    manifests = []
    seen_hashes = set()
    storage_path = _local_store.storage_dir
    for f in storage_path.glob("manifest_*.json"):
        data = json.loads(f.read_text())
        fh = data.get("file_hash")
        seen_hashes.add(fh)
        manifests.append({
            "file_hash": fh,
            "filename": data.get("original_filename"),
            "size": data.get("original_size"),
            "chunks": len(data.get("chunks", [])),
            "merkle_root": data.get("merkle_root", ""),
            "source": "local",
        })

    # Also fetch file lists from alive peers (skip if this is a peer-to-peer call)
    if _node and not local_only:
        peers = await _node.state.get_alive_peers()
        for nid, peer in peers.items():
            try:
                async with httpx.AsyncClient(timeout=5) as client:
                    # Pass local_only=true to prevent recursion
                    resp = await client.get(
                        f"http://{peer.ip}:{peer.api_port}/files",
                        params={"local_only": "true"},
                    )
                if resp.status_code == 200:
                    peer_files = resp.json().get("files", [])
                    for pf in peer_files:
                        fh = pf.get("file_hash")
                        if fh and fh not in seen_hashes:
                            seen_hashes.add(fh)
                            pf["source"] = f"peer:{peer.name}"
                            manifests.append(pf)
            except Exception:
                continue  # Peer unreachable, skip

    return {"files": manifests}


@router.get("/manifest/{file_hash}")
async def get_manifest(file_hash: str):
    """Fetch the full manifest for a file (for swarmed downloads)."""
    if not _local_store:
        raise HTTPException(503, "Node not initialized")

    manifest_dict = _local_store.load_manifest(file_hash)
    if not manifest_dict:
        raise HTTPException(404, f"Manifest not found: {file_hash}")
    return manifest_dict


@router.get("/chunk/{chunk_hash}")
async def get_chunk(chunk_hash: str):
    """Fetch a single raw chunk by its hash (for swarmed downloads)."""
    if not _local_store:
        raise HTTPException(503, "Node not initialized")

    from fastapi.responses import Response

    data = _local_store.load_chunk(chunk_hash)
    if data is None:
        raise HTTPException(404, f"Chunk not found: {chunk_hash[:16]}...")

    return Response(
        content=data,
        media_type="application/octet-stream",
        headers={"X-Chunk-Hash": chunk_hash},
    )
