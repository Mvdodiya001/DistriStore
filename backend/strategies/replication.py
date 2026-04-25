"""
DistriStore — Replication Strategy
Selects top-k peers and sends chunks to them over TCP.
"""

import asyncio
import base64
from typing import List, Optional

from backend.node.state import NodeState
from backend.strategies.selector import select_best_peers, score_peers
from backend.dht.routing import RoutingTable, find_closest_peers
from backend.network.connection import ConnectionManager, PeerConnection
from backend.network.protocol import store_chunk_msg, store_ack_msg, MSG_STORE_ACK
from backend.file_engine.chunker import FileManifest, ChunkInfo
from backend.storage.local_store import LocalStore
from backend.utils.logger import get_logger

logger = get_logger("strategies.replication")


class ReplicationEngine:
    """Handles distributing chunks to peers across the network."""

    def __init__(self, state: NodeState, conn_mgr: ConnectionManager,
                 routing: RoutingTable, local_store: LocalStore,
                 replication_factor: int = 3):
        self.state = state
        self.conn_mgr = conn_mgr
        self.routing = routing
        self.local_store = local_store
        self.k = replication_factor

    async def replicate_chunks(self, manifest: FileManifest,
                                chunk_data_list: list[bytes]) -> dict:
        """
        Distribute all chunks of a file to the best k peers.

        Returns:
            dict with results per chunk.
        """
        results = {}

        for info, data in zip(manifest.chunks, chunk_data_list):
            # Save locally first
            self.local_store.save_chunk(info.chunk_hash, data)
            await self.state.register_chunk(info.chunk_hash, info.chunk_hash)

            # Find best peers using combined heuristic + XOR
            target_peers = await self._select_targets(info.chunk_hash)

            if not target_peers:
                logger.warning(f"No peers available for chunk {info.chunk_hash[:12]}...")
                results[info.chunk_hash] = {"stored_locally": True, "replicated_to": []}
                continue

            # Send to each target peer
            replicated_to = []
            for peer_id in target_peers[:self.k]:
                success = await self._send_chunk_to_peer(peer_id, info, data, manifest.file_hash)
                if success:
                    replicated_to.append(peer_id)

            # Update routing table
            self.routing.assign_chunk(info.chunk_hash, [self.state.node_id] + replicated_to)

            results[info.chunk_hash] = {
                "stored_locally": True,
                "replicated_to": replicated_to,
                "total_copies": 1 + len(replicated_to),
            }
            logger.info(
                f"Chunk {info.chunk_hash[:12]}... replicated to "
                f"{len(replicated_to)}/{self.k} peers"
            )

        return results

    async def _select_targets(self, chunk_hash: str) -> List[str]:
        """Combine heuristic scoring with XOR distance for peer selection."""
        peers = await self.state.get_alive_peers()
        if not peers:
            return []

        # Score by heuristic
        scored = score_peers(peers)
        heuristic_top = [pid for pid, _, _ in scored[:self.k * 2]]

        # Also consider XOR-closest
        xor_closest = find_closest_peers(chunk_hash, list(peers.keys()), k=self.k)
        xor_top = [pid for pid, _ in xor_closest]

        # Merge: prioritize XOR-closest but fill with heuristic-best
        combined = []
        for pid in xor_top:
            if pid not in combined:
                combined.append(pid)
        for pid in heuristic_top:
            if pid not in combined:
                combined.append(pid)

        return combined[:self.k]

    async def _send_chunk_to_peer(self, peer_id: str, info: ChunkInfo,
                                   data: bytes, file_hash: str) -> bool:
        """Send a single chunk to a peer over TCP."""
        conn = self.conn_mgr.connections.get(peer_id)
        if not conn:
            # Try to connect
            peer = await self.state.get_peer(peer_id)
            if not peer:
                return False
            conn = await self.conn_mgr.connect_to_peer(peer.ip, peer.tcp_port)
            if not conn:
                return False

        try:
            data_b64 = base64.b64encode(data).decode()
            msg = store_chunk_msg(self.state.node_id, info.chunk_hash, data_b64, file_hash)
            await conn.send(msg)
            logger.debug(f"Sent chunk {info.chunk_hash[:12]}... to {peer_id[:12]}...")
            return True
        except Exception as e:
            logger.error(f"Failed to send chunk to {peer_id[:12]}...: {e}")
            return False
