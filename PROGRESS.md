# DistriStore — Project Progress Tracker

> **LAN-Optimized P2P Distributed Hash Table (DHT) Storage Framework**
> Last Updated: 2026-05-03

---

## 📊 Overall Status

```
Phase 1 (Foundation)      ████████████████████ 100% ✅
Phase 2 (File Engine)     ████████████████████ 100% ✅
Phase 3 (DHT & Routing)   ████████████████████ 100% ✅
Phase 4 (Strategies)      ████████████████████ 100% ✅
Phase 5 (API & SDK)       ████████████████████ 100% ✅
Phase 6 (Frontend GUI)    ████████████████████ 100% ✅
Phase 7 (Advanced)        ████████████████████ 100% ✅
Phase 2R (Research)       ████████████████████ 100% ✅
Phase 3O (Optimization)   ████████████████████ 100% ✅
Phase 8 (Enterprise UI)   ████████████████████ 100% ✅
Phase 9 (Docker)          ████████████████████ 100% ✅
Phase 10 (Dynamic Ports)  ████████████████████ 100% ✅
Phase 11 (LAN Access)     ████████████████████ 100% ✅
Phase 12 (Cross-Node)     ████████████████████ 100% ✅
Phase 13 (Adv Throughput) ████████████████████ 100% ✅
Phase 14 (Storage Quotas) ████████████████████ 100% ✅
Phase 15 (Swarm Auth)     ████████████████████ 100% ✅
Phase 16 (SQLite)         ████████████████████ 100% ✅
Phase 17 (Binary Proto)   ████████████████████ 100% ✅
Phase 18 (ZSTD Compress)  ████████████████████ 100% ✅
```

**Current Position: All 20 phases complete. V2.1 — ZSTD Stream Compression.**

---

## 🔷 Phase 1 — Node State & Discovery

| Component | File | Status |
|-----------|------|--------|
| Node State (asyncio locks) | `backend/node/state.py` | ✅ |
| Node Orchestrator | `backend/node/node.py` | ✅ |
| UDP Broadcast Discovery | `backend/network/discovery.py` | ✅ |
| TCP Connection Manager | `backend/network/connection.py` | ✅ |
| YAML Config Loader | `backend/utils/config.py` | ✅ |
| Centralized Logger | `backend/utils/logger.py` | ✅ |

**Verification:** `python -m tests.test_phase1` — 2 nodes discover each other + TCP handshake ✅

---

## 🔷 Phase 2 — File Engine & Cryptography

| Component | File | Status |
|-----------|------|--------|
| AES-256 Encryption | `backend/file_engine/crypto.py` | ✅ |
| File Chunker (256KB) | `backend/file_engine/chunker.py` | ✅ |
| Local Chunk Storage | `backend/storage/local_store.py` | ✅ |

**Verification:** `python -m tests.test_phase2` — 1MB file round-trip perfect ✅

---

## 🔷 Phase 3 — DHT & Routing

| Component | File | Status |
|-----------|------|--------|
| XOR Distance Calculation | `backend/dht/routing.py` | ✅ |
| Dynamic Routing Table | `backend/dht/routing.py` | ✅ |
| Peer Search / Lookup | `backend/dht/lookup.py` | ✅ |
| Binary Protocol Messages | `backend/network/protocol.py` | ✅ |

**Verification:** `python -m tests.test_phase3` — XOR distance, closest-peer ✅

---

## 🔷 Phase 4 — Framework Strategies

| Component | File | Status |
|-----------|------|--------|
| Heuristic Peer Scoring | `backend/strategies/selector.py` | ✅ |
| k-Replication Engine | `backend/strategies/replication.py` | ✅ |

**Verification:** `python -m tests.test_phase4` — Chunks replicated to peers B & C ✅

---

## 🔷 Phase 5 — API Layer & Python SDK

| Component | File | Status |
|-----------|------|--------|
| FastAPI Entry Point | `backend/main.py` | ✅ |
| REST Routes (upload/download/status/files) | `backend/api/routes.py` | ✅ |
| Python SDK Client | `backend/framework/client.py` | ✅ |

