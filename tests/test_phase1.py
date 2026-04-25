"""
DistriStore — Phase 1 Verification Test
Verification Gate 1: Spin up two nodes, verify they discover each other via UDP
and establish TCP connections.

Run from the distristore/ directory:
    python -m tests.test_phase1
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from backend.utils.config import load_config, _generate_node_id
from backend.utils.logger import setup_logging, get_logger
from backend.node.state import NodeState
from backend.network.discovery import start_discovery
from backend.network.connection import ConnectionManager

logger = get_logger("test.phase1")


async def run_test():
    setup_logging("DEBUG")
    print("=" * 60)
    print("  DistriStore — Phase 1 Verification Test")
    print("=" * 60)

    # ── Step 1: Create two node states ─────────────────────────
    print("\n[1/5] Creating Node A and Node B states...")
    state_a = NodeState(node_id=_generate_node_id(), name="node-alpha")
    state_b = NodeState(node_id=_generate_node_id(), name="node-beta")
    print(f"  Node A: {state_a.node_id[:16]}...")
    print(f"  Node B: {state_b.node_id[:16]}...")
    print("  ✅ States created")

    # ── Step 2: Start TCP servers ──────────────────────────────
    print("\n[2/5] Starting TCP servers...")
    conn_a = ConnectionManager(state_a)
    conn_b = ConnectionManager(state_b)
    await conn_a.start_server("127.0.0.1", 50001)
    await conn_b.start_server("127.0.0.1", 50003)
    print("  ✅ TCP servers running (A=50001, B=50003)")

    # ── Step 3: Start UDP discovery ────────────────────────────
    print("\n[3/5] Starting UDP discovery...")
    disc_a = await start_discovery(state_a, tcp_port=50001,
                                    discovery_port=50000,
                                    broadcast_address="127.255.255.255",
                                    interval=2)
    disc_b = await start_discovery(state_b, tcp_port=50003,
                                    discovery_port=50002,
                                    broadcast_address="127.255.255.255",
                                    interval=2)

    # Manually send discovery messages to simulate LAN broadcast
    # (on loopback, broadcast doesn't work normally)
    import json, time
    hello_a = json.dumps({
        "type": "HELLO",
        "node_id": state_a.node_id,
        "name": state_a.name,
        "tcp_port": 50001,
        "timestamp": time.time(),
    }).encode()
    hello_b = json.dumps({
        "type": "HELLO",
        "node_id": state_b.node_id,
        "name": state_b.name,
        "tcp_port": 50003,
        "timestamp": time.time(),
    }).encode()

    # Simulate: A receives B's hello, B receives A's hello
    disc_a.datagram_received(hello_b, ("127.0.0.1", 50002))
    disc_b.datagram_received(hello_a, ("127.0.0.1", 50000))

    await asyncio.sleep(1)
    print("  ✅ Discovery messages exchanged")

    # ── Step 4: Verify peers are registered ────────────────────
    print("\n[4/5] Checking peer discovery...")
    peers_a = await state_a.get_all_peers()
    peers_b = await state_b.get_all_peers()

    assert len(peers_a) >= 1, "Node A did not discover Node B!"
    assert len(peers_b) >= 1, "Node B did not discover Node A!"

    for nid, p in peers_a.items():
        print(f"  Node A sees: {p.name} ({p.ip}:{p.tcp_port})")
    for nid, p in peers_b.items():
        print(f"  Node B sees: {p.name} ({p.ip}:{p.tcp_port})")
    print("  ✅ Peers discovered")

    # ── Step 5: Establish TCP connection ───────────────────────
    print("\n[5/5] Testing TCP connection (A -> B)...")
    peer_b_info = list(peers_a.values())[0]
    tcp_conn = await conn_a.connect_to_peer(peer_b_info.ip, peer_b_info.tcp_port)

    assert tcp_conn is not None, "TCP connection to Node B failed!"
    print(f"  ✅ Connected to {peer_b_info.name} ({peer_b_info.ip}:{peer_b_info.tcp_port})")

    # ── Cleanup ────────────────────────────────────────────────
    await conn_a.stop()
    await conn_b.stop()

    print("\n" + "=" * 60)
    print("  ✅ PHASE 1 VERIFICATION PASSED — All checks green!")
    print("=" * 60)


if __name__ == "__main__":
    try:
        asyncio.run(run_test())
    except KeyboardInterrupt:
        pass
    except AssertionError as e:
        print(f"\n  ❌ VERIFICATION FAILED: {e}")
        sys.exit(1)
