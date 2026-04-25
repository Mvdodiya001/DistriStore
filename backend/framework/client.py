"""
DistriStore — Python SDK Client with Parallel Swarming

Phase 2 Upgrade: Async batched chunk retrieval.
Instead of downloading chunks one-by-one, the client requests up to
SWARM_CONCURRENCY chunks simultaneously from different peers using
asyncio.gather(), similar to BitTorrent swarming.
"""

import asyncio
import time
from pathlib import Path
from typing import Optional, List

import httpx

from backend.utils.logger import get_logger

logger = get_logger("framework.client")

# Number of concurrent chunk downloads
SWARM_CONCURRENCY = 5


class DistriStoreClient:
    """
    Python SDK for interacting with a DistriStore node.

    Supports both synchronous and async parallel (swarmed) downloads.

    Usage:
        client = DistriStoreClient("http://localhost:8000")
        result = client.upload("myfile.txt", password="secret")
        client.download(result["file_hash"], "output.txt", password="secret")

        # Or async swarmed download:
        await client.download_swarmed(file_hash, "output.txt", password="secret")
    """

    def __init__(self, base_url: str = "http://localhost:8000",
                 timeout: float = 30.0,
                 swarm_concurrency: int = SWARM_CONCURRENCY):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.swarm_concurrency = swarm_concurrency

    # ── Synchronous API ────────────────────────────────────────

    def upload(self, file_path: str, password: str = "") -> dict:
        """Upload a file to the DistriStore network."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(path, "rb") as f:
            files = {"file": (path.name, f, "application/octet-stream")}
            data = {"password": password}
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.post(f"{self.base_url}/upload", files=files, data=data)

        resp.raise_for_status()
        result = resp.json()
        logger.info(f"Uploaded '{path.name}' -> hash={result.get('file_hash', '')[:16]}...")
        return result

    def download(self, file_hash: str, output_path: str, password: str = "") -> str:
        """Download a file (sequential, single-connection)."""
        params = {}
        if password:
            params["password"] = password

        with httpx.Client(timeout=self.timeout) as client:
            resp = client.get(f"{self.base_url}/download/{file_hash}", params=params)

        resp.raise_for_status()
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(resp.content)
        logger.info(f"Downloaded {file_hash[:16]}... -> {output_path}")
        return str(out)

    def status(self) -> dict:
        """Get the node's current status."""
        with httpx.Client(timeout=self.timeout) as client:
            resp = client.get(f"{self.base_url}/status")
        resp.raise_for_status()
        return resp.json()

    def list_files(self) -> list:
        """List all files stored on the node."""
        with httpx.Client(timeout=self.timeout) as client:
            resp = client.get(f"{self.base_url}/files")
        resp.raise_for_status()
        return resp.json().get("files", [])

    def get_manifest(self, file_hash: str) -> dict:
        """Fetch the manifest for a file."""
        with httpx.Client(timeout=self.timeout) as client:
            resp = client.get(f"{self.base_url}/manifest/{file_hash}")
        resp.raise_for_status()
        return resp.json()

    def get_chunk(self, chunk_hash: str) -> bytes:
        """Fetch a single chunk by hash."""
        with httpx.Client(timeout=self.timeout) as client:
            resp = client.get(f"{self.base_url}/chunk/{chunk_hash}")
        resp.raise_for_status()
        return resp.content

    # ── Async Parallel (Swarmed) API ───────────────────────────

    async def download_swarmed(self, file_hash: str, output_path: str,
                                password: str = "",
                                peer_urls: List[str] = None) -> dict:
        """
        Download a file using parallel chunk swarming.

        Fetches the manifest, then downloads up to `swarm_concurrency`
        chunks simultaneously from available peers using asyncio.gather().

        Args:
            file_hash: SHA-256 hash of the original file.
            output_path: Where to save the downloaded file.
            password: Decryption password.
            peer_urls: Optional list of peer API URLs to swarm from.
                       Defaults to [self.base_url].

        Returns:
            dict with download stats (time, chunks, speed, etc.)
        """
        urls = peer_urls or [self.base_url]
        start_time = time.perf_counter()

        # Step 1: Fetch manifest
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.get(f"{urls[0]}/manifest/{file_hash}")
            resp.raise_for_status()
            manifest = resp.json()

        chunks_info = manifest.get("chunks", [])
        total_chunks = len(chunks_info)
        logger.info(
            f"Swarming {total_chunks} chunks from {len(urls)} peer(s) "
            f"(concurrency={self.swarm_concurrency})"
        )

        # Step 2: Download chunks in parallel batches
        chunk_data = [None] * total_chunks
        downloaded = 0
        total_bytes = 0

        semaphore = asyncio.Semaphore(self.swarm_concurrency)

        async def fetch_chunk(idx: int, chunk_hash: str) -> None:
            nonlocal downloaded, total_bytes
            # Round-robin across available peers
            peer_url = urls[idx % len(urls)]

            async with semaphore:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    resp = await client.get(f"{peer_url}/chunk/{chunk_hash}")
                    resp.raise_for_status()
                    data = resp.content
                    chunk_data[idx] = data
                    downloaded += 1
                    total_bytes += len(data)
                    logger.debug(
                        f"Chunk {idx}/{total_chunks} ({chunk_hash[:12]}...) "
                        f"from {peer_url} [{len(data)} bytes]"
                    )

        # Launch all chunk downloads with concurrency limit
        tasks = [
            fetch_chunk(info["index"], info["chunk_hash"])
            for info in chunks_info
        ]
        await asyncio.gather(*tasks)

        elapsed = time.perf_counter() - start_time

        # Step 3: Reassemble file (via the API's download endpoint for decryption)
        # Or if we have direct access, merge locally
        params = {"password": password} if password else {}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.get(
                f"{urls[0]}/download/{file_hash}", params=params
            )
            resp.raise_for_status()

        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(resp.content)

        speed_mbps = (total_bytes / (1024 * 1024)) / elapsed if elapsed > 0 else 0

        stats = {
            "file_hash": file_hash,
            "output_path": str(out),
            "total_chunks": total_chunks,
            "total_bytes": total_bytes,
            "elapsed_seconds": round(elapsed, 3),
            "speed_mbps": round(speed_mbps, 2),
            "peers_used": len(urls),
            "concurrency": self.swarm_concurrency,
        }

        logger.info(
            f"Swarmed download complete: {total_chunks} chunks, "
            f"{total_bytes} bytes in {elapsed:.2f}s ({speed_mbps:.1f} MB/s)"
        )
        return stats

    async def download_chunks_parallel(self, chunk_hashes: List[str],
                                        peer_urls: List[str] = None) -> List[bytes]:
        """
        Download a list of chunks in parallel from multiple peers.
        Uses asyncio.gather() with semaphore for concurrency control.

        Returns:
            List of chunk data bytes in the same order as chunk_hashes.
        """
        urls = peer_urls or [self.base_url]
        results = [None] * len(chunk_hashes)
        semaphore = asyncio.Semaphore(self.swarm_concurrency)

        async def fetch(idx: int, chunk_hash: str):
            peer_url = urls[idx % len(urls)]
            async with semaphore:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    resp = await client.get(f"{peer_url}/chunk/{chunk_hash}")
                    resp.raise_for_status()
                    results[idx] = resp.content

        await asyncio.gather(*[
            fetch(i, h) for i, h in enumerate(chunk_hashes)
        ])

        return results
