"""
DistriStore — TCP Connection Manager
Async TCP server + client for peer-to-peer communication.
"""

import asyncio
import json
from typing import Callable, Optional

from backend.node.state import NodeState
from backend.utils.logger import get_logger

logger = get_logger("network.connection")

# Message delimiter — newline-separated JSON
DELIMITER = b"\n"
BUFFER_SIZE = 65536
STREAM_LIMIT = 1024 * 1024  # 1 MB — prevents LimitOverrunError on large messages


class PeerConnection:
    """Represents one TCP connection to a peer."""

    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter, peer_id: str = ""):
        self.reader = reader
        self.writer = writer
        self.peer_id = peer_id
        self.addr = writer.get_extra_info("peername")
        # Increase the internal buffer limit to handle large messages (1 MB)
        self.reader._limit = 1024 * 1024

    async def send(self, message: dict) -> None:
        data = json.dumps(message).encode() + DELIMITER
        self.writer.write(data)
        await self.writer.drain()

    async def receive(self) -> Optional[dict]:
        try:
            data = await self.reader.readuntil(DELIMITER)
            return json.loads(data.strip())
        except (asyncio.IncompleteReadError, asyncio.LimitOverrunError,
                ConnectionResetError, json.JSONDecodeError):
            return None

    async def close(self) -> None:
        try:
            self.writer.close()
            await self.writer.wait_closed()
        except Exception:
            pass


class ConnectionManager:
    """Manages all TCP connections — both inbound and outbound."""

    def __init__(self, state: NodeState, message_handler: Callable = None):
        self.state = state
        self.message_handler = message_handler or self._default_handler
        self.connections: dict[str, PeerConnection] = {}
        self._server: Optional[asyncio.Server] = None

    async def start_server(self, host: str = "0.0.0.0", port: int = 0) -> None:
        self._server = await asyncio.start_server(
            self._handle_client, host, port, limit=STREAM_LIMIT
        )
        actual_port = self._server.sockets[0].getsockname()[1]
        self.state.tcp_port = actual_port
        logger.info(f"TCP server listening on {host}:{actual_port} (requested {port})")

    async def _handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        addr = writer.get_extra_info("peername")
        logger.info(f"Incoming TCP connection from {addr}")
        conn = PeerConnection(reader, writer)

        try:
            # Expect a HANDSHAKE as the first message
            msg = await conn.receive()
            if not msg or msg.get("type") != "HANDSHAKE":
                logger.warning(f"Bad handshake from {addr}, dropping")
                await conn.close()
                return

            conn.peer_id = msg.get("node_id", "")
            self.connections[conn.peer_id] = conn
            logger.info(f"Connected to peer {conn.peer_id[:12]}... ({addr[0]})")

            # Register peer from TCP handshake (important when UDP is blocked)
            from backend.node.state import PeerInfo
            peer = PeerInfo(
                node_id=conn.peer_id,
                ip=addr[0],
                tcp_port=msg.get("tcp_port", 0),
                name=msg.get("name", "unknown"),
                api_port=msg.get("api_port", 8888),
            )
            asyncio.ensure_future(self.state.add_peer(peer))

            # Send our handshake back (include api_port + tcp_port)
            await conn.send({
                "type": "HANDSHAKE_ACK",
                "node_id": self.state.node_id,
                "name": self.state.name,
                "tcp_port": self.state.tcp_port,
                "api_port": getattr(self.state, 'api_port', 8888),
            })

            # Message loop
            while True:
                msg = await conn.receive()
                if msg is None:
                    break
                await self.message_handler(conn, msg)

        except Exception as e:
            logger.error(f"Connection error with {addr}: {e}")
        finally:
            self.connections.pop(conn.peer_id, None)
            await conn.close()
            logger.info(f"Disconnected from {addr}")

    async def connect_to_peer(self, ip: str, port: int) -> Optional[PeerConnection]:
        """Initiate an outbound TCP connection to a peer."""
        try:
            reader, writer = await asyncio.open_connection(ip, port, limit=STREAM_LIMIT)
            conn = PeerConnection(reader, writer)

            # Send handshake (include tcp_port + api_port for peer registration)
            await conn.send({
                "type": "HANDSHAKE",
                "node_id": self.state.node_id,
                "name": self.state.name,
                "tcp_port": self.state.tcp_port,
                "api_port": getattr(self.state, 'api_port', 8888),
            })

            # Wait for ACK
            ack = await conn.receive()
            if not ack or ack.get("type") != "HANDSHAKE_ACK":
                logger.warning(f"Handshake rejected by {ip}:{port}")
                await conn.close()
                return None

            conn.peer_id = ack.get("node_id", "")
            self.connections[conn.peer_id] = conn
            logger.info(f"Connected to {ip}:{port} (peer {conn.peer_id[:12]}...)")

            # Register remote peer from ACK (important when UDP is blocked)
            from backend.node.state import PeerInfo
            peer = PeerInfo(
                node_id=conn.peer_id,
                ip=ip,
                tcp_port=ack.get("tcp_port", port),
                name=ack.get("name", "unknown"),
                api_port=ack.get("api_port", 8888),
            )
            asyncio.ensure_future(self.state.add_peer(peer))

            return conn

        except (ConnectionRefusedError, OSError) as e:
            logger.debug(f"Cannot connect to {ip}:{port}: {e}")
            return None

    async def send_to_peer(self, node_id: str, message: dict) -> bool:
        conn = self.connections.get(node_id)
        if not conn:
            return False
        try:
            await conn.send(message)
            return True
        except Exception:
            return False

    async def broadcast_to_peers(self, message: dict) -> int:
        sent = 0
        for nid, conn in list(self.connections.items()):
            if await self.send_to_peer(nid, message):
                sent += 1
        return sent

    async def _default_handler(self, conn: PeerConnection, msg: dict) -> None:
        logger.debug(f"Received from {conn.peer_id[:12]}...: {msg.get('type', 'UNKNOWN')}")

    async def stop(self) -> None:
        if self._server:
            self._server.close()
            await self._server.wait_closed()
        for conn in list(self.connections.values()):
            await conn.close()
        self.connections.clear()
        logger.info("Connection manager stopped")
