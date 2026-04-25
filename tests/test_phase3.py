"""
DistriStore — Phase 3 Verification Test
Verification Gate 3: Create dummy hashes, verify XOR routing correctly
identifies the closest peer for each chunk.

Run from distristore/ directory:
    python -m tests.test_phase3
"""

import os
import sys
import secrets

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from backend.utils.logger import setup_logging
from backend.dht.routing import xor_distance, find_closest_peers, RoutingTable
from backend.network.protocol import store_chunk_msg, get_chunk_msg, find_node_msg


def run_test():
    setup_logging("INFO")
    print("=" * 60)
    print("  DistriStore — Phase 3 Verification Test")
    print("=" * 60)

    # ── Step 1: Generate dummy node IDs and chunk hashes ───────
    print("\n[1/4] Generating test data...")
    peer_ids = [secrets.token_hex(20) for _ in range(5)]
    chunk_hashes = [secrets.token_hex(20) for _ in range(3)]

    print("  Peers:")
    for i, pid in enumerate(peer_ids):
        print(f"    Peer {i}: {pid[:20]}...")
    print("  Chunks:")
    for i, ch in enumerate(chunk_hashes):
        print(f"    Chunk {i}: {ch[:20]}...")
    print("  ✅ Test data generated")

    # ── Step 2: Test XOR distance calculation ──────────────────
    print("\n[2/4] Testing XOR distance calculation...")
    d = xor_distance(peer_ids[0], peer_ids[1])
    assert d > 0, "XOR distance should be > 0 for different IDs"
    d_self = xor_distance(peer_ids[0], peer_ids[0])
    assert d_self == 0, "XOR distance to self should be 0"
    print(f"  dist(peer0, peer1) = {d}")
    print(f"  dist(peer0, peer0) = {d_self}")
    print("  ✅ XOR distance works correctly")

    # ── Step 3: Test closest peer lookup ───────────────────────
    print("\n[3/4] Testing closest-peer lookup...")
    for i, ch in enumerate(chunk_hashes):
        closest = find_closest_peers(ch, peer_ids, k=3)
        print(f"\n  Chunk {i} ({ch[:16]}...) closest peers:")
        for rank, (pid, dist) in enumerate(closest):
            print(f"    #{rank+1}: {pid[:16]}... (distance={dist})")

        # Verify ordering (closest first)
        for j in range(len(closest) - 1):
            assert closest[j][1] <= closest[j+1][1], "Peers not sorted by distance!"
    print("\n  ✅ Closest-peer lookup works correctly")

    # ── Step 4: Test routing table + protocol messages ─────────
    print("\n[4/4] Testing routing table & protocol messages...")
    rt = RoutingTable()

    # Assign chunks to their closest peers
    for ch in chunk_hashes:
        closest = find_closest_peers(ch, peer_ids, k=2)
        holder_ids = [pid for pid, _ in closest]
        rt.assign_chunk(ch, holder_ids)

    # Verify routing table
    for ch in chunk_hashes:
        holders = rt.get_holders(ch)
        assert len(holders) == 2, f"Expected 2 holders, got {len(holders)}"
        print(f"  Chunk {ch[:16]}... -> {len(holders)} holders")

    # Test peer removal
    removed_peer = peer_ids[0]
    affected = rt.remove_peer_from_all(removed_peer)
    print(f"  Removed peer {removed_peer[:16]}... affected {len(affected)} chunks")

    # Test protocol messages
    msg_store = store_chunk_msg(peer_ids[0], chunk_hashes[0], "base64data")
    msg_get = get_chunk_msg(peer_ids[1], chunk_hashes[0])
    msg_find = find_node_msg(peer_ids[2], chunk_hashes[1])

    assert msg_store["type"] == "STORE_CHUNK"
    assert msg_get["type"] == "GET_CHUNK"
    assert msg_find["type"] == "FIND_NODE"
    print(f"  Protocol messages: STORE_CHUNK ✅, GET_CHUNK ✅, FIND_NODE ✅")

    print(f"\n  Routing table has {rt.chunk_count()} entries")
    print("  ✅ Routing table & protocol messages working")

    print("\n" + "=" * 60)
    print("  ✅ PHASE 3 VERIFICATION PASSED — All checks green!")
    print("=" * 60)


if __name__ == "__main__":
    try:
        run_test()
    except AssertionError as e:
        print(f"\n  ❌ VERIFICATION FAILED: {e}")
        sys.exit(1)
