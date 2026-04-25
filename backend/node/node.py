"""
DistriStore — Node Orchestrator
Boots the node: loads config, starts discovery, starts TCP server,
and connects to discovered peers.
"""

import asyncio

from backend.utils.config import get_config
from backend.utils.logger import setup_logging, get_logger
from backend.node.state import NodeState
from backend.network.discovery import start_discovery
from backend.network.connection import ConnectionManager

logger = get_logger("node.core")


class DistriNode:
    """Main node orchestrator — ties together state, discovery, and connections."""

    def __init__(self, config_path: str = None):
        self.config = get_config(config_path)
        setup_logging(self.config.logging.level, self.config.logging.file)

        self.state = NodeState(
            node_id=self.config.node.node_id,
            name=self.config.node.name,
        )
        self.conn_mgr = ConnectionManager(self.state)
        self._discovery_protocol = None
        self._tasks: list[asyncio.Task] = []

    async def start(self) -> None:
        """Boot the node: TCP server + UDP discovery + peer connector."""
        net = self.config.network

        # 1. Start TCP server
        await self.conn_mgr.start_server("0.0.0.0", net.tcp_port)

        # 2. Start UDP discovery
        self._discovery_protocol = await start_discovery(
            state=self.state,
            tcp_port=net.tcp_port,
            discovery_port=net.discovery_port,
            broadcast_address=net.broadcast_address,
            interval=net.discovery_interval,
        )

        # 3. Launch background tasks
        self._tasks.append(asyncio.create_task(
            self._discovery_protocol.broadcast_loop()
        ))
        self._tasks.append(asyncio.create_task(
            self._peer_connector_loop()
        ))

        logger.info(
            f"Node [{self.state.name}] started | "
            f"ID: {self.state.node_id[:12]}... | "
            f"TCP: {net.tcp_port} | UDP: {net.discovery_port}"
        )

    async def _peer_connector_loop(self) -> None:
        """Periodically try to TCP-connect to discovered peers we're not connected to."""
        while True:
            await asyncio.sleep(3)
            peers = await self.state.get_alive_peers(self.config.network.peer_timeout)
            for nid, peer in peers.items():
                if nid not in self.conn_mgr.connections:
                    logger.debug(f"Attempting TCP to {peer.ip}:{peer.tcp_port}")
                    await self.conn_mgr.connect_to_peer(peer.ip, peer.tcp_port)

    async def stop(self) -> None:
        """Gracefully shut down."""
        for t in self._tasks:
            t.cancel()
        await self.conn_mgr.stop()
        logger.info("Node shut down")

    async def run_forever(self) -> None:
        """Start the node and block until interrupted."""
        await self.start()
        try:
            await asyncio.Event().wait()  # block forever
        except asyncio.CancelledError:
            pass
        finally:
            await self.stop()
