"""
DistriStore — AES-256-GCM with ProcessPoolExecutor for GIL Bypass

Phase 3: CPU-bound crypto (SHA-256, AES) dispatched to ProcessPool
so the asyncio event loop stays responsive during heavy encryption.

Binary format (per chunk):
  [version (1)] [salt (16)] [nonce (12)] [auth_tag (16)] [ciphertext...]
"""

import hashlib
import os
import struct
from concurrent.futures import ProcessPoolExecutor
from typing import List, Tuple

from Crypto.Cipher import AES

from backend.utils.logger import get_logger

logger = get_logger("file_engine.crypto")

# ── Constants ──────────────────────────────────────────────────
VERSION = 1
PBKDF2_ITERATIONS = 100_000
SALT_SIZE = 16
KEY_SIZE = 32
NONCE_SIZE = 12
TAG_SIZE = 16
HEADER_SIZE = 1 + SALT_SIZE + NONCE_SIZE + TAG_SIZE

# Module-level process pool (lazy-initialized)
_pool: ProcessPoolExecutor = None
_MAX_WORKERS = min(os.cpu_count() or 2, 4)


def _get_pool() -> ProcessPoolExecutor:
    global _pool
    if _pool is None:
        _pool = ProcessPoolExecutor(max_workers=_MAX_WORKERS)
    return _pool


def shutdown_pool():
    """Cleanly shut down the process pool."""
    global _pool
    if _pool:
        _pool.shutdown(wait=False)
        _pool = None


# ── Core Crypto (pickle-safe top-level functions) ──────────────

def derive_key(password: str, salt: bytes = None) -> tuple[bytes, bytes]:
    """Derive 256-bit AES key from password using PBKDF2-HMAC-SHA256."""
    if salt is None:
        salt = os.urandom(SALT_SIZE)
    key = hashlib.pbkdf2_hmac(
        "sha256", password.encode(), salt,
        PBKDF2_ITERATIONS, dklen=KEY_SIZE
    )
    return key, salt


def sha256_hash(data: bytes) -> str:
    """Return hex SHA-256 digest of data."""
    return hashlib.sha256(data).hexdigest()


def encrypt(data: bytes, password: str) -> bytes:
    """Encrypt data with AES-256-GCM (derives key fresh each call)."""
    key, salt = derive_key(password)
    return encrypt_with_key(data, key, salt)


def encrypt_with_key(data: bytes, key: bytes, salt: bytes) -> bytes:
    """Encrypt with a pre-derived key — avoids repeated PBKDF2."""
    nonce = os.urandom(NONCE_SIZE)
    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    ciphertext, tag = cipher.encrypt_and_digest(data)
    return struct.pack("B", VERSION) + salt + nonce + tag + ciphertext


def decrypt(encrypted: bytes, password: str) -> bytes:
    """Decrypt AES-256-GCM (derives key from salt in header each call)."""
    if len(encrypted) < HEADER_SIZE:
        raise ValueError(f"Data too short ({len(encrypted)} < {HEADER_SIZE})")
    version = encrypted[0]
    if version != VERSION:
        raise ValueError(f"Unsupported format version: {version}")
    off = 1
    salt = encrypted[off:off + SALT_SIZE]; off += SALT_SIZE
    key, _ = derive_key(password, salt)
    return decrypt_with_key(encrypted, key)


def decrypt_with_key(encrypted: bytes, key: bytes) -> bytes:
    """Decrypt with a pre-derived key — avoids repeated PBKDF2."""
    if len(encrypted) < HEADER_SIZE:
        raise ValueError(f"Data too short ({len(encrypted)} < {HEADER_SIZE})")
    version = encrypted[0]
    if version != VERSION:
        raise ValueError(f"Unsupported format version: {version}")
    off = 1 + SALT_SIZE  # skip version + salt
    nonce = encrypted[off:off + NONCE_SIZE]; off += NONCE_SIZE
    tag = encrypted[off:off + TAG_SIZE]; off += TAG_SIZE
    ciphertext = encrypted[off:]
    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    try:
        return cipher.decrypt_and_verify(ciphertext, tag)
    except ValueError as e:
        raise ValueError(
            f"Authenticated decryption FAILED: {e}. "
            f"The chunk may have been tampered with, or the password is wrong."
        ) from e


