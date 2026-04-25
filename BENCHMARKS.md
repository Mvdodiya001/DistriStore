# DistriStore — Benchmarks

> All benchmarks run on the same machine with AES-256-GCM encryption + Merkle verification enabled.
> Last run: 2026-04-25

---

## 📊 1. Core Benchmark Suite (Encrypt → Store → Load → Decrypt)

10 file sizes tested end-to-end with AES-256-GCM encryption, SHA-256 hashing, and Merkle root verification.

| File Size | Chunks | Encrypt | Store | Load | Decrypt | **Total** | Status |
|-----------|--------|---------|-------|------|---------|-----------|--------|
| 64 KB | 1 | 32.9ms | 0.3ms | 0.0ms | 27.3ms | **60.6ms** | ✅ PASS |
| 128 KB | 1 | 27.3ms | 0.6ms | 0.1ms | 26.7ms | **54.6ms** | ✅ PASS |
| 256 KB | 1 | 27.2ms | 0.6ms | 0.1ms | 27.8ms | **55.7ms** | ✅ PASS |
| 512 KB | 2 | 28.0ms | 1.0ms | 0.2ms | 29.3ms | **58.5ms** | ✅ PASS |
| 1 MB | 4 | 32.3ms | 1.0ms | 0.4ms | 32.2ms | **65.9ms** | ✅ PASS |
| 2 MB | 8 | 34.2ms | 1.5ms | 0.7ms | 36.3ms | **72.7ms** | ✅ PASS |
| 3 MB | 12 | 39.3ms | 2.2ms | 1.4ms | 44.7ms | **87.6ms** | ✅ PASS |
| 4 MB | 16 | 43.0ms | 3.7ms | 2.3ms | 51.0ms | **100.0ms** | ✅ PASS |
| 5 MB | 20 | 47.2ms | 4.3ms | 2.8ms | 57.7ms | **111.9ms** | ✅ PASS |
| 10 MB | 40 | 75.0ms | 9.0ms | 8.8ms | 83.9ms | **176.7ms** | ✅ PASS |

- **Average turnaround:** 84.7ms
- **All integrity checks:** ✅ PASSED
- **Encryption:** AES-256-GCM (Authenticated Encryption)
- **Hashing:** SHA-256 per chunk + Merkle tree root
- **Chunk size:** 256 KB

### Key Observations

- Encrypt + decrypt dominate total time (store/load are near-instant for local disk)
- Time scales linearly with file size (O(N) confirmed)
- PBKDF2 key derivation is cached — derived once per file, not per chunk

---

## 📊 2. Phase 3 Performance Optimization (100MB Test)

### Before vs After Optimization

| Metric | Before (Phase 2) | After (Phase 3) | Speedup |
|--------|-------------------|------------------|---------|
| **100MB total** | 19.96s | **0.78s** | **25.6x** |
| 100MB chunk + encrypt | 10.03s | 0.45s | 22x |
| 100MB merge + decrypt | 9.93s | 0.33s | 30x |
| 10MB merge (in-memory) | 1009ms | 105ms | 10x |
| 10MB merge (to disk) | 982ms | 57ms | 17x |

### What Changed

| Fix | Problem | Solution |
|-----|---------|----------|
| O(N²) merger | `+=` byte concatenation caused quadratic reallocation | Pre-allocated `bytearray(total_size)` |
| Full file in RAM | `file.read()` loaded entire file before chunking | Generator: `file.read(256KB)` in loop |
| GIL blocking crypto | SHA-256 + AES blocked asyncio event loop | `ProcessPoolExecutor` for true parallelism |
| Sequential pipeline | Read All → Encrypt All → Store All | Streaming: Read → Encrypt → Store per chunk |
| PBKDF2 per-chunk | 100K iterations × 400 chunks = massive overhead | Derive key once, reuse for all chunks |

---

## 📊 3. ProcessPoolExecutor Crypto Benchmark

Parallel encryption/decryption of 8 × 256KB chunks using multiple CPU cores:

| Operation | Sequential | Parallel | Speedup |
|-----------|-----------|----------|---------|
| Encrypt (8 chunks) | 432ms | 55ms | **7.83x** |
| Decrypt (8 chunks) | ~400ms | 33ms | **~12x** |

