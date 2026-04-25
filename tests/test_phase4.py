"""
DistriStore — Phase 4 Verification Test
Verification Gate 4: Node A processes a file. Nodes B and C receive chunks
and save them to their .storage/ folders.

Run from distristore/ directory:
    python -m tests.test_phase4
"""

import asyncio
import base64
import json
import os
import sys
import shutil

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from backend.utils.config import _generate_node_id
from backend.utils.logger import setup_logging, get_logger
from backend.node.state import NodeState, PeerInfo
from backend.network.connection import ConnectionManager, PeerConnection
from backend.network.protocol import MSG_STORE_CHUNK
from backend.dht.routing import RoutingTable
from backend.file_engine.chunker import chunk_file
from backend.storage.local_store import LocalStore
from backend.strategies.replication import ReplicationEngine

logger = get_logger("test.phase4")
TMP = os.path.join(os.path.dirname(__file__), "..", ".test_tmp_p4")


async def _peer_handler(store: LocalStore, conn: PeerConnection, msg: dict):
    """Handle incoming messages on peer nodes — store chunks."""
    if msg.get("type") == MSG_STORE_CHUNK:
        chunk_hash = msg["chunk_hash"]
        data = base64.b64decode(msg["chunk_data"])
        store.save_chunk(chunk_hash, data)
        logger.info(f"Peer stored chunk {chunk_hash[:12]}... ({len(data)} bytes)")


async def run_test():
    setup_logging("INFO")
    print("=" * 60)
    print("  DistriStore — Phase 4 Verification Test")
    print("=" * 60)

    # Cleanup
    if os.path.exists(TMP):
        shutil.rmtree(TMP)
    os.makedirs(TMP, exist_ok=True)

    # ── Step 1: Set up 3 nodes ─────────────────────────────────
    print("\n[1/5] Setting up 3 nodes (A, B, C)...")
    state_a = NodeState(_generate_node_id(), "node-A")
    state_b = NodeState(_generate_node_id(), "node-B")
    state_c = NodeState(_generate_node_id(), "node-C")

    store_a = LocalStore(os.path.join(TMP, "storage_a"))
    store_b = LocalStore(os.path.join(TMP, "storage_b"))
    store_c = LocalStore(os.path.join(TMP, "storage_c"))

    conn_a = ConnectionManager(state_a)
    conn_b = ConnectionManager(state_b, lambda c, m: _peer_handler(store_b, c, m))
    conn_c = ConnectionManager(state_c, lambda c, m: _peer_handler(store_c, c, m))

    await conn_b.start_server("127.0.0.1", 50010)
    await conn_c.start_server("127.0.0.1", 50011)
    print("  ✅ 3 nodes created, TCP servers for B & C running")

    # ── Step 2: Register peers on Node A ───────────────────────
    print("\n[2/5] Registering peers on Node A...")
    await state_a.add_peer(PeerInfo(state_b.node_id, "127.0.0.1", 50010, "node-B",
                                     free_space=1_000_000, uptime=100, latency=2))
    await state_a.add_peer(PeerInfo(state_c.node_id, "127.0.0.1", 50011, "node-C",
                                     free_space=2_000_000, uptime=200, latency=1))
    print("  ✅ Peers registered")

    # ── Step 3: Create test file and chunk it ──────────────────
    print("\n[3/5] Creating & chunking test file...")
    test_file = os.path.join(TMP, "testfile.bin")
    with open(test_file, "wb") as f:
        f.write(os.urandom(512 * 1024))  # 512 KB

    manifest, chunks = chunk_file(test_file, chunk_size=262144, password="secret")
    print(f"  File chunked: {len(chunks)} chunks")

    # ── Step 4: Replicate to peers ─────────────────────────────
    print("\n[4/5] Replicating chunks to peers...")
    routing = RoutingTable()
    engine = ReplicationEngine(state_a, conn_a, routing, store_a, replication_factor=2)
    results = await engine.replicate_chunks(manifest, chunks)

    for ch, info in results.items():
        print(f"  Chunk {ch[:16]}... -> {info['total_copies']} copies, replicated to {len(info['replicated_to'])} peers")

    # Give peers time to process
    await asyncio.sleep(1)

    # ── Step 5: Verify chunks arrived at B and C ───────────────
    print("\n[5/5] Verifying chunks on peer nodes...")
    b_chunks = store_b.list_chunks()
    c_chunks = store_c.list_chunks()
    total_remote = len(b_chunks) + len(c_chunks)

    print(f"  Node B has: {len(b_chunks)} chunks")
    print(f"  Node C has: {len(c_chunks)} chunks")
    print(f"  Node A has: {len(store_a.list_chunks())} chunks (local)")

    assert total_remote > 0, "No chunks were replicated to remote peers!"
    print(f"  ✅ {total_remote} chunk copies distributed to remote peers")

    # Cleanup
    await conn_a.stop()
    await conn_b.stop()
    await conn_c.stop()
    shutil.rmtree(TMP, ignore_errors=True)

    print("\n" + "=" * 60)
    print("  ✅ PHASE 4 VERIFICATION PASSED — All checks green!")
    print("=" * 60)


if __name__ == "__main__":
    try:
        asyncio.run(run_test())
    except AssertionError as e:
        print(f"\n  ❌ VERIFICATION FAILED: {e}")
        sys.exit(1)