**Verification:** `python -m tests.test_phase5` — HTTP upload/download/status ✅

---

## 🔷 Phase 6 — Frontend GUI (React + Vite)

| Component | File | Status |
|-----------|------|--------|
| Dashboard + Stats | `frontend/src/App.jsx` | ✅ |
| Upload (Drag & Drop) | `frontend/src/App.jsx` | ✅ |
| Download by Hash | `frontend/src/App.jsx` | ✅ |
| Design System (Dark Mode) | `frontend/src/index.css` | ✅ |

**Verification:** `cd frontend && npx vite build` — Builds clean ✅

---

## 🔷 Phase 7 — Advanced Features

| Component | File | Status |
|-----------|------|--------|
| Heartbeat Monitor | `backend/advanced/heartbeat.py` | ✅ |
| Self-Healing (Re-replication) | `backend/advanced/self_healing.py` | ✅ |
| Benchmark Suite (10 sizes) | `backend/benchmark/benchmark.py` | ✅ |

**Verification:** `python -m backend.benchmark.benchmark` — All 10 tests PASS ✅

---

## 🔶 Phase 2R — Research & Performance Upgrade

| Step | Upgrade | File | Status |
|------|---------|------|--------|
| 2.1 | AES-256-GCM Authenticated Encryption | `backend/file_engine/crypto.py` | ✅ |
| 2.2 | Merkle Manifest (Content-Addressing) | `backend/file_engine/chunker.py` | ✅ |
| 2.3 | Parallel Swarming Downloads | `backend/framework/client.py` + `backend/api/routes.py` | ✅ |
| 2.4 | Health-Scored Peer Discovery | `backend/network/discovery.py` | ✅ |
| 2.5 | Frontend Visualization (Topology, Chunk Map, Perf Gauge) | `frontend/src/App.jsx` + `frontend/src/index.css` | ✅ |

**Verifications:**
- `python -m tests.test_phase2_gcm` — GCM tamper detection ✅
- `python -m tests.test_phase2_merkle` — Merkle proofs verified ✅
- `python -m tests.test_phase2_swarm` — Parallel chunk download ✅
- `python -m tests.test_phase2_health` — Health scores in HELLO ✅

---

## 🔶 Phase 3O — O(N) Performance Optimization

| Fix | Problem | Solution | Status |
|-----|---------|----------|--------|
| 1 | O(N²) merger (byte concatenation) | Pre-allocated `bytearray(total_size)` + disk streaming | ✅ |
| 2 | Full file loaded into RAM | Generator: `file.read(chunk_size)` in `while` loop | ✅ |
| 3 | GIL blocks crypto on asyncio | `ProcessPoolExecutor` for encrypt/decrypt/hash | ✅ |
| 4 | Sequential Read→Encrypt→Store | Streaming pipeline with overlapped I/O + CPU | ✅ |
| — | PBKDF2 called per-chunk (400x) | Derive key once, pass to all chunks | ✅ |

**Performance Results:**

| Metric | Before | After | Speedup |
|--------|--------|-------|---------|
| **100MB total** | 19.96s | **0.67s** | **29.8x** |
| 100MB encrypt | 10.03s | 0.38s | 26x |
| 100MB decrypt | 9.93s | 0.29s | 34x |
| ProcessPool vs sequential | 1x | **8.52x** | GIL bypassed |
| O(N) linearity (10MB→100MB) | — | **5.9x ratio** | Confirmed |

**Verification:** `python -m tests.test_phase3_perf` — 100MB in 0.67s ✅

---

## 🔷 Phase 8 — Enterprise Frontend & Memory-Safe Downloads

### Backend: Memory-Safe Download Fix

| Change | Before | After | Status |
|--------|--------|-------|--------|
| Download endpoint | `Response(content=file_data)` — O(N) RAM | `FileResponse(path=temp_file)` — O(1) RAM | ✅ |
| Merge strategy | `merge_chunks()` in memory | `merge_chunks_to_disk()` streaming | ✅ |
| Temp cleanup | None | `BackgroundTasks.add_task(os.remove)` | ✅ |

### Frontend: Enterprise Architecture Refactor

