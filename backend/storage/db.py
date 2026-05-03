"""
DistriStore — SQLite Persistence Layer (Phase 16)
Replaces in-memory dicts and flat JSON files with a persistent
SQLite database for File Manifests and Peer Routing Tables.

All writes use asyncio.to_thread() to avoid blocking the event loop.
"""

import asyncio
import json
import sqlite3
import time
from pathlib import Path
from typing import Optional

from backend.utils.logger import get_logger

logger = get_logger("storage.db")


class NodeDatabase:
    """Persistent SQLite store for manifests and peer routing."""

    def __init__(self, storage_dir: str = ".storage"):
        db_dir = Path(storage_dir)
        db_dir.mkdir(parents=True, exist_ok=True)
        db_path = db_dir / "distristore.db"

        self._conn = sqlite3.connect(str(db_path), check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL")      # concurrent reads
        self._conn.execute("PRAGMA synchronous=NORMAL")     # safe + fast
        self._conn.row_factory = sqlite3.Row

        self._create_tables()
        logger.info(f"NodeDatabase initialized at {db_path.resolve()}")

    # ── Schema ─────────────────────────────────────────────────────

    def _create_tables(self) -> None:
        cur = self._conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS peers (
                node_id     TEXT PRIMARY KEY,
                ip          TEXT,
                tcp_port    INTEGER,
                api_port    INTEGER,
                name        TEXT DEFAULT '',
                health_score REAL DEFAULT 0.0,
                last_seen   REAL
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS manifests (
                file_hash   TEXT PRIMARY KEY,
                filename    TEXT,
                total_size  INTEGER,
                merkle_root TEXT,
                chunks_json TEXT,
                compression TEXT DEFAULT ''
            )
        """)
        # Phase 18: migrate existing tables that lack the compression column
        try:
            cur.execute("ALTER TABLE manifests ADD COLUMN compression TEXT DEFAULT ''")
        except sqlite3.OperationalError:
            pass  # column already exists
        self._conn.commit()

    # ── Manifest operations (sync, called via to_thread) ───────────

    def _save_manifest_sync(self, file_hash: str, manifest_dict: dict) -> None:
        chunks_json = json.dumps(manifest_dict.get("chunks", []))
        self._conn.execute(
            """INSERT OR REPLACE INTO manifests
               (file_hash, filename, total_size, merkle_root, chunks_json, compression)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                file_hash,
                manifest_dict.get("original_filename", ""),
                manifest_dict.get("original_size", 0),
                manifest_dict.get("merkle_root", ""),
                chunks_json,
                manifest_dict.get("compression", ""),
            ),
        )
        self._conn.commit()
        logger.debug(f"DB: Saved manifest {file_hash[:12]}...")

    def _get_manifest_sync(self, file_hash: str) -> Optional[dict]:
        cur = self._conn.execute(
            "SELECT * FROM manifests WHERE file_hash = ?", (file_hash,)
        )
        row = cur.fetchone()
        if not row:
            return None
        return {
            "file_hash": row["file_hash"],
            "original_filename": row["filename"],
            "original_size": row["total_size"],
            "merkle_root": row["merkle_root"],
            "chunks": json.loads(row["chunks_json"]),
            "compression": row["compression"] if "compression" in row.keys() else "",
        }

    def _get_all_manifests_sync(self) -> list[dict]:
        cur = self._conn.execute("SELECT * FROM manifests")
        results = []
        for row in cur.fetchall():
            results.append({
                "file_hash": row["file_hash"],
                "original_filename": row["filename"],
                "original_size": row["total_size"],
                "merkle_root": row["merkle_root"],
                "chunks": json.loads(row["chunks_json"]),
                "compression": row["compression"] if "compression" in row.keys() else "",
            })
        return results

    # ── Peer operations (sync, called via to_thread) ───────────────

    def _upsert_peer_sync(
        self, node_id: str, ip: str, tcp_port: int,
        api_port: int = 8888, name: str = "",
        health_score: float = 0.0, last_seen: float = None,
    ) -> None:
        if last_seen is None:
            last_seen = time.time()
        self._conn.execute(
            """INSERT OR REPLACE INTO peers
               (node_id, ip, tcp_port, api_port, name, health_score, last_seen)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (node_id, ip, tcp_port, api_port, name, health_score, last_seen),
        )
        self._conn.commit()

    def _get_all_peers_sync(self) -> list[dict]:
        cur = self._conn.execute("SELECT * FROM peers")
        return [dict(row) for row in cur.fetchall()]

    # ── Async wrappers ─────────────────────────────────────────────

    async def save_manifest(self, file_hash: str, manifest_dict: dict) -> None:
        await asyncio.to_thread(self._save_manifest_sync, file_hash, manifest_dict)

    async def get_manifest(self, file_hash: str) -> Optional[dict]:
        return await asyncio.to_thread(self._get_manifest_sync, file_hash)

    async def get_all_manifests(self) -> list[dict]:
        return await asyncio.to_thread(self._get_all_manifests_sync)

    async def upsert_peer(self, **kwargs) -> None:
        await asyncio.to_thread(self._upsert_peer_sync, **kwargs)

    async def get_all_peers(self) -> list[dict]:
        return await asyncio.to_thread(self._get_all_peers_sync)

    def close(self) -> None:
        self._conn.close()
        logger.info("NodeDatabase connection closed")
