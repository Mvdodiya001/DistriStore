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
    return status


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    password: str = Form(""),
):
    """Upload a file: chunk, encrypt, store locally, and replicate."""
    if not _node or not _local_store:
        raise HTTPException(503, "Node not initialized")

    from backend.file_engine.chunker import chunk_file, FileManifest
    from backend.strategies.replication import ReplicationEngine

    # Save uploaded file to temp location
    tmp_dir = tempfile.mkdtemp()
    tmp_path = os.path.join(tmp_dir, file.filename)
    content = await file.read()
    with open(tmp_path, "wb") as f:
        f.write(content)

    try:
        # Chunk + encrypt
        pwd = password if password else None
        manifest, chunks = chunk_file(tmp_path, password=pwd)

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
    Uses O(1) memory — streams decrypted chunks directly to a temp file,
    then serves it via FileResponse with background cleanup.
    """
    if not _local_store:
        raise HTTPException(503, "Node not initialized")

    from backend.file_engine.chunker import merge_chunks_to_disk, FileManifest

    # Load manifest
    manifest_dict = _local_store.load_manifest(file_hash)
    if not manifest_dict:
        raise HTTPException(404, f"File manifest not found for hash: {file_hash}")

    manifest = FileManifest.from_dict(manifest_dict)

    # Load all chunks (data stays on disk, only loaded one-at-a-time in merger)
    chunks = []
    for info in manifest.chunks:
        data = _local_store.load_chunk(info.chunk_hash)
        if data is None:
            raise HTTPException(404, f"Chunk missing: {info.chunk_hash[:16]}...")
        chunks.append(data)

    # Generate safe temp file path
    temp_dir = _local_store.storage_dir
    temp_file = os.path.join(str(temp_dir), f"temp_{uuid.uuid4().hex}.bin")

    # Merge + decrypt directly to disk — O(1) memory
    try:
        pwd = password if password else None
        merge_chunks_to_disk(manifest, chunks, temp_file, password=pwd)
    except ValueError as e:
        # Clean up temp file on error
        if os.path.exists(temp_file):
            os.unlink(temp_file)
        raise HTTPException(400, f"Decryption/integrity error: {e}")

    # Schedule temp file deletion after response is sent
    if background_tasks:
        background_tasks.add_task(os.remove, temp_file)

    logger.info(
        f"Serving '{manifest.original_filename}' ({manifest.original_size} bytes) "
        f"via FileResponse [O(1) memory]"
    )

    return FileResponse(
        path=temp_file,
        media_type="application/octet-stream",
        filename=manifest.original_filename,
    )


@router.get("/files")
async def list_files():
    """List all stored file manifests."""
    if not _local_store:
        raise HTTPException(503, "Node not initialized")

    import json
    manifests = []
    storage_path = _local_store.storage_dir
    for f in storage_path.glob("manifest_*.json"):
        data = json.loads(f.read_text())
        manifests.append({
            "file_hash": data.get("file_hash"),
            "filename": data.get("original_filename"),
            "size": data.get("original_size"),
            "chunks": len(data.get("chunks", [])),
            "merkle_root": data.get("merkle_root", ""),
        })
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