| Component | File | Status |
|-----------|------|--------|
| API Service Layer | `frontend/src/api/client.js` | ✅ |
| Zustand Global Store | `frontend/src/store/useNetworkStore.js` | ✅ |
| Card (Atomic UI) | `frontend/src/components/ui/Card.jsx` | ✅ |
| Button (Atomic UI) | `frontend/src/components/ui/Button.jsx` | ✅ |
| CopyButton (Atomic UI) | `frontend/src/components/ui/CopyButton.jsx` | ✅ |
| StatCard (Atomic UI) | `frontend/src/components/ui/StatCard.jsx` | ✅ |
| Header (Layout) | `frontend/src/components/layout/Header.jsx` | ✅ |
| Sidebar (Layout) | `frontend/src/components/layout/Sidebar.jsx` | ✅ |
| NetworkTopology (Viz) | `frontend/src/components/network/NetworkTopology.jsx` | ✅ |
| TransferSpeedChart (Viz) | `frontend/src/components/network/TransferSpeedChart.jsx` | ✅ |
| PeerTable (Viz) | `frontend/src/components/network/PeerTable.jsx` | ✅ |
| DashboardPage | `frontend/src/pages/DashboardPage.jsx` | ✅ |
| UploadPage | `frontend/src/pages/UploadPage.jsx` | ✅ |
| DownloadPage | `frontend/src/pages/DownloadPage.jsx` | ✅ |
| SettingsPage | `frontend/src/pages/SettingsPage.jsx` | ✅ |
| BrowserRouter App | `frontend/src/App.jsx` | ✅ |

### Dependencies Added
`react-router-dom`, `recharts`, `lucide-react`, `zustand`, `clsx`

**Verification:** `cd frontend && npx vite build` — ✅ Build clean

---

## 🔷 Phase 9 — Docker Containerization

| Component | File | Status |
|-----------|------|--------|
| Backend Dockerfile | `backend/Dockerfile` | ✅ |
| Frontend Dockerfile (multi-stage) | `frontend/Dockerfile` | ✅ |
| Docker Compose | `docker-compose.yml` | ✅ |
| Root .dockerignore | `.dockerignore` | ✅ |
| Frontend .dockerignore | `frontend/.dockerignore` | ✅ |
| psutil added to requirements | `requirements.txt` | ✅ |

**Verification:** `docker compose config --quiet` — ✅ Valid | `docker compose up --build` — ✅ Running

---

## 🔷 Phase 10 — Dynamic Port Resolution & Deployment Scripts

### Dynamic Port Allocation

| Component | File | Change | Status |
|-----------|------|--------|--------|
| TCP Server (OS-assigned) | `backend/network/connection.py` | `port=0` → `getsockname()` extracts actual port | ✅ |
| Node State (tcp_port) | `backend/node/state.py` | Added `tcp_port: int = 0` attribute | ✅ |
| UDP Discovery (dynamic HELLO) | `backend/network/discovery.py` | HELLO reads `state.tcp_port`, SO_REUSEADDR before bind | ✅ |
| Node Orchestrator | `backend/node/node.py` | Removed hardcoded `tcp_port` arg from `start_discovery()` | ✅ |
| API Port Fallback | `backend/main.py` | Loop tries ports 8000→8010, catches `OSError` | ✅ |

**Verification:** All 12 test suites pass ✅

---

## 🔷 Phase 11 — LAN Accessibility & Network Debugging

| Bug | Component | Fix Applied | Status |
|-----|-----------|-------------|--------|
| Cannot connect from other laptop | `frontend/src/api/client.js` | Dynamic `API_BASE` using `window.location.hostname` | ✅ |
| Vite dev server blocking LAN | `start.sh` & `start.bat` | Added `--host` flag to `npm run dev` | ✅ |
| Root permissions blocking upload | `.storage/` directory | Fixed Docker-created root ownership (`chown`) | ✅ |
| Downloads fail silently (Frontend) | `frontend/src/api/client.js` | Delayed `URL.revokeObjectURL` by 100ms | ✅ |
| Missing filename on download | `backend/main.py` | Added `expose_headers=["*"]` to `CORSMiddleware` | ✅ |
| Uvicorn crash on Windows (UnicodeEncodeError) | `backend/utils/logger.py` | Replaced unicode box-drawing characters with ASCII equivalents | ✅ |

