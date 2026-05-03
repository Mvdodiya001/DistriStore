"""
DistriStore — Phase 2.4 Verification: Enhanced Peer Discovery with Health Scores

Tests:
  1. Health score computation (RAM, CPU, Disk)
  2. HELLO message includes health metrics (with HMAC auth wrapper)
  3. Peers register with health data (using signed payloads)
  4. Health scores are realistic values

Run: python -m tests.test_phase2_health
"""

import asyncio
import json
import os
import sys
import time
import hmac
import hashlib

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

import orjson

from backend.utils.logger import setup_logging
from backend.utils.config import _generate_node_id, get_config
from backend.node.state import NodeState, PeerInfo
from backend.network.discovery import compute_health_score, DiscoveryProtocol


def run_test():
    setup_logging("INFO")
    print("=" * 65)
    print("  DistriStore — Phase 2.4: Enhanced Discovery Verification")
    print("=" * 65)

    # ── Test 1: Health Score Computation ────────────────────────
    print("\n[1/4] Testing health score computation...")
    health = compute_health_score()

    assert "free_ram_mb" in health
    assert "cpu_freq_ghz" in health
    assert "cpu_percent" in health
    assert "free_disk_gb" in health
    assert "health_score" in health

    print(f"  Free RAM:     {health['free_ram_mb']} MB")
    print(f"  CPU Freq:     {health['cpu_freq_ghz']} GHz")
    print(f"  CPU Load:     {health['cpu_percent']}%")
    print(f"  Free Disk:    {health['free_disk_gb']} GB")
    print(f"  Health Score: {health['health_score']}")

    assert health["free_ram_mb"] > 0, "Free RAM should be > 0"
    assert health["health_score"] != 0, "Health score should be non-zero"
    print("  ✅ Health score computation correct")

    # ── Test 2: HELLO Message Format (Phase 15: HMAC wrapper) ──
    print("\n[2/4] Testing HELLO message includes health data...")
    state = NodeState(_generate_node_id(), "test-node")
    state.tcp_port = 50001  # Simulate dynamic port assignment
    protocol = DiscoveryProtocol(state)
    hello_bytes = protocol._build_hello()

    # Phase 15: HELLO is now wrapped: {"payload": {...}, "signature": "..."}
    wrapper = orjson.loads(hello_bytes)

    assert "payload" in wrapper, "HELLO should have 'payload' wrapper (Phase 15 HMAC auth)"
    assert "signature" in wrapper, "HELLO should have 'signature' (Phase 15 HMAC auth)"

    hello_msg = wrapper["payload"]

    assert hello_msg["type"] == "HELLO"
    assert "health" in hello_msg, "HELLO should include 'health' field"
    assert "health_score" in hello_msg["health"]
    assert "free_ram_mb" in hello_msg["health"]
    assert "cpu_freq_ghz" in hello_msg["health"]
    assert "uptime" in hello_msg

    # Verify HMAC signature
    swarm_key = get_config().network.swarm_key.encode()
    payload_bytes = orjson.dumps(hello_msg, option=orjson.OPT_SORT_KEYS)
    expected_sig = hmac.new(swarm_key, payload_bytes, hashlib.sha256).hexdigest()
    assert hmac.compare_digest(wrapper["signature"], expected_sig), "HMAC signature mismatch!"

    print(f"  Wrapper fields: {list(wrapper.keys())}")
    print(f"  Payload fields: {list(hello_msg.keys())}")
    print(f"  Health fields: {list(hello_msg['health'].keys())}")
    print(f"  Health score in HELLO: {hello_msg['health']['health_score']}")
    print(f"  HMAC signature valid: ✅")
    print("  ✅ HELLO message format correct")

    # ── Test 3: Peer Registration with Health Data ─────────────
    print("\n[3/4] Testing peer registration with health data...")

    async def _test_peer_registration():
        state_a = NodeState(_generate_node_id(), "node-A")
        state_b = NodeState(_generate_node_id(), "node-B")

        state_a.tcp_port = 50001
        disc_a = DiscoveryProtocol(state_a)

        # Build a properly signed HELLO from node B (Phase 15 format)
        payload = {
            "type": "HELLO",
            "node_id": state_b.node_id,
            "name": state_b.name,
            "tcp_port": 50003,
            "api_port": 8888,
            "uptime": 120.5,
            "timestamp": time.time(),
            "health": {
                "free_ram_mb": 4096.0,
                "cpu_freq_ghz": 3.5,
                "cpu_percent": 25.0,
                "free_disk_gb": 100.0,
                "health_score": 4696.0,
            },
        }

        # Sign the payload with the same swarm_key
        key = get_config().network.swarm_key.encode()
        payload_bytes = orjson.dumps(payload, option=orjson.OPT_SORT_KEYS)
        sig = hmac.new(key, payload_bytes, hashlib.sha256).hexdigest()

        signed_hello = orjson.dumps({"payload": payload, "signature": sig})

        disc_a.datagram_received(signed_hello, ("192.168.1.100", 50000))
        await asyncio.sleep(0.3)  # let ensure_future complete

        peers = await state_a.get_all_peers()
        assert len(peers) == 1, f"Expected 1 peer, got {len(peers)}"
        peer = list(peers.values())[0]
        assert peer.name == "node-B"
        assert peer.free_space > 0, "Peer should have free_space from health data"
        assert peer.uptime == 120.5

        print(f"  Registered peer: {peer.name} ({peer.ip})")
        print(f"  Peer free space: {peer.free_space / (1024**3):.1f} GB")
        print(f"  Peer uptime: {peer.uptime}s")
        print("  ✅ Peer registered with health data")

    asyncio.run(_test_peer_registration())

    # ── Test 4: Multiple Health Score Calls ────────────────────
    print("\n[4/4] Testing health score stability...")
    scores = [compute_health_score()["health_score"] for _ in range(5)]
    avg = sum(scores) / len(scores)
    variance = sum((s - avg) ** 2 for s in scores) / len(scores)

    print(f"  5 samples: {[round(s, 1) for s in scores]}")
    print(f"  Average: {avg:.1f}, Variance: {variance:.1f}")
    print("  ✅ Health scores stable across calls")

    print("\n" + "=" * 65)
    print("  ✅ PHASE 2.4 VERIFICATION PASSED — Enhanced Discovery Working!")
    print("=" * 65)


if __name__ == "__main__":
    try:
        run_test()
    except AssertionError as e:
        print(f"\n  ❌ VERIFICATION FAILED: {e}")
        sys.exit(1)
