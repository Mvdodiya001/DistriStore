# DistriStore — Benchmarks

> All benchmarks run on the same machine with AES-256-GCM encryption + Merkle verification enabled.
> Last verified: 2026-04-26 (Phase 10 — Dynamic Ports + Docker re-verification)

---

## 📊 1. Core Benchmark Suite (Encrypt → Store → Load → Decrypt)

10 file sizes tested end-to-end with AES-256-GCM encryption, SHA-256 hashing, and Merkle root verification.

| File Size | Chunks | Encrypt | Store | Load | Decrypt | **Total** | Status |
|-----------|--------|---------|-------|------|---------|-----------|--------|
| 64 KB | 1 | 46.4ms | 1.3ms | 0.1ms | 45.8ms | **93.6ms** | ✅ PASS |
| 128 KB | 1 | 46.0ms | 1.2ms | 0.1ms | 34.7ms | **81.9ms** | ✅ PASS |
| 256 KB | 1 | 34.9ms | 1.4ms | 0.2ms | 32.8ms | **69.4ms** | ✅ PASS |
| 512 KB | 2 | 30.9ms | 1.2ms | 0.2ms | 32.2ms | **64.6ms** | ✅ PASS |
| 1 MB | 4 | 31.9ms | 0.8ms | 0.3ms | 35.2ms | **68.2ms** | ✅ PASS |
| 2 MB | 8 | 36.6ms | 2.6ms | 1.4ms | 41.9ms | **82.6ms** | ✅ PASS |
| 3 MB | 12 | 40.7ms | 2.3ms | 1.8ms | 48.2ms | **93.0ms** | ✅ PASS |
| 4 MB | 16 | 43.4ms | 3.5ms | 2.2ms | 52.7ms | **101.8ms** | ✅ PASS |
| 5 MB | 20 | 48.8ms | 10.2ms | 1.7ms | 62.1ms | **122.7ms** | ✅ PASS |
| 10 MB | 40 | 70.6ms | 7.0ms | 8.8ms | 87.8ms | **174.2ms** | ✅ PASS |

- **Average turnaround:** 95.2ms
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
| HELLO message size | ~300 bytes |
| Metrics included | RAM, CPU freq, CPU load, disk free |

---

## 📊 7. Throughput Summary

| File Size | Encrypt Speed | Decrypt Speed | Total Speed |
|-----------|--------------|---------------|-------------|
| 1 MB | 31.3 MB/s | 28.4 MB/s | 14.7 MB/s |
| 10 MB | 141.6 MB/s | 113.9 MB/s | 57.4 MB/s |
| 100 MB | 263.2 MB/s | 344.8 MB/s | 149.3 MB/s |

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

### Download Architecture

| Component | Before (Phase 7) | After (Phase 8) |
|-----------|-------------------|------------------|
| Merge function | `merge_chunks()` — all in RAM | `merge_chunks_to_disk()` — streamed to disk |
| Response | `Response(content=file_data)` | `FileResponse(path=temp_file)` |
| Memory usage | O(N) — entire file in RAM | O(1) — kernel sendfile |
| Cleanup | None | `BackgroundTasks.add_task(os.remove)` |
| Max safe file | ~500 MB before OOM | Unlimited (disk-bound) |

---

## 📊 9. Docker Containerization Benchmarks (Phase 9)

### Container Build Sizes

| Image | Base | Final Size |
|-------|------|------------|
| `distristore-backend` | python:3.11-slim | 700 MB |
| `distristore-frontend` | nginx:alpine (multi-stage) | 93.5 MB |

### Docker API Performance

| Operation | File Size | Time | Notes |
|-----------|-----------|------|-------|
| Upload (via HTTP to container) | 1 MB | 54ms | python:3.11-slim on Docker |
| Upload (via HTTP to container) | 5 MB | 71ms | python:3.11-slim on Docker |
| Download (via HTTP from container) | 1 MB | 35ms | FileResponse streaming |
| Frontend page load | — | 2ms | nginx:alpine CDN-level speed |
| Health check response | — | <5ms | `/status` endpoint |

