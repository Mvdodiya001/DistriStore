"""DistriStore — Chunk Pipeline (Streaming Architecture)

Phase 3: Instead of Read All → Chunk All → Encrypt All → Send All,
this pipeline does: Read 256KB → Compress → Encrypt → Store → Read next.

The network transmits chunk[0] while the CPU encrypts chunk[1].
Uses asyncio + ProcessPoolExecutor for true overlap.

Phase 10: Advanced Throughput
  - Dynamic chunk sizing via get_optimal_chunk_size()
  - Disk writes wrapped in asyncio.to_thread (non-blocking)

Phase 18: Per-chunk zstd compression in the pipeline workers.
"""

import asyncio
import os
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Optional, Callable, Awaitable

from backend.file_engine.crypto import (
    encrypt, decrypt, sha256_hash, _worker_encrypt,
    _get_pool, _MAX_WORKERS,
)
from backend.file_engine.chunker import (
    _stream_chunks, _streaming_file_hash,
    _async_streaming_file_hash,
    FileManifest, ChunkInfo,
    compute_merkle_root, DEFAULT_CHUNK_SIZE, get_optimal_chunk_size,
)
from backend.utils.logger import get_logger

logger = get_logger("file_engine.pipeline")


async def pipeline_chunk_and_store(
    file_path: str,
    store_fn: Callable[[str, bytes], Awaitable[None]],
    chunk_size: int = None,
    password: str = None,
) -> FileManifest:
    """
    Streaming pipeline: Read → Encrypt → Store, one chunk at a time.

    If chunk_size is None, uses get_optimal_chunk_size() to auto-select
    based on file size (256KB / 1MB / 4MB).

    While chunk[N] is being stored (I/O bound), chunk[N+1] is being
    encrypted (CPU bound in a process pool). This overlaps I/O and CPU.

    Args:
        file_path: Path to the file to process.
        store_fn: async callable(chunk_hash, chunk_data) to persist each chunk.
        chunk_size: Chunk size in bytes.
        password: Encryption password (None = no encryption).

    Returns:
        Complete FileManifest with all chunks and Merkle root.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    file_size = path.stat().st_size

    # Auto-select chunk size if not explicitly provided
    if chunk_size is None:
        chunk_size = get_optimal_chunk_size(file_size)
    logger.info(f"Chunk size for '{path.name}' ({file_size} bytes): {chunk_size // 1024}KB")

    loop = asyncio.get_running_loop()
    pool = _get_pool()

    # Compute file hash in a worker process (doesn't block event loop)
    file_hash = await loop.run_in_executor(pool, _streaming_file_hash, file_path)

    manifest = FileManifest(
        original_filename=path.name,
        original_size=file_size,
        file_hash=file_hash,
        chunk_size=chunk_size,
    )

    chunk_hashes = []
    pending_store = None  # Track the previous store task for overlap

    for idx, raw_bytes in _stream_chunks(file_path, chunk_size):
        # Encrypt in process pool (CPU-bound, bypasses GIL)
        if password:
            ct, ch = await loop.run_in_executor(pool, _worker_encrypt, raw_bytes, password)
            encrypted = True
        else:
            ct = raw_bytes
            ch = await loop.run_in_executor(pool, sha256_hash, raw_bytes)
            encrypted = False

        chunk_hashes.append(ch)
        manifest.chunks.append(ChunkInfo(
            index=idx, chunk_hash=ch,
            size=len(ct), encrypted=encrypted,
        ))

        # Wait for previous store to finish before starting new one (backpressure)
        if pending_store is not None:
            await pending_store

        # Start storing this chunk (I/O-bound) — overlaps with next read+encrypt
        pending_store = asyncio.create_task(store_fn(ch, ct))

    # Wait for the last store
    if pending_store is not None:
        await pending_store

    manifest.merkle_root = compute_merkle_root(chunk_hashes)
    manifest.compression = "zstd"

    logger.info(
        f"Pipeline chunked '{path.name}' ({file_size} bytes) "
        f"-> {len(manifest.chunks)} chunks "
        f"({'encrypted' if password else 'plain'}, zstd) "
        f"[pipelined, {_MAX_WORKERS} workers]"
    )
    return manifest


async def pipeline_merge_to_disk(
    manifest: FileManifest,
    load_fn: Callable[[str], Awaitable[bytes]],
    output_path: str,
    password: str = None,
) -> str:
    """
    Streaming merge pipeline: Load → Decrypt → Write, one chunk at a time.
    O(1) memory — never holds more than 2 chunks in RAM.

    Args:
        manifest: File manifest with chunk ordering.
        load_fn: async callable(chunk_hash) -> bytes to fetch each chunk.
        output_path: Where to write the reassembled file.
        password: Decryption password.

    Returns:
        Path to the output file.
    """
    import hashlib
    loop = asyncio.get_running_loop()
    pool = _get_pool()
    h = hashlib.sha256()

    ordered = sorted(manifest.chunks, key=lambda c: c.index)

    with open(output_path, "wb") as f:
        # Pre-fetch the next chunk while decrypting the current one
        next_data = None
        for i, info in enumerate(ordered):
            # Load chunk
            if next_data is not None:
                data = next_data
            else:
                data = await load_fn(info.chunk_hash)

            # Pre-fetch next chunk (overlaps with decrypt below)
            prefetch = None
            if i + 1 < len(ordered):
                prefetch = asyncio.create_task(load_fn(ordered[i + 1].chunk_hash))

            # Decrypt in process pool
            if info.encrypted and password:
                from backend.file_engine.crypto import _worker_decrypt_keyed, _worker_decrypt_keyed_nocompress, derive_key, SALT_SIZE
                # Derive key from first chunk salt
                first_salt = data[1:1 + SALT_SIZE]
                dec_key, _ = derive_key(password, first_salt)
                if manifest.compression == "zstd":
                    plaintext = await loop.run_in_executor(pool, _worker_decrypt_keyed, data, dec_key)
                else:
                    plaintext = await loop.run_in_executor(pool, _worker_decrypt_keyed_nocompress, data, dec_key)
            else:
                # Unencrypted: may still need decompression
                if manifest.compression == "zstd":
                    import zstandard as _zstd
                    plaintext = _zstd.ZstdDecompressor().decompress(data)
                else:
                    plaintext = data

            # Non-blocking disk write via asyncio.to_thread
            await asyncio.to_thread(f.write, plaintext)
            h.update(plaintext)

            # Get prefetched data
            if prefetch is not None:
                next_data = await prefetch
            else:
                next_data = None

    result_hash = h.hexdigest()
    if result_hash != manifest.file_hash:
        os.unlink(output_path)
        raise ValueError(
            f"Pipeline merge integrity failed! "
            f"Expected {manifest.file_hash[:16]}... got {result_hash[:16]}..."
        )

    logger.info(
        f"Pipeline merged {len(ordered)} chunks -> {output_path} "
        f"(integrity ✅ O(1) memory)"
    )
    return output_path
