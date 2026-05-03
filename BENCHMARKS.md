# DistriStore — Benchmarks

> All benchmarks run on the same machine with AES-256-GCM encryption + Merkle verification enabled.
> Last verified: 2026-05-03 (Phase 17 — Binary Protocol + SQLite Persistence)

---

## 📊 1. Core Benchmark Suite (Encrypt → Store → Load → Decrypt)

7 file sizes tested end-to-end with Phase 13 Dynamic Chunk Sizing, AES-256-GCM encryption, SHA-256 hashing, and Merkle root verification.

| File Size | Chunks | Encrypt | Store | Load | Decrypt | **Total** | Status |
|-----------|--------|---------|-------|------|---------|-----------|--------|
| 64 KB | 1 | 30.7ms | 0.6ms | 0.1ms | 26.0ms | **57.4ms** | ✅ PASS |
| 256 KB | 1 | 26.2ms | 0.4ms | 0.1ms | 25.0ms | **51.7ms** | ✅ PASS |
| 1 MB | 4 | 28.4ms | 1.0ms | 0.2ms | 29.4ms | **59.0ms** | ✅ PASS |
| 10 MB | 40 | 59.2ms | 4.2ms | 5.8ms | 68.4ms | **137.6ms** | ✅ PASS |
| 55 MB | 55 | 223.0ms | 27.4ms | 28.4ms | 269.3ms | **548.1ms** | ✅ PASS |
| 100 MB | 100 | 384.1ms | 168.4ms | 43.7ms | 571.1ms | **1167.3ms** | ✅ PASS |
| 505 MB | 127 | 2247.3ms | 422.3ms | 653.2ms | 3309.7ms | **6632.5ms** | ✅ PASS |

- **Average turnaround:** 1236.2ms
- **All integrity checks:** ✅ PASSED
- **Encryption:** AES-256-GCM (Authenticated Encryption)
- **Hashing:** SHA-256 per chunk + Merkle tree root
- **Chunk size:** Dynamic (256 KB / 1 MB / 4 MB) via Phase 13 logic

### Key Observations

- Encrypt + decrypt dominate total time (store/load are near-instant for local disk)
- Time scales linearly with file size (O(N) confirmed)
- PBKDF2 key derivation is cached — derived once per file, not per chunk

---

## 📊 2. Phase 3 Performance Optimization (100MB Test)

### Before vs After Optimization

| Metric | Before (Phase 2) | After (Phase 3) | Speedup |
|--------|-------------------|------------------|---------|
| **100MB total** | 19.96s | **0.67s** | **29.8x** |
| 100MB chunk + encrypt | 10.03s | 0.38s | 26x |
| 100MB merge + decrypt | 9.93s | 0.29s | 34x |
| 10MB merge (in-memory) | 1009ms | 73.3ms | 14x |
| 10MB merge (to disk) | 982ms | 52.6ms | 19x |

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
| Encrypt (8 chunks) | 405ms | 48ms | **8.52x** |
| Decrypt (8 chunks) | ~400ms | 31ms | **~13x** |

> The ProcessPoolExecutor bypasses Python's Global Interpreter Lock (GIL),
> enabling true CPU parallelism for crypto operations.

---

## 📊 4. O(N) Linearity Verification

Testing that time scales linearly with file size (not quadratically):

| File Size | Time | Ratio |
|-----------|------|-------|
| 10 MB | 0.11s | — |
| 100 MB | 0.67s | **5.9x** |

> **Expected ratio for O(N): ~10x. Actual: 5.9x** — better than linear!
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

### Zero-Trust Swarm Authentication (Phase 15)

| Test | Protocol | Result |
|------|----------|--------|
| UDP HMAC-SHA256 broadcast signing | UDP | ✅ Valid packets accepted |
| UDP HMAC mismatch → silent drop | UDP | ✅ Rejected cleanly |
| TCP AUTH handshake (2s timeout) | TCP | ✅ Valid AUTH → proceed |
| TCP AUTH invalid → connection closed | TCP | ✅ Rejected immediately |
| TCP AUTH timeout → connection closed | TCP | ✅ No hang/crash |

