"""
DistriStore — Phase 12 Verification: TCP Registration & Cross-Node Handshake
Verifies that HANDSHAKE and HANDSHAKE_ACK correctly exchange api_port and tcp_port
to bypass UDP broadcast drops across different nodes/firewalls.
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from backend.utils.config import _generate_node_id
from backend.utils.logger import setup_logging
from backend.node.state import NodeState
from backend.network.connection import ConnectionManager

async def run_test():
    setup_logging("DEBUG")
    print("=" * 60)
    print("  DistriStore — Phase 12 Verification Test (Cross-Node Handshake)")
    print("=" * 60)

    # 1. Create two nodes representing Windows and Linux
    state_lin = NodeState(node_id=_generate_node_id(), name="linux-node")
    state_win = NodeState(node_id=_generate_node_id(), name="windows-node")
    state_lin.api_port = 8001
    state_win.api_port = 8002

    # 2. Start TCP servers on both
    conn_lin = ConnectionManager(state_lin)
    await conn_lin.start_server("127.0.0.1", 0)
    
    conn_win = ConnectionManager(state_win)
    await conn_win.start_server("127.0.0.1", 0)

    # 3. Connect Linux to Windows (simulate manual connect or fallback)
    # The moment we connect, the HANDSHAKE logic should exchange the api_port and register the peer
    print("\n[1/3] Linux node connecting to Windows node via TCP...")
    tcp_conn = await conn_lin.connect_to_peer("127.0.0.1", state_win.tcp_port)
    assert tcp_conn is not None, "Failed to connect to Windows node"
    
    # Give a tiny bit of time for async peer registration inside the handler
    await asyncio.sleep(0.1)

    # 4. Verify Linux node registered Windows node with correct api_port
    print("\n[2/3] Verifying Linux registered Windows node with api_port...")
    peers_lin = await state_lin.get_all_peers()
    assert state_win.node_id in peers_lin, "Linux did not register Windows!"
    win_peer_in_lin = peers_lin[state_win.node_id]
    assert win_peer_in_lin.api_port == 8002, f"Expected api_port 8002, got {win_peer_in_lin.api_port}"
    assert win_peer_in_lin.tcp_port == state_win.tcp_port, "TCP port mismatch"
    print(f"  ✅ Linux successfully registered Windows peer with API port {win_peer_in_lin.api_port}")

    # 5. Verify Windows node registered Linux node with correct api_port
    print("\n[3/3] Verifying Windows registered Linux node with api_port...")
    peers_win = await state_win.get_all_peers()
    assert state_lin.node_id in peers_win, "Windows did not register Linux!"
    lin_peer_in_win = peers_win[state_lin.node_id]
    assert lin_peer_in_win.api_port == 8001, f"Expected api_port 8001, got {lin_peer_in_win.api_port}"
    print(f"  ✅ Windows successfully registered Linux peer with API port {lin_peer_in_win.api_port}")

    # Cleanup
    await conn_lin.stop()
    await conn_win.stop()

    print("\n" + "=" * 60)
    print("  ✅ PHASE 12 VERIFICATION PASSED")
    print("=" * 60)

if __name__ == "__main__":
    try:
        asyncio.run(run_test())
    except AssertionError as e:
        print(f"\n  ❌ VERIFICATION FAILED: {e}")
        sys.exit(1)
