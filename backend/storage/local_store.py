"""
DistriStore — Local Chunk Storage
Simple disk I/O for storing and retrieving chunk files.
"""

import os
import json
from pathlib import Path
from typing import Optional

from backend.file_engine.crypto import sha256_hash
from backend.utils.logger import get_logger

logger = get_logger("storage.local_store")

DEFAULT_STORAGE_DIR = ".storage"


class LocalStore:
    """Manages chunk files on the local disk."""

    def __init__(self, storage_dir: str = DEFAULT_STORAGE_DIR):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"LocalStore initialized at {self.storage_dir.resolve()}")

    def save_chunk(self, chunk_hash: str, data: bytes) -> str:
        """
        Save chunk data to disk.
        Returns the file path.
        """
        filename = f"chunk_{chunk_hash}.bin"
        filepath = self.storage_dir / filename
        filepath.write_bytes(data)
        logger.debug(f"Saved chunk {chunk_hash[:12]}... ({len(data)} bytes)")
        return str(filepath)

    def load_chunk(self, chunk_hash: str) -> Optional[bytes]:
        """Load chunk data from disk. Returns None if not found."""
        filename = f"chunk_{chunk_hash}.bin"
        filepath = self.storage_dir / filename
        if not filepath.exists():
            logger.warning(f"Chunk not found: {chunk_hash[:12]}...")
            return None
        data = filepath.read_bytes()
        logger.debug(f"Loaded chunk {chunk_hash[:12]}... ({len(data)} bytes)")
        return data

    def has_chunk(self, chunk_hash: str) -> bool:
        """Check if a chunk exists on disk."""
        return (self.storage_dir / f"chunk_{chunk_hash}.bin").exists()

    def delete_chunk(self, chunk_hash: str) -> bool:
        """Delete a chunk file. Returns True if deleted."""
        filepath = self.storage_dir / f"chunk_{chunk_hash}.bin"
        if filepath.exists():
            filepath.unlink()
            logger.debug(f"Deleted chunk {chunk_hash[:12]}...")
            return True
        return False

    def list_chunks(self) -> list[str]:
        """List all chunk hashes stored locally."""
        hashes = []
        for f in self.storage_dir.glob("chunk_*.bin"):
            h = f.stem.replace("chunk_", "")
            hashes.append(h)
        return hashes

    def save_manifest(self, file_hash: str, manifest_dict: dict) -> str:
        """Save a file manifest to disk."""
        filename = f"manifest_{file_hash}.json"
        filepath = self.storage_dir / filename
        filepath.write_text(json.dumps(manifest_dict, indent=2))
        logger.debug(f"Saved manifest {file_hash[:12]}...")
        return str(filepath)

    def load_manifest(self, file_hash: str) -> Optional[dict]:
        """Load a file manifest from disk."""
        filepath = self.storage_dir / f"manifest_{file_hash}.json"
        if not filepath.exists():
            return None
        return json.loads(filepath.read_text())

    def get_storage_size(self) -> int:
        """Total bytes used by stored chunks."""
        total = 0
        for f in self.storage_dir.iterdir():
            if f.is_file():
                total += f.stat().st_size
        return total

    def get_free_space(self) -> int:
        """Free space on the partition holding the storage dir."""
        stat = os.statvfs(str(self.storage_dir))
        return stat.f_bavail * stat.f_frsize