**Verification:** Confirmed cross-LAN upload and download from friend's machine. ✅

---

## 🔷 Phase 12 — Cross-Node Downloads & Platform Independence

### 12a. Cross-Node Download (Core Feature)

| Change | Component | What it does | Status |
|--------|-----------|-------------|--------|
| Peer API port discovery | `backend/network/discovery.py` | HELLO broadcasts now include `api_port` | ✅ |
| Peer API port storage | `backend/node/state.py` | `PeerInfo.api_port` field + status response | ✅ |
| Remote manifest fetch | `backend/api/routes.py` `/download` | If manifest not local, queries peers via HTTP | ✅ |
| Remote chunk fetch | `backend/api/routes.py` `/download` | If chunk not local, fetches from peers + caches | ✅ |
| Peer file listing | `backend/api/routes.py` `/files` | Shows files from peers (with `local_only` recursion guard) | ✅ |
| `os.statvfs` → `shutil.disk_usage` | `backend/storage/local_store.py` | Cross-platform free space check | ✅ |
| TCP LimitOverrunError | `backend/network/connection.py` | 8MB `STREAM_LIMIT` + catch `LimitOverrunError` | ✅ |

### 12b. TCP Peer Registration (Windows Firewall Fix)

| Bug | Root Cause | Fix | Status |
|-----|-----------|-----|--------|
| Linux dashboard shows 0 peers | Windows Firewall blocks UDP port 50000, so HELLO broadcasts never arrive | Register peers from TCP handshakes (`_handle_client` + `connect_to_peer`) | ✅ |
| Peer data missing api_port/tcp_port | TCP HANDSHAKE only sent `node_id` + `name` | Extended HANDSHAKE and HANDSHAKE_ACK to include `tcp_port` + `api_port` | ✅ |

**Verification:** ✅ Upload on Node A (Linux), download on Node B (Windows) via file hash

---

## 🔷 Phase 13 — Advanced Throughput & Reliability

### 13a. Dynamic Chunk Sizing

| File Size | Chunk Size | Rationale | Status |
|-----------|-----------|-----------|--------|
| < 50 MB | 256 KB | Fine-grained, fast for small files | ✅ |
| 50–500 MB | 1 MB | Balanced throughput / chunk count | ✅ |
| > 500 MB | 4 MB | Minimizes chunk overhead on large files | ✅ |

### 13b. Multithreaded Disk I/O

| Operation | Before | After | Status |
|-----------|--------|-------|--------|
| File read (chunking) | Blocking `open().read()` | `asyncio.to_thread()` wrapper | ✅ |
| File hash (SHA-256) | Blocking `hashlib` loop | `_async_streaming_file_hash()` | ✅ |
| Chunk write to disk | Blocking `f.write()` | `asyncio.to_thread(f.write, data)` | ✅ |
| Merge-to-disk writes | Blocking per-chunk write | `asyncio.to_thread()` in pipeline | ✅ |

### 13c. Sliding Window & Selective Retransmission

| Component | Value | Description | Status |
|-----------|-------|-------------|--------|
| `MAX_WINDOW_SIZE` | 20 | Max concurrent in-flight chunks | ✅ |
| `TIMEOUT_SECONDS` | 3.0 | Retransmit threshold per chunk | ✅ |
| `SWEEP_INTERVAL` | 2.0 | Background sweep frequency | ✅ |
| `MAX_RETRIES` | 5 | Max retransmission attempts | ✅ |
| `CHUNK_ACK` protocol | — | Per-chunk acknowledgment message | ✅ |

**Verification:** All existing test suites pass (Phase 1–5, 2R, 3O) ✅

---

## 🟢 Phase 14 — Storage Quotas & LRU Eviction

