"""
DistriStore — FastAPI Entry Point
Starts the FastAPI server with the DistriStore node running in the background.

Usage:
    uvicorn backend.main:app --host 0.0.0.0 --port 8000
    python -m backend.main --name node-beta --tcp-port 50003 --api-port 8001
"""

import argparse
import asyncio
import sys
import os
from contextlib import asynccontextmanager

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.utils.config import get_config, _generate_node_id
from backend.utils.logger import setup_logging, get_logger
from backend.node.node import DistriNode
from backend.dht.routing import RoutingTable
from backend.storage.local_store import LocalStore
from backend.api.routes import router, init_routes

logger = get_logger("main")

# Module-level state
_node: DistriNode = None
_store: LocalStore = None
_routing: RoutingTable = None


def _init():
    """Initialize node, store, routing from config (+ env var overrides)."""
    global _node, _store, _routing

    config = get_config()

    # Allow env var overrides (useful when spawned by test or subprocess)
    name = os.environ.get("DS_NAME", config.node.name)
    tcp_port = int(os.environ.get("DS_TCP_PORT", config.network.tcp_port))
    udp_port = int(os.environ.get("DS_UDP_PORT", config.network.discovery_port))

    if name != config.node.name:
        config.node.name = name
        config.node.node_id = _generate_node_id()
    config.network.tcp_port = tcp_port
    config.network.discovery_port = udp_port

    setup_logging(config.logging.level, config.logging.file)

    _node = DistriNode()
    _store = LocalStore(config.storage.chunk_dir)
    _routing = RoutingTable()
    init_routes(_node, _store, _routing)


@asynccontextmanager
async def lifespan(app):
    """Start P2P node when FastAPI starts, stop on shutdown."""
    await _node.start()
    logger.info("DistriStore node started alongside API server")
    yield
    await _node.stop()
    logger.info("DistriStore node stopped")


# Initialize on module import
_init()

app = FastAPI(
    title="DistriStore",
    description="LAN-optimized P2P Distributed Hash Table Storage",
    version="1.0.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)


if __name__ == "__main__":
    import uvicorn
    config = get_config()
    port = int(os.environ.get("DS_API_PORT", config.api.port))
    uvicorn.run(
        "backend.main:app",
        host=config.api.host,
        port=port,
        reload=False,
    )
