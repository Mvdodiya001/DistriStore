"""
DistriStore — Self-Healing
Detects dead nodes, finds which chunks they held, and re-replicates to survive.
"""

import asyncio

from backend.node.state import NodeState
from backend.dht.routing import RoutingTable, find_closest_peers
from backend.network.connection import ConnectionManager
from backend.storage.local_store import LocalStore
from backend.strategies.replication import ReplicationEngine
from backend.utils.logger import get_logger

logger = get_logger("advanced.self_healing")


class SelfHealingManager:
    """Monitors the routing table and re-replicates chunks from dead nodes."""

    def __init__(self, state: NodeState, conn_mgr: ConnectionManager,
                 routing: RoutingTable, local_store: LocalStore,
                 replication_factor: int = 3, check_interval: int = 10):
        self.state = state
        self.conn_mgr = conn_mgr
        self.routing = routing
        self.local_store = local_store
        self.k = replication_factor
        self.check_interval = check_interval
        self._task = None

    async def start(self):
        self._task = asyncio.create_task(self._heal_loop())
        logger.info(f"Self-healing started (check every {self.check_interval}s, k={self.k})")

    async def stop(self):
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Self-healing stopped")

    async def _heal_loop(self):
        while True:
            try:
                await asyncio.sleep(self.check_interval)
                await self._check_and_heal()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Self-healing error: {e}")

    async def _check_and_heal(self):
        """Check for under-replicated chunks and re-replicate them."""
        alive_peers = await self.state.get_alive_peers()
        alive_ids = set(alive_peers.keys())
        alive_ids.add(self.state.node_id)  # Include ourselves

        routing_table = self.routing.get_all()
        under_replicated = []

        for chunk_hash, holders in routing_table.items():
            # Filter to only alive holders
            alive_holders = [h for h in holders if h in alive_ids]

            if len(alive_holders) < self.k:
                under_replicated.append((chunk_hash, alive_holders))
                # Update routing table with only alive holders
                self.routing.assign_chunk(chunk_hash, alive_holders)

        if not under_replicated:
            return

        logger.warning(f"Found {len(under_replicated)} under-replicated chunks, healing...")

        for chunk_hash, alive_holders in under_replicated:
            needed = self.k - len(alive_holders)
            if needed <= 0:
                continue

            # Check if we have this chunk locally
            chunk_data = self.local_store.load_chunk(chunk_hash)
            if chunk_data is None:
                logger.warning(f"Cannot heal chunk {chunk_hash[:12]}... — not stored locally")
                continue

            # Find new peers to replicate to
            candidates = [pid for pid in alive_peers if pid not in alive_holders]
            if not candidates:
                logger.warning(f"No available peers to re-replicate {chunk_hash[:12]}...")
                continue

            # Use XOR distance to pick best candidates
            closest = find_closest_peers(chunk_hash, candidates, k=needed)
            new_targets = [pid for pid, _ in closest]

            # Send chunk to new targets
            from backend.network.protocol import store_chunk_msg

            for peer_id in new_targets:
                conn = self.conn_mgr.connections.get(peer_id)
                if not conn:
                    peer = alive_peers.get(peer_id)
                    if peer:
                        conn = await self.conn_mgr.connect_to_peer(peer.ip, peer.tcp_port)
                if conn:
                    try:
                        msg = store_chunk_msg(self.state.node_id, chunk_hash, chunk_data)
                        await conn.send(msg)
                        alive_holders.append(peer_id)
                        logger.info(f"Re-replicated {chunk_hash[:12]}... to {peer_id[:12]}...")
                    except Exception as e:
                        logger.error(f"Re-replication to {peer_id[:12]}... failed: {e}")

            self.routing.assign_chunk(chunk_hash, alive_holders)

        logger.info("Self-healing cycle complete")