# ── Top-level worker functions (must be pickle-able) ───────────

def _worker_encrypt(chunk_data: bytes, password: str) -> Tuple[bytes, str]:
    """Encrypt a chunk and return (ciphertext, sha256_hash). Runs in worker process."""
    ct = encrypt(chunk_data, password)
    h = sha256_hash(ct)
    return ct, h


def _worker_encrypt_keyed(chunk_data: bytes, key: bytes, salt: bytes) -> Tuple[bytes, str]:
    """Encrypt with pre-derived key — skips PBKDF2. Runs in worker process."""
    ct = encrypt_with_key(chunk_data, key, salt)
    h = sha256_hash(ct)
    return ct, h


def _worker_decrypt(chunk_data: bytes, password: str) -> bytes:
    """Decrypt a chunk. Runs in worker process."""
    return decrypt(chunk_data, password)


def _worker_decrypt_keyed(chunk_data: bytes, key: bytes) -> bytes:
    """Decrypt with pre-derived key — skips PBKDF2. Runs in worker process."""
    return decrypt_with_key(chunk_data, key)


def _worker_hash(data: bytes) -> str:
    """SHA-256 hash. Runs in worker process."""
    return sha256_hash(data)


# ── Parallel Batch API (bypasses GIL via ProcessPool) ──────────

def encrypt_chunks_parallel(chunks: List[bytes], password: str) -> List[Tuple[bytes, str]]:
    """
    Encrypt multiple chunks in parallel using ProcessPoolExecutor.
    Derives key ONCE, then dispatches all chunks with pre-derived key.

    Returns:
        List of (ciphertext, sha256_hash) tuples in order.
    """
    key, salt = derive_key(password)
    pool = _get_pool()
    futures = [pool.submit(_worker_encrypt_keyed, chunk, key, salt) for chunk in chunks]
    results = [f.result() for f in futures]
    logger.debug(f"Parallel encrypted {len(chunks)} chunks across {_MAX_WORKERS} workers (key cached)")
    return results


def decrypt_chunks_parallel(chunks: List[bytes], password: str) -> List[bytes]:
    """
    Decrypt multiple chunks in parallel using ProcessPoolExecutor.
    Derives key ONCE from the first chunk's salt, then reuses for all.
    """
    if not chunks:
        return []
    # Extract salt from first chunk to derive key once
    first_salt = chunks[0][1:1 + SALT_SIZE]
    key, _ = derive_key(password, first_salt)
    pool = _get_pool()
    futures = [pool.submit(_worker_decrypt_keyed, chunk, key) for chunk in chunks]
    results = [f.result() for f in futures]
    logger.debug(f"Parallel decrypted {len(chunks)} chunks across {_MAX_WORKERS} workers (key cached)")
    return results


def hash_chunks_parallel(chunks: List[bytes]) -> List[str]:
    """Hash multiple chunks in parallel."""
    pool = _get_pool()
    futures = [pool.submit(_worker_hash, chunk) for chunk in chunks]
    return [f.result() for f in futures]


# ── Utility functions (kept for backward compat) ──────────────

def verify_integrity(encrypted: bytes, password: str) -> bool:
    try:
        decrypt(encrypted, password)
        return True
    except ValueError:
        return False


def tamper_test(encrypted: bytes, password: str) -> dict:
    results = {"original_ok": False, "tampered_detected": False}
    try:
        decrypt(encrypted, password)
        results["original_ok"] = True
    except ValueError:
        pass
    if len(encrypted) > HEADER_SIZE + 1:
        tampered = bytearray(encrypted)
        tampered[HEADER_SIZE + 1] ^= 0xFF
        try:
            decrypt(bytes(tampered), password)
        except ValueError:
            results["tampered_detected"] = True
    return results
