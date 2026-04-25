"""
DistriStore — Peer Search / Lookup Logic
Higher-level DHT operations for finding peers that hold a chunk.
"""

from typing import List, Optional

from backend.dht.routing import RoutingTable, find_closest_peers
from backend.node.state import NodeState
from backend.utils.logger import get_logger

logger = get_logger("dht.lookup")


class DHTLookup:
    """Performs DHT lookups using the routing table and node state."""

    def __init__(self, state: NodeState, routing_table: RoutingTable):
        self.state = state
        self.routing = routing_table

    async def find_chunk_holders(self, chunk_hash: str) -> List[str]:
        """
        Find peers that hold a specific chunk.
        First checks the routing table, then falls back to XOR-closest peers.
        """
        holders = self.routing.get_holders(chunk_hash)
        if holders:
            logger.debug(f"Chunk {chunk_hash[:12]}... found in routing table: {len(holders)} holders")
            return holders

        # Fallback: find XOR-closest alive peers
        peers = await self.state.get_alive_peers()
        if not peers:
            logger.warning("No alive peers available for lookup")
            return []

        closest = find_closest_peers(chunk_hash, list(peers.keys()), k=3)
        return [pid for pid, _ in closest]

    async def find_best_storage_peers(self, chunk_hash: str, k: int = 3) -> List[str]:
        """
        Find the best k peers to store a chunk on, based on XOR distance.
        """
        peers = await self.state.get_alive_peers()
        if not peers:
            return []

        closest = find_closest_peers(chunk_hash, list(peers.keys()), k=k)
        return [pid for pid, _ in closest]
