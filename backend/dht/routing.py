"""
DistriStore — XOR Distance Routing
Simplified DHT routing using XOR distance between node IDs and chunk hashes.
"""

from typing import Dict, List, Tuple

from backend.utils.logger import get_logger

logger = get_logger("dht.routing")


def xor_distance(id_a: str, id_b: str) -> int:
    """
    Calculate XOR distance between two hex-encoded IDs.
    Both IDs are interpreted as big integers and XORed.
    """
    int_a = int(id_a, 16)
    int_b = int(id_b, 16)
    return int_a ^ int_b


def find_closest_peers(target_hash: str, peer_ids: List[str], k: int = 3) -> List[Tuple[str, int]]:
    """
    Find the k closest peers to a target hash by XOR distance.

    Args:
        target_hash: The chunk hash (hex string).
        peer_ids: List of peer node IDs (hex strings).
        k: Number of closest peers to return.

    Returns:
        List of (peer_id, distance) tuples, sorted by distance ascending.
    """
    if not peer_ids:
        return []

    distances = []
    for pid in peer_ids:
        try:
            dist = xor_distance(target_hash, pid)
            distances.append((pid, dist))
        except ValueError:
            logger.warning(f"Invalid hex ID: {pid}")
            continue

    distances.sort(key=lambda x: x[1])
    result = distances[:k]
    logger.debug(
        f"Closest {len(result)} peers to {target_hash[:12]}...: "
        + ", ".join(f"{pid[:12]}...(d={d})" for pid, d in result)
    )
    return result


class RoutingTable:
    """
    In-memory routing table mapping chunk_hash -> [list of peer IDs].
    Also tracks which peer is responsible based on XOR distance.
    """

    def __init__(self):
        # chunk_hash -> [peer_id, peer_id, ...]
        self._table: Dict[str, List[str]] = {}

    def assign_chunk(self, chunk_hash: str, peer_ids: List[str]) -> None:
        """Record which peers hold a specific chunk."""
        self._table[chunk_hash] = list(peer_ids)
        logger.debug(f"Assigned {chunk_hash[:12]}... -> {len(peer_ids)} peers")

    def get_holders(self, chunk_hash: str) -> List[str]:
        """Get the list of peers holding a chunk."""
        return list(self._table.get(chunk_hash, []))

    def remove_peer_from_all(self, peer_id: str) -> List[str]:
        """
        Remove a peer from all chunk assignments.
        Returns list of chunk_hashes that lost this peer.
        """
        affected = []
        for chunk_hash, peers in self._table.items():
            if peer_id in peers:
                peers.remove(peer_id)
                affected.append(chunk_hash)
        if affected:
            logger.info(f"Removed peer {peer_id[:12]}... from {len(affected)} chunk assignments")
        return affected

    def get_all(self) -> Dict[str, List[str]]:
        """Return a copy of the full routing table."""
        return {k: list(v) for k, v in self._table.items()}

    def chunk_count(self) -> int:
        return len(self._table)
