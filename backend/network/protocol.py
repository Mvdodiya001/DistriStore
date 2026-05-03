"""
DistriStore — Network Protocol
Binary message schemas for P2P communication (Phase 17: msgpack native bytes).
"""

import time
from typing import Optional

from backend.utils.logger import get_logger

logger = get_logger("network.protocol")


# ── Message Type Constants ─────────────────────────────────────
MSG_HANDSHAKE     = "HANDSHAKE"
MSG_HANDSHAKE_ACK = "HANDSHAKE_ACK"
MSG_HELLO         = "HELLO"
MSG_STORE_CHUNK   = "STORE_CHUNK"
MSG_STORE_ACK     = "STORE_ACK"
MSG_CHUNK_ACK     = "CHUNK_ACK"      # Sliding window per-chunk acknowledgment
MSG_GET_CHUNK     = "GET_CHUNK"
MSG_CHUNK_DATA    = "CHUNK_DATA"
MSG_FIND_NODE     = "FIND_NODE"
MSG_FIND_RESULT   = "FIND_RESULT"
MSG_PING          = "PING"
MSG_PONG          = "PONG"
MSG_STATUS        = "STATUS"


def build_message(msg_type: str, sender_id: str, **kwargs) -> dict:
    """Build a protocol message with standard fields."""
    msg = {
        "type": msg_type,
        "sender_id": sender_id,
        "timestamp": time.time(),
    }
    msg.update(kwargs)
    return msg


def auth_handshake_msg(node_id: str, swarm_key: str) -> dict:
    """Build an authentication message."""
    import hmac
    import hashlib
    sig = hmac.new(swarm_key.encode(), node_id.encode(), hashlib.sha256).hexdigest()
    return {"type": "AUTH", "node_id": node_id, "signature": sig}


def store_chunk_msg(sender_id: str, chunk_hash: str, chunk_data: bytes,
                    file_hash: str = "") -> dict:
    """Build a STORE_CHUNK message with raw binary chunk data."""
    return build_message(
        MSG_STORE_CHUNK, sender_id,
        chunk_hash=chunk_hash,
        chunk_data=chunk_data,
        file_hash=file_hash,
    )


def store_ack_msg(sender_id: str, chunk_hash: str, success: bool) -> dict:
    return build_message(MSG_STORE_ACK, sender_id, chunk_hash=chunk_hash, success=success)


def get_chunk_msg(sender_id: str, chunk_hash: str) -> dict:
    return build_message(MSG_GET_CHUNK, sender_id, chunk_hash=chunk_hash)


def chunk_data_msg(sender_id: str, chunk_hash: str, chunk_data: bytes) -> dict:
    """Build a CHUNK_DATA response with raw binary chunk data."""
    return build_message(MSG_CHUNK_DATA, sender_id, chunk_hash=chunk_hash, chunk_data=chunk_data)


def find_node_msg(sender_id: str, target_hash: str) -> dict:
    return build_message(MSG_FIND_NODE, sender_id, target_hash=target_hash)


def find_result_msg(sender_id: str, target_hash: str, closest_peers: list) -> dict:
    return build_message(MSG_FIND_RESULT, sender_id, target_hash=target_hash, closest_peers=closest_peers)


def ping_msg(sender_id: str) -> dict:
    return build_message(MSG_PING, sender_id)


def pong_msg(sender_id: str, uptime: float, free_space: int) -> dict:
    return build_message(MSG_PONG, sender_id, uptime=uptime, free_space=free_space)


def chunk_ack_msg(sender_id: str, chunk_hash: str, index: int) -> dict:
    """Build a CHUNK_ACK message for sliding window acknowledgment."""
    return build_message(MSG_CHUNK_ACK, sender_id, chunk_hash=chunk_hash, index=index)
