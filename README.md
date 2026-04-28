# DistriStore 🔗

> **LAN-Optimized P2P Distributed Hash Table (DHT) Storage Framework**

A modular, trackerless peer-to-peer file storage system featuring AES-256-GCM authenticated encryption, Merkle-verified content addressing, **cross-node downloads**, parallel swarmed downloads, O(N) streaming architecture, dynamic port allocation, a real-time React dashboard, and native deployment scripts for **Windows + Linux**.

---

## ✨ Highlights

- 🔐 **AES-256-GCM** — Authenticated encryption with automatic tamper detection
- 🌳 **Merkle Manifests** — Content-addressed chunks with per-chunk proof verification
- ⚡ **100MB in 0.67s** — O(N) streaming pipeline with ProcessPool parallelism
- 🕸️ **Parallel Swarming** — Download chunks from multiple peers simultaneously
- 📥 **Cross-Node Downloads** — Upload on one node, download on any peer via hash
- 🏥 **Health-Scored Discovery** — UDP HELLO + TCP handshake fallback (works through firewalls)
- 🔌 **Dynamic Ports** — OS-assigned TCP, auto-fallback API (8888→8898), SO_REUSEADDR UDP
- 🎨 **Enterprise Dashboard** — Sidebar nav, Recharts graphs, Zustand state, sortable peer table
- 🖥️ **Cross-Platform** — Fully tested on Windows + Linux with platform-independent code

---

## 🚀 Quick Start

> **Note:** Docker is **not supported for now**. Please use the native setup scripts or manual local setup.

### Prerequisites
- Python 3.11+
- Node.js 22+ (for frontend / Vite 8)

### One-Command Setup (Linux/macOS)
```bash
cd distristore
./setup.sh          # Creates .venv + installs Python & Node deps
./start.sh          # Starts backend + frontend
```

### One-Command Setup (Windows)
```cmd
cd distristore
setup.bat           REM Creates .venv + installs Python & Node deps
start.bat           REM Starts backend + frontend
```

### Manual Setup
```bash
cd distristore
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Start backend
python -m backend.main

# In another terminal — start frontend
cd frontend && npm install && npm run dev
```

### Running Multiple Nodes (for testing)
```bash
# Terminal 1 — Node Alpha
DS_NAME=node-alpha DS_API_PORT=8888 python -m backend.main

# Terminal 2 — Node Beta (different API port)
DS_NAME=node-beta DS_API_PORT=8889 DS_TCP_PORT=50002 python -m backend.main
```

> TCP P2P ports are dynamically assigned by the OS. UDP discovery uses `SO_REUSEADDR` so multiple nodes share port 50000.
> Cross-node downloads work automatically — upload on any node, download on any other using the file hash.

---

## 📦 Architecture

```
distristore/
├── backend/
│   ├── main.py                      # FastAPI entry point + CORS
│   ├── api/routes.py                # REST endpoints (FileResponse streaming)
│   ├── node/
│   │   ├── node.py                  # Node orchestrator
│   │   └── state.py                 # Thread-safe state (asyncio locks)
│   ├── dht/
│   │   ├── routing.py               # XOR distance + routing table
│   │   └── lookup.py                # Peer search / lookup
│   ├── network/
│   │   ├── discovery.py             # UDP broadcast + health scoring
│   │   ├── protocol.py              # JSON message schemas
│   │   └── connection.py            # Async TCP connection manager
│   ├── file_engine/
│   │   ├── crypto.py                # AES-256-GCM + ProcessPoolExecutor
│   │   ├── chunker.py               # O(1) generator chunking + O(N) merger
│   │   └── pipeline.py              # Streaming chunk pipeline
│   ├── framework/client.py          # Python SDK + async swarmed downloads
│   ├── strategies/
│   │   ├── selector.py              # Heuristic peer scoring
│   │   └── replication.py           # k-copy replication
│   ├── advanced/
│   │   ├── heartbeat.py             # Peer liveness monitoring
│   │   └── self_healing.py          # Auto chunk re-replication
│   ├── storage/local_store.py       # Disk I/O for chunks + manifests
│   └── benchmark/benchmark.py       # 10-size throughput suite
├── frontend/                        # Enterprise React + Vite dashboard
│   └── src/
│       ├── api/client.js            # Singleton Axios + service functions
│       ├── store/useNetworkStore.js  # Zustand auto-polling (3s) global state
│       ├── components/
│       │   ├── ui/                  # Card, Button, CopyButton, StatCard
│       │   ├── layout/              # Header, Sidebar
│       │   └── network/             # NetworkTopology, TransferSpeedChart, PeerTable
│       ├── pages/                   # DashboardPage, UploadPage, DownloadPage, SettingsPage
│       ├── App.jsx                  # BrowserRouter + layout shell only
│       └── index.css                # Design system + dark-mode tokens
├── tests/                           # Phase verification tests
├── config.yaml                      # Node configuration
├── PROGRESS.md                      # Full phase-by-phase tracker
├── BENCHMARKS.md                    # Comprehensive performance data
└── README.md                        # ← This file
```

