"""
DistriStore — Heartbeat Monitor
Periodically pings connected peers to measure latency and detect dead nodes.
"""

import asyncio
import time

from backend.node.state import NodeState
from backend.network.connection import ConnectionManager
from backend.network.protocol import ping_msg, pong_msg, MSG_PING, MSG_PONG
from backend.utils.logger import get_logger

logger = get_logger("advanced.heartbeat")


class HeartbeatMonitor:
    """Background task that pings peers every N seconds."""

    def __init__(self, state: NodeState, conn_mgr: ConnectionManager,
                 interval: int = 5, timeout: int = 15):
        self.state = state
        self.conn_mgr = conn_mgr
        self.interval = interval
        self.timeout = timeout
        self._task = None
        self._pending_pings: dict[str, float] = {}  # peer_id -> send_time

    async def start(self):
        """Start the heartbeat loop."""
        self._task = asyncio.create_task(self._heartbeat_loop())
        logger.info(f"Heartbeat monitor started (interval={self.interval}s, timeout={self.timeout}s)")

    async def stop(self):
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Heartbeat monitor stopped")

    async def _heartbeat_loop(self):
        while True:
            try:
                await self._ping_all_peers()
                await asyncio.sleep(self.interval)
                await self._check_timeouts()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")
                await asyncio.sleep(self.interval)

    async def _ping_all_peers(self):
        """Send PING to all connected peers."""
        peers = await self.state.get_all_peers()
        for peer_id in peers:
            conn = self.conn_mgr.connections.get(peer_id)
            if conn:
                try:
                    msg = ping_msg(self.state.node_id)
                    await conn.send(msg)
                    self._pending_pings[peer_id] = time.time()
                    logger.debug(f"PING -> {peer_id[:12]}...")
                except Exception as e:
                    logger.debug(f"Failed to ping {peer_id[:12]}...: {e}")

    async def _check_timeouts(self):
        """Check for peers that haven't responded within timeout."""
        now = time.time()
        dead_peers = []
        for peer_id, sent_time in list(self._pending_pings.items()):
            if now - sent_time > self.timeout:
                dead_peers.append(peer_id)
                del self._pending_pings[peer_id]

        for peer_id in dead_peers:
            logger.warning(f"Peer {peer_id[:12]}... timed out (>{self.timeout}s)")
            await self.state.remove_peer(peer_id)

    async def handle_pong(self, peer_id: str, msg: dict):
        """Process a PONG response — update peer latency and info."""
        if peer_id in self._pending_pings:
            latency_ms = (time.time() - self._pending_pings[peer_id]) * 1000
            del self._pending_pings[peer_id]

            peer = await self.state.get_peer(peer_id)
            if peer:
                peer.latency = latency_ms
                peer.uptime = msg.get("uptime", 0)
                peer.free_space = msg.get("free_space", 0)
                peer.last_seen = time.time()
                await self.state.add_peer(peer)

            logger.debug(f"PONG <- {peer_id[:12]}... (latency={latency_ms:.1f}ms)")

    async def handle_ping(self, peer_id: str):
        """Respond to an incoming PING with PONG."""
        conn = self.conn_mgr.connections.get(peer_id)
        if conn:
            from backend.storage.local_store import LocalStore
            store = LocalStore()
            msg = pong_msg(
                self.state.node_id,
                uptime=self.state.uptime,
                free_space=store.get_free_space(),
            )
            await conn.send(msg)
            logger.debug(f"PONG -> {peer_id[:12]}...")