### Docker vs Local Performance Comparison

| Metric | Local (Native) | Docker Container | Overhead |
|--------|----------------|------------------|----------|
| 100MB Chunk + Encrypt | 0.38s | — | — |
| 100MB Merge + Decrypt | 0.29s | — | — |
| 1MB Upload (HTTP API) | ~45ms | 54ms | +20% |
| 1MB Download (HTTP API) | ~30ms | 35ms | +17% |
| Frontend load (nginx) | — | 2ms | Excellent |
| Container startup | — | ~5.7s | Health check wait |

> Docker overhead is minimal (~17-20%) for HTTP API operations.
> The frontend served via nginx:alpine is extremely fast (2ms page load).

### Port Allocation

| Service | Local (Native) | Docker |
|---------|---------------|--------|
| FastAPI API | Dynamic (8000-8010 fallback) | 8001 (mapped) |
| TCP P2P | Dynamic (OS-assigned, port=0) | 50001 (mapped) |
| UDP Discovery | 50000 (SO_REUSEADDR shared) | 50000/udp (mapped) |
| Frontend Dashboard | 5173 (Vite dev) | 3000 → nginx:80 |

---

## 📊 10. Dynamic Port Resolution (Phase 10)

### TCP Port Allocation

| Feature | Before | After |
|---------|--------|-------|
| TCP server port | Hardcoded `50001` | `port=0` → OS-assigned |
| Port discovery | Static config | Extracted via `socket.getsockname()` |
| HELLO broadcast | `tcp_port: 50001` | `tcp_port: state.tcp_port` (dynamic) |
| Multi-node conflict | ❌ Crash on same host | ✅ Each node gets unique port |

### API Port Fallback

| Port | Status | Action |
|------|--------|--------|
| 8000 | In use (mobsf) | Skip, try 8001 |
| 8001 | Available | ✅ Bind and serve |
| 8002-8010 | Reserved fallback | Available if needed |

### UDP Discovery Socket

| Feature | Before | After |
|---------|--------|-------|
| Socket creation | `create_datagram_endpoint(local_addr=...)` | Pre-configured `socket.socket()` |
| SO_REUSEADDR | Set after binding (too late) | Set before binding ✅ |
| SO_REUSEPORT | Best-effort | Best-effort with try/except |
| Multi-node sharing | ❌ Second node fails | ✅ Both share UDP port |

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
| Phase 1 | Node discovery + TCP (dynamic ports) | `python -m tests.test_phase1` | ✅ |
| Phase 2 | File chunk + encrypt round-trip | `python -m tests.test_phase2` | ✅ |
| Phase 2 GCM | AES-256-GCM tamper detection | `python -m tests.test_phase2_gcm` | ✅ |
| Phase 2 Merkle | Merkle proofs + root verification | `python -m tests.test_phase2_merkle` | ✅ |
| Phase 2 Swarm | Parallel chunk downloads | `python -m tests.test_phase2_swarm` | ✅ |
| Phase 2 Health | psutil health scores in HELLO | `python -m tests.test_phase2_health` | ✅ |
| Phase 3 | DHT routing + XOR distance | `python -m tests.test_phase3` | ✅ |
| Phase 4 | Replication strategies | `python -m tests.test_phase4` | ✅ |
| Phase 5 | HTTP API endpoints | `python -m tests.test_phase5` | ✅ |
| Phase 3 Perf | 100MB O(N) performance | `python -m tests.test_phase3_perf` | ✅ |
| Phase 8 | Memory-safe FileResponse download | `curl` upload → download → sha256sum | ✅ |
| Phase 9 | Docker build + compose validation | `docker compose up --build` | ✅ |
| Phase 10 | Dynamic ports + deployment scripts | `./start.sh` | ✅ |
| Benchmark | 10-size throughput suite | `python -m backend.benchmark.benchmark` | ✅ |