| Component | File | Status |
|-----------|------|--------|
| `max_storage_mb` config (default 5 GB) | `config.yaml` + `backend/utils/config.py` | ✅ |
| `get_total_storage_size()` | `backend/storage/local_store.py` | ✅ |
| `evict_oldest_chunks(target_bytes_to_free)` | `backend/storage/local_store.py` | ✅ |
| Background Garbage Collector (60s loop) | `backend/advanced/garbage_collector.py` | ✅ |
| GC integration (node startup) | `backend/node/node.py` + `backend/main.py` | ✅ |
| `/status` exposes `storage_used_mb` / `storage_max_mb` | `backend/api/routes.py` | ✅ |

### LRU Eviction Logic
- Uses `os.path.getatime()` to sort `.bin` chunks by last access time
- Evicts oldest chunks one-by-one until target bytes freed
- GC fires when storage exceeds `max_storage_mb`, frees down to 90% capacity
- Runs via `asyncio.to_thread` to avoid blocking the event loop

**Verification:** `python -m tests.test_phase5` — Upload/download/status with GC active ✅

---

## 🟢 Phase 15 — Zero-Trust Swarm Authentication

| Component | File | Status |
|-----------|------|--------|
| `swarm_key` config (Pre-Shared Key) | `config.yaml` + `backend/utils/config.py` | ✅ |
| UDP HMAC-SHA256 signing (`_build_hello`) | `backend/network/discovery.py` | ✅ |
| UDP HMAC verification (`datagram_received`) | `backend/network/discovery.py` | ✅ |
| `AUTH` protocol message builder | `backend/network/protocol.py` | ✅ |
| TCP AUTH handshake (2s timeout) | `backend/network/connection.py` | ✅ |
| `/status` → `swarm_auth_active: true` | `backend/api/routes.py` | ✅ |
| Frontend "Swarm PSK: Active" badge | `frontend/src/pages/SettingsPage.jsx` | ✅ |

### Security Model
- **UDP**: Every HELLO packet is wrapped as `{"payload": {...}, "signature": "<hmac_hex>"}`. Mismatched signatures are silently dropped.
- **TCP**: Every new TCP connection must send an `AUTH` message within 2 seconds containing an HMAC-signed `node_id`. Invalid or missing AUTH → connection closed immediately.
- **No crash risk**: All auth failures are caught with `try/except` and logged at DEBUG level without disrupting the event loop.

**Verification:** `python -m tests.test_phase1` — Discovery + TCP handshake with HMAC auth ✅

---

## 🟢 Phase 16 — SQLite Persistence

| Component | File | Status |
|-----------|------|--------|
| `NodeDatabase` class (sqlite3 + WAL) | `backend/storage/db.py` | ✅ |
| `peers` table (node_id, ip, tcp_port, api_port, health_score, last_seen) | `backend/storage/db.py` | ✅ |
| `manifests` table (file_hash, filename, total_size, merkle_root, chunks_json) | `backend/storage/db.py` | ✅ |
| Async wrappers (`asyncio.to_thread`) | `backend/storage/db.py` | ✅ |
| Manifest persistence (save/load/list) | `backend/storage/local_store.py` | ✅ |
| Peer persistence (upsert on discovery) | `backend/node/state.py` | ✅ |
| Historical peer loading on boot | `backend/node/state.py` + `backend/main.py` | ✅ |
| `/files` reads from SQLite | `backend/api/routes.py` | ✅ |

### Benefits
- **Instant boot**: Historical peers loaded from SQLite on startup — no cold discovery delay
- **Crash recovery**: Manifests persist across restarts — no re-upload required
- **No flat files**: Eliminated `manifest_*.json` files, single `distristore.db` file
- **WAL journal mode**: Concurrent reads + non-blocking writes via `asyncio.to_thread`

**Verification:** `python -m tests.test_phase2` + `python -m tests.test_phase5` — Manifest CRUD via SQLite ✅

---

## 🟢 Phase 17 — Cross-Platform Binary Protocol