---

## 📊 6. API & Network Benchmarks

### Parallel Swarming (8 chunks via HTTP)

| Method | Time | Throughput |
|--------|------|------------|
| Sequential download (8 chunks) | 33.4ms | 62.8 MB/s |
| Parallel (concurrency=5) | 150.0ms | 14.0 MB/s |

> On localhost, sequential is faster (no latency to hide).
> On a real LAN with multiple peers, parallel swarming provides significant speedup.

### Health-Scored Peer Discovery

| Metric | Value |
|--------|-------|
| Health score computation time | <1ms |
| Health score average (5 samples) | 2249.0 |
| Health score variance (5 samples) | 1370.4 |
| HELLO message size | ~384 bytes (orjson + HMAC) |
| Metrics included | RAM, CPU freq, CPU load, disk free |

---

## 📊 7. Throughput Summary

| File Size | Encrypt Speed | Decrypt Speed | Total Speed |
|-----------|--------------|---------------|-------------|
| 1 MB | 35.2 MB/s | 34.0 MB/s | 16.9 MB/s |
| 10 MB | 168.9 MB/s | 146.2 MB/s | 72.7 MB/s |
| 100 MB | 260.3 MB/s | 175.1 MB/s | 85.7 MB/s |
| 505 MB | 224.7 MB/s | 152.6 MB/s | 76.1 MB/s |

> Throughput improves with file size due to PBKDF2 key derivation being amortized.

---

## 📊 8. Memory-Safe Download API (Phase 8)

The `/download/{hash}` endpoint uses `FileResponse` + `BackgroundTasks` for O(1) memory downloads:

| Test | File Size | SHA-256 Match | Temp Cleanup | Status |
|------|-----------|---------------|--------------|--------|
| Upload → Download → Verify | 64 KB | ✅ | ✅ 0 files | ✅ PASS |
| Upload → Download → Verify | 1 MB | ✅ | ✅ 0 files | ✅ PASS |
| Upload → Download → Verify | 5 MB | ✅ | ✅ 0 files | ✅ PASS |
| Wrong password rejection | 64 KB | — | — | ✅ HTTP 400 |

---

## 📊 9. Docker Containerization Benchmarks (Phase 9)

### Docker vs Local Performance Comparison

| Metric | Local (Native) | Docker Container | Overhead |
|--------|----------------|------------------|----------|
| 1MB Upload (HTTP API) | ~45ms | 54ms | +20% |
| 1MB Download (HTTP API) | ~30ms | 35ms | +17% |
| Frontend load (nginx) | — | 2ms | Excellent |
| Container startup | — | ~5.7s | Health check wait |

---

## 📊 10. Dynamic Port Resolution (Phase 10)

| Feature | Before | After |
|---------|--------|-------|
| TCP server port | Hardcoded `50001` | `port=0` → OS-assigned |
| Port discovery | Static config | Extracted via `socket.getsockname()` |
| HELLO broadcast | `tcp_port: 50001` | `tcp_port: state.tcp_port` (dynamic) |
| Multi-node conflict | ❌ Crash on same host | ✅ Each node gets unique port |

---

## 📊 11. Advanced Throughput & Reliability (Phase 13)

### Dynamic Chunk Sizing

| File Size Range | Chunk Size | Chunks for 100MB | Chunks for 1GB |
|----------------|-----------|-----------------|----------------|
| < 50 MB | 256 KB | 400 | 4,096 |
| 50–500 MB | 1 MB | 100 | 1,024 |
| > 500 MB | 4 MB | 25 | 256 |

> Dynamic sizing reduces manifest overhead by up to 16x for large files (4096 → 256 chunks for 1GB).

### Sliding Window Protocol

| Parameter | Value | Purpose |
|-----------|-------|---------|
| `MAX_WINDOW_SIZE` | 20 chunks | Concurrent in-flight transfers |
| `TIMEOUT_SECONDS` | 3.0s | Per-chunk ACK deadline |
| `SWEEP_INTERVAL` | 2.0s | Retransmit sweep frequency |
| `MAX_RETRIES` | 5 | Retry limit before giving up |
| Retransmission | Selective | Only timed-out chunks resent |