---

## 🔑 Key Features

| Feature | Description |
|---------|-------------|
| **AES-256-GCM** | Authenticated encryption — tampered chunks auto-rejected |
| **Merkle Manifests** | Content-addressed files with SHA-256 tree root + per-chunk proofs |
| **Cross-Node Downloads** | Upload on Node A, download on Node B — manifest + chunks fetched via peer HTTP API and cached locally |
| **O(N) Pipeline** | Streaming Read→Encrypt→Store with `ProcessPoolExecutor` parallelism |
| **O(1) Downloads** | `FileResponse` streaming — temp file served directly, zero RAM |
| **Dynamic Ports** | TCP port=0 (OS-assigned), API fallback 8888→8898, SO_REUSEADDR UDP |
| **Parallel Swarming** | `asyncio.gather()` downloads 5 chunks simultaneously from peers |
| **Dual Discovery** | UDP HELLO broadcasts + TCP handshake peer registration (works through Windows Firewall) |
| **Health-Scored Peers** | `psutil` metrics (RAM, CPU, disk) in HELLO + `api_port` for cross-node HTTP |
| **XOR DHT Routing** | Kademlia-style routing for chunk placement |
| **k-Replication** | Configurable redundancy (default k=3) |
| **Self-Healing** | Automatic re-replication when peers go offline |
| **Enterprise Frontend** | Sidebar nav, URL routing, Zustand state, Recharts, lucide-react |
| **Copy Hash UX** | One-click copy hash + quick download from file list |
| **Cross-Platform** | Windows + Linux/macOS — all code uses platform-independent APIs |

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/status` | Node status, peers (with `api_port`), uptime, storage |
| `POST` | `/upload` | Upload + chunk + encrypt + Merkle manifest + replicate |
| `GET` | `/download/{hash}?password=` | Download + decrypt + merge — fetches from peers if not local |
| `GET` | `/files?local_only=false` | List files (local + peer merged, deduplicated) |
| `GET` | `/manifest/{hash}` | Fetch file manifest (used by cross-node download) |
| `GET` | `/chunk/{hash}` | Fetch raw chunk bytes (used by cross-node download) |

---

## 🧪 Running Tests

```bash
source .venv/bin/activate

# Foundation
python -m tests.test_phase1          # Node discovery + TCP
python -m tests.test_phase2          # File chunk + encrypt round-trip
python -m tests.test_phase3          # XOR routing + protocol
python -m tests.test_phase4          # Multi-node replication
python -m tests.test_phase5          # HTTP API endpoints

# Security & Integrity
python -m tests.test_phase2_gcm      # AES-256-GCM tamper detection
python -m tests.test_phase2_merkle   # Merkle root + proof verification

