"""
DistriStore — Thread-Safe Node State
Holds all mutable node state behind asyncio locks.
"""

import asyncio
import time
from dataclasses import dataclass, field
from typing import Dict, Optional

from backend.utils.logger import get_logger

logger = get_logger("node.state")


@dataclass
class PeerInfo:
    """Information about a connected peer."""
    node_id: str
    ip: str
    tcp_port: int
    name: str = ""
    last_seen: float = field(default_factory=time.time)
    free_space: int = 0       # bytes available (reported by peer)
    uptime: float = 0.0       # seconds since peer boot
    latency: float = 0.0      # round-trip ms to this peer
    health_score: float = 0.0 # computed health score from HELLO

    def is_alive(self, timeout: int = 15) -> bool:
        """Check if peer has been seen within the timeout window."""
        return (time.time() - self.last_seen) < timeout


class NodeState:
    """
    Thread-safe container for all mutable node state.
    Every mutation MUST be done under the appropriate lock.
    """

    def __init__(self, node_id: str, name: str = "node"):
        # Identity
        self.node_id: str = node_id
        self.name: str = name
        self.tcp_port: int = 0  # Set dynamically by ConnectionManager after OS allocation
        self.start_time: float = time.time()

        # Peer registry: node_id -> PeerInfo
        self._peers: Dict[str, PeerInfo] = {}
        self._peers_lock: asyncio.Lock = asyncio.Lock()

        # Chunk registry: chunk_hash -> local file path
        self._chunks: Dict[str, str] = {}
        self._chunks_lock: asyncio.Lock = asyncio.Lock()

        # Routing table: chunk_hash -> [list of peer node_ids holding this chunk]
        self._routing: Dict[str, list] = {}
        self._routing_lock: asyncio.Lock = asyncio.Lock()

        logger.info(f"NodeState initialized: id={self.node_id[:12]}... name={self.name}")

    # ── Peer management ────────────────────────────────────────────

    async def add_peer(self, peer: PeerInfo) -> None:
        """Register or update a peer."""
        async with self._peers_lock:
            existing = self._peers.get(peer.node_id)
            if existing:
                existing.last_seen = time.time()
                existing.ip = peer.ip
                existing.tcp_port = peer.tcp_port
                if peer.free_space:
                    existing.free_space = peer.free_space
                if peer.uptime:
                    existing.uptime = peer.uptime
                if peer.health_score:
                    existing.health_score = peer.health_score
                if peer.name and peer.name != "unknown":
                    existing.name = peer.name
                logger.debug(f"Updated peer {peer.node_id[:12]}... ({peer.ip})")
            else:
                peer.last_seen = time.time()
                self._peers[peer.node_id] = peer
                logger.info(f"New peer discovered: {peer.node_id[:12]}... ({peer.ip}:{peer.tcp_port})")

    async def remove_peer(self, node_id: str) -> Optional[PeerInfo]:
        """Remove a peer by node_id."""
        async with self._peers_lock:
            peer = self._peers.pop(node_id, None)
            if peer:
                logger.info(f"Removed peer {node_id[:12]}... ({peer.ip})")
            return peer

    async def get_peer(self, node_id: str) -> Optional[PeerInfo]:
        """Get a peer by node_id."""
        async with self._peers_lock:
            return self._peers.get(node_id)

    async def get_all_peers(self) -> Dict[str, PeerInfo]:
        """Return a copy of the peer dictionary."""
        async with self._peers_lock:
            return dict(self._peers)

    async def get_alive_peers(self, timeout: int = 15) -> Dict[str, PeerInfo]:
        """Return only peers seen within the timeout window."""
        async with self._peers_lock:
            return {
                nid: p for nid, p in self._peers.items()
                if p.is_alive(timeout)
            }

    # ── Chunk management ───────────────────────────────────────────

    async def register_chunk(self, chunk_hash: str, file_path: str) -> None:
        """Record that a chunk is stored locally."""
        async with self._chunks_lock:
            self._chunks[chunk_hash] = file_path
            logger.debug(f"Registered local chunk {chunk_hash[:12]}...")

    async def get_chunk_path(self, chunk_hash: str) -> Optional[str]:
        """Get the local path of a stored chunk."""
        async with self._chunks_lock:
            return self._chunks.get(chunk_hash)

    async def list_chunks(self) -> Dict[str, str]:
        """Return a copy of all locally stored chunks."""
        async with self._chunks_lock:
            return dict(self._chunks)

    async def remove_chunk(self, chunk_hash: str) -> Optional[str]:
        """Remove a chunk record."""
        async with self._chunks_lock:
            return self._chunks.pop(chunk_hash, None)

    # ── Routing table ──────────────────────────────────────────────

    async def update_routing(self, chunk_hash: str, peer_ids: list) -> None:
        """Set which peers hold a specific chunk."""
        async with self._routing_lock:
            self._routing[chunk_hash] = peer_ids
            logger.debug(f"Routing updated: {chunk_hash[:12]}... -> {len(peer_ids)} peers")

    async def get_chunk_holders(self, chunk_hash: str) -> list:
        """Get the list of peer IDs holding a specific chunk."""
        async with self._routing_lock:
            return list(self._routing.get(chunk_hash, []))

    async def get_full_routing_table(self) -> Dict[str, list]:
        """Return a copy of the routing table."""
        async with self._routing_lock:
            return {k: list(v) for k, v in self._routing.items()}

    # ── Utilities ──────────────────────────────────────────────────

    @property
    def uptime(self) -> float:
        """Seconds since this node started."""
        return time.time() - self.start_time

    async def status(self) -> dict:
        """Return a summary of the current node state."""
        peers = await self.get_all_peers()
        chunks = await self.list_chunks()
        return {
            "node_id": self.node_id,
            "name": self.name,
            "uptime_seconds": round(self.uptime, 2),
            "peer_count": len(peers),
            "chunk_count": len(chunks),
            "peers": {
                nid: {
                    "ip": p.ip,
                    "tcp_port": p.tcp_port,
                    "last_seen": p.last_seen,
                    # Frontend-compatible aliases
                    "name": p.name,
                    "host": p.ip,
                    "port": p.tcp_port,
                    "health_score": p.health_score,
                    "free_space": p.free_space,
                    "uptime": p.uptime,
                }
                for nid, p in peers.items()
            },
        }