> The ProcessPoolExecutor bypasses Python's Global Interpreter Lock (GIL),
> enabling true CPU parallelism for crypto operations.

---

## 📊 4. O(N) Linearity Verification

Testing that time scales linearly with file size (not quadratically):

| File Size | Time | Ratio |
|-----------|------|-------|
| 10 MB | 0.15s | — |
| 100 MB | 0.78s | **5.1x** |

> **Expected ratio for O(N): ~10x. Actual: 5.1x** — better than linear!
> This is because fixed overhead (key derivation, file hash) is amortized over more chunks.
> If it were O(N²), the ratio would be ~100x.

---

## 📊 5. Security Benchmarks

### AES-256-GCM Authenticated Encryption

| Test | Result |
|------|--------|
| Encrypt → Decrypt roundtrip | ✅ Identical data restored |
| Wrong password rejection | ✅ `ValueError` raised |
| Tampered ciphertext detection | ✅ GCM auth tag rejects |
| Single bit flip detection | ✅ Automatically caught |

### Merkle Tree Verification

| Test | Result |
|------|--------|
| Merkle root computation (4 chunks) | ✅ Correct |
| Merkle root computation (5 chunks) | ✅ Handles odd count |
| Merkle proof generation | ✅ 2-step proofs for 4 chunks |
| Merkle proof verification | ✅ All chunks verified |
| Tampered chunk → root mismatch | ✅ Detected |

---

## 📊 6. API & Network Benchmarks

### Parallel Swarming (8 chunks via HTTP)

| Method | Time | Throughput |
|--------|------|------------|
| Sequential download | 34.7ms | 57.7 MB/s |
| Parallel (concurrency=5) | 137.9ms | 14.5 MB/s |

> On localhost, sequential is faster (no latency to hide).
> On a real LAN with multiple peers, parallel swarming provides significant speedup.

### Health-Scored Peer Discovery

| Metric | Value |
|--------|-------|
| Health score computation time | <1ms |
| Health score variance (5 samples) | 5.7 |
| HELLO message size | ~300 bytes |
| Metrics included | RAM, CPU freq, CPU load, disk free |

---

## 📊 7. Throughput Summary

| File Size | Encrypt Speed | Decrypt Speed | Total Speed |
|-----------|--------------|---------------|-------------|
| 1 MB | 30.9 MB/s | 31.1 MB/s | 15.2 MB/s |
| 10 MB | 133.3 MB/s | 119.2 MB/s | 56.6 MB/s |
| 100 MB | 222.2 MB/s | 303.0 MB/s | 128.2 MB/s |

> Throughput improves with file size due to PBKDF2 key derivation being amortized.

---

## 🔄 How to Run

```bash
cd distristore
source .venv/bin/activate

# Core benchmark (10 file sizes)
python -m backend.benchmark.benchmark

# 100MB performance test
python -m tests.test_phase3_perf

# Security tests
python -m tests.test_phase2_gcm
python -m tests.test_phase2_merkle

# Swarming test (starts a server)
python -m tests.test_phase2_swarm

# Discovery health test
python -m tests.test_phase2_health
```

---

## 📋 Test Matrix

| Test | What it verifies | Command |
|------|-----------------|---------|
| Phase 1 | Node discovery + TCP | `python -m tests.test_phase1` |
| Phase 2 | File chunk + encrypt round-trip | `python -m tests.test_phase2` |
| Phase 2 GCM | AES-256-GCM tamper detection | `python -m tests.test_phase2_gcm` |
| Phase 2 Merkle | Merkle proofs + root verification | `python -m tests.test_phase2_merkle` |
| Phase 2 Swarm | Parallel chunk downloads | `python -m tests.test_phase2_swarm` |
| Phase 2 Health | psutil health scores in HELLO | `python -m tests.test_phase2_health` |
| Phase 3 | DHT routing + XOR distance | `python -m tests.test_phase3` |
| Phase 4 | Replication strategies | `python -m tests.test_phase4` |
| Phase 5 | HTTP API endpoints | `python -m tests.test_phase5` |
| Phase 3 Perf | 100MB O(N) performance | `python -m tests.test_phase3_perf` |
| Benchmark | 10-size throughput suite | `python -m backend.benchmark.benchmark` |
