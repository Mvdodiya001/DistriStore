"""
DistriStore — Phase 2.1 Verification: AES-256-GCM Authenticated Encryption

Tests:
  1. Encrypt/decrypt round-trip with correct password
  2. Wrong password → automatic detection (ValueError)
  3. Tampered ciphertext → automatic detection (ValueError)
  4. Full file chunk/encrypt/decrypt/merge cycle with GCM

Run: python -m tests.test_phase2_gcm
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from backend.utils.logger import setup_logging
from backend.file_engine.crypto import (
    encrypt, decrypt, sha256_hash, verify_integrity, tamper_test, HEADER_SIZE
)
from backend.file_engine.chunker import chunk_file, merge_chunks
from backend.storage.local_store import LocalStore


def run_test():
    setup_logging("INFO")
    print("=" * 65)
    print("  DistriStore — Phase 2.1: AES-256-GCM Verification")
    print("=" * 65)

    # ── Test 1: Basic Encrypt/Decrypt Round-Trip ───────────────
    print("\n[1/5] Testing AES-256-GCM encrypt/decrypt round-trip...")
    plaintext = b"Hello, DistriStore! This is a secret message for GCM testing."
    password = "super-secret-password"

    ciphertext = encrypt(plaintext, password)
    assert len(ciphertext) == len(plaintext) + HEADER_SIZE
    print(f"  Plaintext:  {len(plaintext)} bytes")
    print(f"  Ciphertext: {len(ciphertext)} bytes (overhead={HEADER_SIZE}B)")

    decrypted = decrypt(ciphertext, password)
    assert decrypted == plaintext, "Decrypted data doesn't match!"
    print(f"  Decrypted:  {len(decrypted)} bytes ✅")
    print("  ✅ Round-trip passed")

    # ── Test 2: Wrong Password Detection ───────────────────────
    print("\n[2/5] Testing wrong password detection...")
    try:
        decrypt(ciphertext, "wrong-password")
        assert False, "Should have raised ValueError!"
    except ValueError as e:
        print(f"  Wrong password correctly detected: {str(e)[:60]}...")
        print("  ✅ Wrong password rejected")

    # ── Test 3: Tamper Detection ───────────────────────────────
    print("\n[3/5] Testing GCM tamper detection...")
    results = tamper_test(ciphertext, password)
    assert results["original_ok"], "Original should decrypt fine!"
    assert results["tampered_detected"], "Tampered data should be detected!"
    print(f"  Original data decrypts:  ✅ {results['original_ok']}")
    print(f"  Tampered data detected:  ✅ {results['tampered_detected']}")
    print("  ✅ GCM authenticated encryption prevents tampering")

    # ── Test 4: Large Data (1MB) ───────────────────────────────
    print("\n[4/5] Testing 1MB data block...")
    big_data = os.urandom(1024 * 1024)
    big_ct = encrypt(big_data, password)
    big_pt = decrypt(big_ct, password)
    assert big_pt == big_data
    print(f"  1MB encrypted -> {len(big_ct)} bytes -> decrypted ✅")
    print("  ✅ Large data round-trip passed")

    # ── Test 5: Full File Chunk/Encrypt/Merge Cycle ────────────
    print("\n[5/5] Testing full file chunk → encrypt → store → load → decrypt → merge...")
    import shutil
    tmp = os.path.join(os.path.dirname(__file__), "..", ".test_gcm")
    os.makedirs(tmp, exist_ok=True)

    # Create 512KB test file
    test_data = os.urandom(512 * 1024)
    test_file = os.path.join(tmp, "gcm_test.bin")
    with open(test_file, "wb") as f:
        f.write(test_data)

    original_hash = sha256_hash(test_data)

    # Chunk + encrypt
    manifest, chunks = chunk_file(test_file, chunk_size=262144, password=password)
    print(f"  Chunked: {len(chunks)} chunks, encrypted with AES-256-GCM")

    # Store to disk
    store = LocalStore(os.path.join(tmp, ".storage"))
    for info, data in zip(manifest.chunks, chunks):
        store.save_chunk(info.chunk_hash, data)

    # Load from disk
    loaded = [store.load_chunk(info.chunk_hash) for info in manifest.chunks]

    # Merge + decrypt
    restored = merge_chunks(manifest, loaded, password=password)
    restored_hash = sha256_hash(restored)

    assert restored == test_data, "Data mismatch!"
    assert restored_hash == original_hash, "Hash mismatch!"
    print(f"  Original hash:  {original_hash[:32]}...")
    print(f"  Restored hash:  {restored_hash[:32]}...")
    print("  ✅ Full file cycle with GCM passed — integrity verified")

    # Bonus: verify a chunk is tamper-proof
    chunk_data = loaded[0]
    tampered_chunk = bytearray(chunk_data)
    tampered_chunk[50] ^= 0xFF
    try:
        decrypt(bytes(tampered_chunk), password)
        print("  ❌ Tampered chunk was NOT detected!")
    except ValueError:
        print("  ✅ Bonus: tampered chunk automatically rejected by GCM")

    shutil.rmtree(tmp, ignore_errors=True)

    print("\n" + "=" * 65)
    print("  ✅ PHASE 2.1 VERIFICATION PASSED — AES-256-GCM Working!")
    print("=" * 65)


if __name__ == "__main__":
    try:
        run_test()
    except AssertionError as e:
        print(f"\n  ❌ VERIFICATION FAILED: {e}")
        sys.exit(1)
