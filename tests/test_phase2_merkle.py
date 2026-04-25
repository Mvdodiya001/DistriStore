"""
DistriStore — Phase 2.2 Verification: Merkle Manifest & Content Addressing

Tests:
  1. Merkle root computation (odd & even chunk counts)
  2. Merkle proof generation & verification
  3. Tampered chunk detection via Merkle root
  4. Full file cycle with Merkle verification
  5. Content-addressing: file_hash as DHT key

Run: python -m tests.test_phase2_merkle
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from backend.utils.logger import setup_logging
from backend.file_engine.crypto import sha256_hash
from backend.file_engine.chunker import (
    compute_merkle_root, compute_merkle_proof, verify_merkle_proof,
    chunk_file, merge_chunks, FileManifest,
)


def run_test():
    setup_logging("INFO")
    print("=" * 65)
    print("  DistriStore — Phase 2.2: Merkle Manifest Verification")
    print("=" * 65)

    # ── Test 1: Merkle Root Computation ────────────────────────
    print("\n[1/5] Testing Merkle root computation...")

    # Even number of leaves
    hashes_4 = [sha256_hash(f"chunk_{i}".encode()) for i in range(4)]
    root_4 = compute_merkle_root(hashes_4)
    assert len(root_4) == 64, "Root should be 64-char hex"
    print(f"  4 chunks -> root: {root_4[:24]}...")

    # Odd number of leaves (last is duplicated)
    hashes_5 = [sha256_hash(f"chunk_{i}".encode()) for i in range(5)]
    root_5 = compute_merkle_root(hashes_5)
    assert root_5 != root_4, "Different inputs should give different roots"
    print(f"  5 chunks -> root: {root_5[:24]}...")

    # Single leaf
    root_1 = compute_merkle_root([hashes_4[0]])
    assert root_1 == hashes_4[0], "Single leaf should be its own root"
    print(f"  1 chunk  -> root: {root_1[:24]}... (same as leaf)")

    # Deterministic
    assert compute_merkle_root(hashes_4) == root_4, "Should be deterministic"
    print("  ✅ Merkle root computation correct")

    # ── Test 2: Merkle Proof Generation & Verification ─────────
    print("\n[2/5] Testing Merkle proof generation & verification...")
    for i in range(len(hashes_4)):
        proof = compute_merkle_proof(hashes_4, i)
        valid = verify_merkle_proof(hashes_4[i], proof, root_4)
        assert valid, f"Proof for chunk {i} should be valid!"
        print(f"  Chunk {i}: proof has {len(proof)} steps -> verified ✅")

    # Test with 5 chunks (odd)
    for i in range(len(hashes_5)):
        proof = compute_merkle_proof(hashes_5, i)
        valid = verify_merkle_proof(hashes_5[i], proof, root_5)
        assert valid, f"Proof for chunk {i} (odd set) should be valid!"
    print(f"  5-chunk proofs: all verified ✅")
    print("  ✅ Merkle proofs working correctly")

    # ── Test 3: Tampered Chunk Detection ───────────────────────
    print("\n[3/5] Testing tampered chunk detection via Merkle root...")
    tampered_hashes = list(hashes_4)
    tampered_hashes[2] = sha256_hash(b"EVIL_DATA")
    tampered_root = compute_merkle_root(tampered_hashes)
    assert tampered_root != root_4, "Tampered tree should have different root!"
    print(f"  Original root:  {root_4[:24]}...")
    print(f"  Tampered root:  {tampered_root[:24]}...")

    # Verify tampered proof fails
    fake_proof = compute_merkle_proof(hashes_4, 2)
    invalid = verify_merkle_proof(tampered_hashes[2], fake_proof, root_4)
    assert not invalid, "Tampered chunk should fail proof against original root"
    print("  ✅ Tampered chunk correctly rejected by Merkle verification")

    # ── Test 4: Full File Cycle with Merkle ────────────────────
    print("\n[4/5] Testing full file cycle with Merkle manifest...")
    import shutil
    tmp = os.path.join(os.path.dirname(__file__), "..", ".test_merkle")
    os.makedirs(tmp, exist_ok=True)

    test_data = os.urandom(768 * 1024)  # 768 KB -> 3 chunks
    test_file = os.path.join(tmp, "merkle_test.bin")
    with open(test_file, "wb") as f:
        f.write(test_data)

    manifest, chunks = chunk_file(test_file, chunk_size=262144, password="merkle-pass")
    print(f"  Chunks: {len(chunks)}")
    print(f"  Merkle root: {manifest.merkle_root[:32]}...")
    print(f"  File hash (content address): {manifest.file_hash[:32]}...")

    # Manifest should have all required fields
    d = manifest.to_dict()
    assert d["version"] == 2
    assert d["merkle_root"] == manifest.merkle_root
    assert d["chunk_count"] == len(chunks)
    assert d["file_hash"] == manifest.file_hash
    print(f"  Manifest version: {d['version']}")
    print(f"  Manifest fields: ✅ All present")

    # Roundtrip via to_dict/from_dict
    restored_manifest = FileManifest.from_dict(d)
    assert restored_manifest.merkle_root == manifest.merkle_root
    print("  Manifest serialization roundtrip: ✅")

    # Merge with Merkle verification
    restored = merge_chunks(manifest, chunks, password="merkle-pass")
    assert restored == test_data
    print("  ✅ Full file cycle with Merkle verification passed")

    # ── Test 5: Individual Chunk Proof Verification ────────────
    print("\n[5/5] Testing per-chunk Merkle proof via manifest...")
    for i in range(len(manifest.chunks)):
        proof = manifest.get_merkle_proof(i)
        valid = verify_merkle_proof(
            manifest.chunks[i].chunk_hash, proof, manifest.merkle_root
        )
        assert valid, f"Chunk {i} proof failed!"
        print(f"  Chunk {i} ({manifest.chunks[i].chunk_hash[:16]}...): proof valid ✅")

    shutil.rmtree(tmp, ignore_errors=True)

    print("\n" + "=" * 65)
    print("  ✅ PHASE 2.2 VERIFICATION PASSED — Merkle Manifest Working!")
    print("=" * 65)


if __name__ == "__main__":
    try:
        run_test()
    except AssertionError as e:
        print(f"\n  ❌ VERIFICATION FAILED: {e}")
        sys.exit(1)
