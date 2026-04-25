"""
DistriStore — Phase 2 Verification Test
Verification Gate 2: Input a 1MB file, chunk it, encrypt it,
decrypt it, and merge it back perfectly.

Run from distristore/ directory:
    python -m tests.test_phase2
"""

import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from backend.utils.logger import setup_logging
from backend.file_engine.chunker import chunk_file, merge_chunks
from backend.file_engine.crypto import sha256_hash
from backend.storage.local_store import LocalStore


def run_test():
    setup_logging("DEBUG")
    print("=" * 60)
    print("  DistriStore — Phase 2 Verification Test")
    print("=" * 60)

    # ── Step 1: Create a 1MB test file ─────────────────────────
    print("\n[1/6] Creating 1MB test file...")
    test_data = os.urandom(1024 * 1024)  # 1 MB random data
    original_hash = sha256_hash(test_data)

    tmp_dir = os.path.join(os.path.dirname(__file__), "..", ".test_tmp")
    os.makedirs(tmp_dir, exist_ok=True)
    test_file = os.path.join(tmp_dir, "test_1mb.bin")
    with open(test_file, "wb") as f:
        f.write(test_data)
    print(f"  File: {test_file}")
    print(f"  Size: {len(test_data)} bytes")
    print(f"  Hash: {original_hash[:24]}...")
    print("  ✅ Test file created")

    # ── Step 2: Chunk + Encrypt ────────────────────────────────
    print("\n[2/6] Chunking & encrypting with password...")
    password = "test-password-123"
    manifest, chunks = chunk_file(test_file, chunk_size=262144, password=password)
    print(f"  Chunks: {len(chunks)}")
    print(f"  Manifest file_hash: {manifest.file_hash[:24]}...")
    for c in manifest.chunks:
        print(f"    chunk[{c.index}]: hash={c.chunk_hash[:16]}... size={c.size} encrypted={c.encrypted}")
    print("  ✅ Chunked & encrypted")

    # ── Step 3: Store chunks to disk ───────────────────────────
    print("\n[3/6] Saving chunks to local store...")
    store = LocalStore(os.path.join(tmp_dir, ".storage"))
    for info, data in zip(manifest.chunks, chunks):
        store.save_chunk(info.chunk_hash, data)
    store.save_manifest(manifest.file_hash, manifest.to_dict())
    print(f"  Storage size: {store.get_storage_size()} bytes")
    print(f"  Stored chunks: {len(store.list_chunks())}")
    print("  ✅ Chunks saved to disk")

    # ── Step 4: Load chunks back from disk ─────────────────────
    print("\n[4/6] Loading chunks from disk...")
    loaded_chunks = []
    for info in manifest.chunks:
        data = store.load_chunk(info.chunk_hash)
        assert data is not None, f"Chunk {info.chunk_hash[:12]} not found!"
        loaded_chunks.append(data)
    print(f"  Loaded {len(loaded_chunks)} chunks")
    print("  ✅ All chunks loaded")

    # ── Step 5: Merge + Decrypt ────────────────────────────────
    print("\n[5/6] Merging & decrypting...")
    restored_data = merge_chunks(manifest, loaded_chunks, password=password)
    restored_hash = sha256_hash(restored_data)
    print(f"  Restored size: {len(restored_data)} bytes")
    print(f"  Restored hash: {restored_hash[:24]}...")

    # ── Step 6: Verify integrity ───────────────────────────────
    print("\n[6/6] Verifying integrity...")
    assert restored_data == test_data, "DATA MISMATCH!"
    assert restored_hash == original_hash, "HASH MISMATCH!"
    print(f"  Original hash:  {original_hash[:24]}...")
    print(f"  Restored hash:  {restored_hash[:24]}...")
    print("  ✅ Perfect match — data integrity verified")

    # Cleanup
    import shutil
    shutil.rmtree(tmp_dir, ignore_errors=True)

    print("\n" + "=" * 60)
    print("  ✅ PHASE 2 VERIFICATION PASSED — All checks green!")
    print("=" * 60)


if __name__ == "__main__":
    try:
        run_test()
    except AssertionError as e:
        print(f"\n  ❌ VERIFICATION FAILED: {e}")
        sys.exit(1)