| Component | File | Status |
|-----------|------|--------|
| `msgpack>=1.0.8` dependency | `requirements.txt` | ✅ |
| `orjson>=3.9.0` dependency | `requirements.txt` | ✅ |
| TCP: msgpack serialization (length-prefixed) | `backend/network/connection.py` | ✅ |
| TCP: Raw bytes chunk transfer (no base64) | `backend/network/protocol.py` | ✅ |
| UDP: orjson fast JSON serialization | `backend/network/discovery.py` | ✅ |
| Windows `ProactorEventLoopPolicy` | `backend/main.py` | ✅ |
| Base64 removed from replication | `backend/strategies/replication.py` | ✅ |
| Base64 removed from sliding window | `backend/strategies/sliding_window.py` | ✅ |
| Base64 removed from self-healing | `backend/advanced/self_healing.py` | ✅ |

### Protocol Changes
- **TCP framing**: Switched from newline-delimited JSON to **4-byte length-prefixed msgpack**. This is critical because msgpack binary output can contain `0x0A` bytes.
- **Base64 eliminated**: Chunk data now sent as raw `bytes` via msgpack's native binary support — **~33% bandwidth savings** on chunk transfers.
- **UDP speed**: `orjson` is 3-10x faster than stdlib `json` for HELLO packet serialization.
- **Windows**: IOCP event loop via `WindowsProactorEventLoopPolicy` for native async speed.

**Verification:** `python -m tests.test_phase1` + `python -m tests.test_phase4` + `python -m tests.test_phase5` — All green ✅

---

## 🟢 Phase 18 — ZSTD Stream Compression

| Component | File | Status |
|-----------|------|--------|
| `zstandard>=0.22.0` dependency | `requirements.txt` | ✅ |
| Compress → encrypt in workers | `backend/file_engine/crypto.py` | ✅ |
| Decrypt → decompress in workers | `backend/file_engine/crypto.py` | ✅ |
| Compress in `chunk_file()` | `backend/file_engine/chunker.py` | ✅ |
| Decompress in `merge_chunks()` | `backend/file_engine/chunker.py` | ✅ |
| Decompress in `merge_chunks_to_disk()` | `backend/file_engine/chunker.py` | ✅ |
| Compress in `pipeline_chunk_and_store()` | `backend/file_engine/pipeline.py` | ✅ |
| Decompress in `pipeline_merge_to_disk()` | `backend/file_engine/pipeline.py` | ✅ |
| Manifest `"compression": "zstd"` field | `backend/file_engine/chunker.py` | ✅ |
| SQLite `compression` column + migration | `backend/storage/db.py` | ✅ |
| Upload API compression telemetry | `backend/api/routes.py` | ✅ |
| Backward compat (no-compress workers) | `backend/file_engine/crypto.py` | ✅ |

### Architecture
- **Upload flow**: Read chunk → **zstd.compress(level=3)** → AES-256-GCM encrypt → store
- **Download flow**: Load chunk → AES-256-GCM decrypt → **zstd.decompress()** → write
- **O(1) memory**: Each chunk compressed/decompressed individually — no full-file buffering
- **GIL bypass**: Compression runs inside `ProcessPoolExecutor` workers alongside crypto
- **Backward compat**: Manifests without `compression: "zstd"` skip decompression (pre-Phase-18 files)
- **SQLite**: `compression` column added with `ALTER TABLE` migration for existing databases

### Upload API Response (new fields)
```json
{
  "compressed_size": 45231,
  "compression_ratio": 2.26,
  "compression": "zstd"
}
```

**Verification:** `python -m tests.test_phase2` + `python -m tests.test_phase5` + `python -m tests.test_phase2_gcm` — All green ✅

---

## 📁 Project Structure

