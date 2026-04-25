"""
DistriStore — Dynamic Heuristic Peer Scoring
Scores peers using: score = free_space_norm + uptime_norm - latency_norm
"""

from typing import Dict, List, Tuple

from backend.node.state import NodeState, PeerInfo
from backend.utils.logger import get_logger

logger = get_logger("strategies.selector")


def _normalize(values: List[float]) -> List[float]:
    """Min-max normalize a list of values to [0, 1]."""
    if not values:
        return []
    mn, mx = min(values), max(values)
    if mx == mn:
        return [0.5] * len(values)
    return [(v - mn) / (mx - mn) for v in values]


def score_peers(peers: Dict[str, PeerInfo]) -> List[Tuple[str, float, dict]]:
    """
    Score peers using the heuristic:
        score = free_space_norm + uptime_norm - latency_norm

    Returns:
        Sorted list of (peer_id, score, details) — highest score first.
    """
    if not peers:
        return []

    ids = list(peers.keys())
    free_spaces = [peers[pid].free_space for pid in ids]
    uptimes = [peers[pid].uptime for pid in ids]
    latencies = [peers[pid].latency for pid in ids]

    fs_norm = _normalize(free_spaces)
    up_norm = _normalize(uptimes)
    lat_norm = _normalize(latencies)

    results = []
    for i, pid in enumerate(ids):
        score = fs_norm[i] + up_norm[i] - lat_norm[i]
        details = {
            "free_space": free_spaces[i],
            "uptime": uptimes[i],
            "latency": latencies[i],
            "fs_norm": round(fs_norm[i], 3),
            "up_norm": round(up_norm[i], 3),
            "lat_norm": round(lat_norm[i], 3),
        }
        results.append((pid, round(score, 4), details))

    results.sort(key=lambda x: x[1], reverse=True)
    logger.debug(f"Scored {len(results)} peers, best={results[0][0][:12]}... (score={results[0][1]})")
    return results


async def select_best_peers(state: NodeState, k: int = 3) -> List[str]:
    """Select the top k peers by heuristic score."""
    peers = await state.get_alive_peers()
    if not peers:
        return []
    scored = score_peers(peers)
    selected = [pid for pid, _, _ in scored[:k]]
    logger.info(f"Selected {len(selected)} best peers for storage")
    return selected
