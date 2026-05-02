"""
DistriStore — Phase 10 Verification: Dynamic Ports Test
Verifies that setting port=0 successfully binds to an OS-assigned dynamic port,
and updates the NodeState tcp_port accordingly.
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
    print("  DistriStore — Phase 10 Verification Test (Dynamic Ports)")
    print("=" * 60)

    # 1. Create Node state
    state = NodeState(node_id=_generate_node_id(), name="dynamic-node")
    assert state.tcp_port == 0, "Initial TCP port should be 0"

    # 2. Start TCP server with port 0
    conn_mgr = ConnectionManager(state)
    await conn_mgr.start_server("127.0.0.1", 0)

    # 3. Verify actual port is > 0 and stored in state
    assigned_port = state.tcp_port
    print(f"  ✅ OS-assigned TCP port: {assigned_port}")
    assert assigned_port > 0, "Dynamic port was not assigned!"
    assert assigned_port <= 65535, "Assigned port is invalid"

    # 4. Try connecting to the assigned port
    reader, writer = await asyncio.open_connection("127.0.0.1", assigned_port)
    print(f"  ✅ Successfully connected to 127.0.0.1:{assigned_port}")
    
    writer.close()
    await writer.wait_closed()
    
    await conn_mgr.stop()

    print("\n" + "=" * 60)
    print("  ✅ PHASE 10 VERIFICATION PASSED")
    print("=" * 60)

if __name__ == "__main__":
    try:
        asyncio.run(run_test())
    except AssertionError as e:
        print(f"\n  ❌ VERIFICATION FAILED: {e}")
        sys.exit(1)