```
distristore/
├── backend/
│   ├── main.py                      # FastAPI entry point + Windows IOCP tuning
│   ├── api/routes.py                # REST endpoints + /manifest + /chunk
│   ├── node/
│   │   ├── node.py                  # Node orchestrator
│   │   └── state.py                 # Thread-safe state + SQLite peer persistence
│   ├── dht/
│   │   ├── routing.py               # XOR distance + routing table
│   │   └── lookup.py                # Peer search
│   ├── network/
│   │   ├── discovery.py             # UDP broadcast + HMAC auth + orjson
│   │   ├── protocol.py              # msgpack binary message schemas
│   │   └── connection.py            # Length-prefixed msgpack TCP framing
│   ├── file_engine/
│   │   ├── crypto.py                # AES-256-GCM + zstd + ProcessPool
│   │   ├── chunker.py               # Dynamic chunking + zstd + O(N) merger
│   │   └── pipeline.py              # Streaming chunk pipeline + zstd
│   ├── framework/client.py          # Python SDK + swarmed downloads
│   ├── strategies/
│   │   ├── selector.py              # Heuristic peer scoring
│   │   ├── replication.py           # k-copy replication (raw bytes)
│   │   └── sliding_window.py        # Sliding window + selective retransmit
│   ├── advanced/
│   │   ├── heartbeat.py             # Peer liveness monitor
│   │   ├── self_healing.py          # Auto re-replication
│   │   └── garbage_collector.py     # LRU eviction + storage quota
│   ├── storage/
│   │   ├── local_store.py           # Chunk disk I/O + SQLite manifest wrapper
│   │   └── db.py                    # NodeDatabase (SQLite + WAL + async)
│   └── benchmark/benchmark.py       # Performance testing
├── frontend/                        # Enterprise React + Vite dashboard
│   └── src/
│       ├── api/client.js            # Singleton Axios + service functions
│       ├── store/useNetworkStore.js  # Zustand auto-polling global state
│       ├── components/
│       │   ├── ui/                  # Card, Button, CopyButton, StatCard
│       │   ├── layout/              # Header, Sidebar
│       │   └── network/             # NetworkTopology, TransferSpeedChart, PeerTable
│       ├── pages/                   # Dashboard, Upload, Download, Settings
│       ├── App.jsx                  # BrowserRouter + layout shell
│       └── index.css                # Design system tokens
├── tests/
│   ├── test_phase1.py               # Node discovery + TCP + HMAC auth
│   ├── test_phase2.py               # File chunking + encryption + SQLite
│   ├── test_phase2_gcm.py           # AES-256-GCM tamper detection
│   ├── test_phase2_merkle.py        # Merkle root + proofs
│   ├── test_phase2_swarm.py         # Parallel chunk downloads
│   ├── test_phase2_health.py        # Health-scored discovery
│   ├── test_phase3.py               # DHT routing
│   ├── test_phase4.py               # Replication (msgpack binary)
│   ├── test_phase5.py               # HTTP API endpoints
│   ├── test_phase3_perf.py          # 100MB O(N) performance
│   ├── test_phase10_dynamic_ports.py
│   ├── test_phase12_cross_node.py
│   └── test_phase13_throughput.py
├── .github/workflows/ci.yml         # GitHub Actions CI pipeline
├── config.yaml                      # Node configuration
├── setup.sh / setup.bat             # One-command environment setup
├── start.sh / start.bat             # One-command launch scripts
├── ARCHITECTURE.md                  # System design + diagrams
├── BENCHMARKS.md                    # Performance data
├── CHANGELOG.md                     # Release history
├── README.md                        # Project documentation
└── PROGRESS.md                      # ← This file
```

---

## 🧪 Run All Tests

```bash
cd distristore
source .venv/bin/activate

# Foundation tests
python -m tests.test_phase1
python -m tests.test_phase2
python -m tests.test_phase3
python -m tests.test_phase4
python -m tests.test_phase5

# Research upgrade tests
python -m tests.test_phase2_gcm
python -m tests.test_phase2_merkle
python -m tests.test_phase2_swarm
python -m tests.test_phase2_health

# Performance test
python -m tests.test_phase3_perf

# Advanced features & Edge Cases
python -m tests.test_phase10_dynamic_ports
python -m tests.test_phase12_cross_node
python -m tests.test_phase13_throughput

# Benchmark
python -m backend.benchmark.benchmark

# Frontend
cd frontend && npx vite build
```

---

## 🚀 Run the Project

### Native (Recommended)
```bash
cd distristore
./setup.sh       # First time only
./start.sh       # Backend + Frontend
```

### Manual
```bash
# Backend (Terminal 1)
cd distristore && source .venv/bin/activate
python -m backend.main

# Frontend (Terminal 2)
cd distristore/frontend
npm run dev
```

### Docker
```bash
cd distristore
docker compose up --build
# Dashboard: http://localhost:3000
# API: http://localhost:8001
```