# Performance
python -m tests.test_phase2_swarm    # Parallel chunk downloads
python -m tests.test_phase2_health   # Health-scored discovery
python -m tests.test_phase3_perf     # 100MB O(N) performance test

# Benchmark Suite
python -m backend.benchmark.benchmark
```

---

## 📊 Benchmark Results

### Core Suite (AES-256-GCM + Merkle) — avg 95.2ms

| Size | Chunks | Encrypt | Decrypt | **Total** |
|------|--------|---------|---------|-----------|
| 64 KB | 1 | 46ms | 46ms | **94ms** |
| 1 MB | 4 | 32ms | 35ms | **68ms** |
| 10 MB | 40 | 71ms | 88ms | **174ms** |

### 100MB Performance

| Metric | Result |
|--------|--------|
| Chunk + Encrypt (400 chunks) | 0.38s |
| Merge + Decrypt (400 chunks) | 0.29s |
| **Total end-to-end** | **0.67s** |
| ProcessPool speedup | 8.52x |
| O(N) linearity (10→100MB) | 5.9x ratio ✅ |

### Runtime Note

Current benchmark figures are based on native local execution.

> Full benchmark data: [BENCHMARKS.md](BENCHMARKS.md)

---

## ⚙️ Configuration (`config.yaml`)

```yaml
node:
  node_id: "auto"
  name: "node-alpha"

network:
  discovery_port: 50000      # UDP broadcast port
  tcp_port: 50001            # TCP peer-to-peer port
  discovery_interval: 5      # HELLO broadcast interval (seconds)
  peer_timeout: 15           # Peer considered dead after (seconds)

storage:
  chunk_dir: ".storage"
  chunk_size: 262144         # 256 KB per chunk

replication:
  factor: 3                  # k-copy replication

api:
  host: "0.0.0.0"
  port: 8888                 # HTTP API port (auto-fallback to 8898)
```

> **Environment overrides:** `DS_NAME`, `DS_API_PORT`, `DS_TCP_PORT`, `DS_UDP_PORT`

---

## 🔧 Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11, FastAPI, asyncio, uvicorn |
| Crypto | PyCryptodome (AES-256-GCM), PBKDF2-HMAC-SHA256 |
| Parallelism | `ProcessPoolExecutor` (GIL bypass), `asyncio.gather` |
| Discovery | UDP broadcast + TCP handshake fallback, `psutil` health metrics |
| Cross-Node | `httpx` async client for peer manifest/chunk fetching |
| Frontend | React 19, Vite 8, React Router, Zustand, Recharts, lucide-react |
| Storage | Local filesystem, JSON manifests, `FileResponse` streaming |
| Platforms | Windows + Linux/macOS (cross-platform APIs throughout) |
| DevOps | Native setup/start scripts (`setup.sh/.bat`, `start.sh/.bat`) |

---

## 📄 Documentation

| Document | Description |
|----------|-------------|
| [PROGRESS.md](PROGRESS.md) | Phase-by-phase implementation tracker |
| [BENCHMARKS.md](BENCHMARKS.md) | All performance data and test results |

---

## 🐳 Docker Status

Docker artifacts may still exist in the repository, but they are currently not part of the supported workflow.
Use native local execution for development and testing.

### Why Docker support is removed for now

1. The active development and test workflow is built around native local execution (`setup.sh/.bat`, `start.sh/.bat`).
2. Current code paths and runtime behavior are validated in local runs, not maintained in Docker-first flows.
3. Keeping Docker instructions while they are not actively used creates confusion and outdated setup expectations.

---

## 📜 Deployment Scripts

| Script | Platform | Purpose |
|--------|----------|---------|
| `setup.sh` | Linux/macOS | Creates `.venv`, installs Python + Node deps |
| `setup.bat` | Windows | Creates `.venv`, installs Python + Node deps |
| `start.sh` | Linux/macOS | Starts backend (background) + frontend |
| `start.bat` | Windows | Opens backend in new window + frontend |

---

## License

Apache 2.0