---

## 📊 12. SQLite Persistence (Phase 16)

### Database Performance

| Operation | Mechanism | Blocking? |
|-----------|-----------|----------|
| Save manifest | `INSERT OR REPLACE` via `asyncio.to_thread` | ❌ Non-blocking |
| Load manifest | `SELECT` via `asyncio.to_thread` | ❌ Non-blocking |
| Upsert peer | `INSERT OR REPLACE` via `asyncio.to_thread` | ❌ Non-blocking |
| Load all peers on boot | `SELECT *` via `asyncio.to_thread` | ❌ Non-blocking |

### Schema

| Table | Primary Key | Columns |
|-------|-------------|---------|
| `peers` | `node_id TEXT` | ip, tcp_port, api_port, name, health_score, last_seen |
| `manifests` | `file_hash TEXT` | filename, total_size, merkle_root, chunks_json |

> **WAL journal mode** enables concurrent reads during writes. All DB calls are wrapped in `asyncio.to_thread()` to keep the event loop responsive.

---

## 📊 13. Binary Protocol (Phase 17)

### Serialization Performance

| Layer | Before | After | Improvement |
|-------|--------|-------|-------------|
| **TCP framing** | JSON + newline delimiter | msgpack + 4-byte length prefix | ~2x faster serialize, ~33% smaller payload |
| **TCP chunk data** | base64-encoded string | Raw bytes (native msgpack) | **~33% bandwidth savings** |
| **UDP metadata** | stdlib `json` | `orjson` | 3-10x faster JSON encode/decode |
| **Windows asyncio** | Default `SelectorEventLoop` | `ProactorEventLoop` (IOCP) | Native I/O completion ports |

### Protocol Frame Format

```
┌──────────────────────┬──────────────────────────────┐
│ Length (4 bytes, BE)  │ msgpack Payload (N bytes)    │
│ uint32 big-endian    │ binary: dict with raw bytes  │
└──────────────────────┴──────────────────────────────┘
```

> The 4-byte length prefix is critical: msgpack binary output can contain `0x0A` (newline) bytes, making newline-delimited framing unsafe for binary chunk data.

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

# Docker benchmarks
docker compose up --build -d
curl -X POST -F "file=@testfile.bin" -F "password=test" http://localhost:8001/upload
docker compose down
```

---

## 📋 Test Matrix

| Test | What it verifies | Command | Status |
|------|-----------------|---------|--------|
| Phase 1 | Node discovery + TCP + HMAC auth | `python -m tests.test_phase1` | ✅ |
| Phase 2 | File chunk + encrypt + SQLite manifest | `python -m tests.test_phase2` | ✅ |
| Phase 2 GCM | AES-256-GCM tamper detection | `python -m tests.test_phase2_gcm` | ✅ |
| Phase 2 Merkle | Merkle proofs + root verification | `python -m tests.test_phase2_merkle` | ✅ |
| Phase 2 Swarm | Parallel chunk downloads | `python -m tests.test_phase2_swarm` | ✅ |
| Phase 2 Health | psutil health scores in HELLO | `python -m tests.test_phase2_health` | ✅ |
| Phase 3 | DHT routing + XOR distance | `python -m tests.test_phase3` | ✅ |
| Phase 4 | Replication strategies (msgpack binary) | `python -m tests.test_phase4` | ✅ |
| Phase 5 | HTTP API endpoints + SQLite files | `python -m tests.test_phase5` | ✅ |
| Phase 3 Perf | 100MB O(N) performance | `python -m tests.test_phase3_perf` | ✅ |
| Phase 10 | Dynamic ports + deployment scripts | `python -m tests.test_phase10_dynamic_ports` | ✅ |
| Phase 12 | Cross-node manifest/chunk fetch | `python -m tests.test_phase12_cross_node` | ✅ |
| Phase 13 | Dynamic chunks + sliding window + async I/O | `python -m tests.test_phase13_throughput` | ✅ |
| Benchmark | 10-size throughput suite | `python -m backend.benchmark.benchmark` | ✅ |
