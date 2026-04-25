# DistriStore 🔗

> **LAN-Optimized P2P Distributed Hash Table (DHT) Storage Framework**

A modular, trackerless peer-to-peer file storage system featuring AES-256-GCM authenticated encryption, Merkle-verified content addressing, parallel swarmed downloads, O(N) streaming architecture, dynamic port allocation, a real-time React dashboard, native deployment scripts, and Docker containerization.

---

## ✨ Highlights

- 🔐 **AES-256-GCM** — Authenticated encryption with automatic tamper detection
- 🌳 **Merkle Manifests** — Content-addressed chunks with per-chunk proof verification
- ⚡ **100MB in 0.67s** — O(N) streaming pipeline with ProcessPool parallelism
- 🕸️ **Parallel Swarming** — Download chunks from multiple peers simultaneously
- 🏥 **Health-Scored Discovery** — Peers broadcast RAM, CPU, disk metrics in HELLO
- 🔌 **Dynamic Ports** — OS-assigned TCP, auto-fallback API (8000→8010), SO_REUSEADDR UDP
- 🎨 **Enterprise Dashboard** — Sidebar nav, Recharts graphs, Zustand state, sortable peer table
- 🐳 **Docker-Ready** — Multi-stage builds, compose orchestration, nginx production serving

---

## 🚀 Quick Start

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
# Terminal 1 — Node Alpha (ports auto-assigned)
DS_NAME=node-alpha uvicorn backend.main:app --port 8000

# Terminal 2 — Node Beta (ports auto-assigned)
DS_NAME=node-beta uvicorn backend.main:app --port 8001
```

> TCP P2P ports are dynamically assigned by the OS. UDP discovery uses `SO_REUSEADDR` so multiple nodes share port 50000.

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
| **O(N) Pipeline** | Streaming Read→Encrypt→Store with `ProcessPoolExecutor` parallelism |
| **O(1) Downloads** | `FileResponse` streaming — temp file served directly, zero RAM |
| **Dynamic Ports** | TCP port=0 (OS-assigned), API fallback 8000→8010, SO_REUSEADDR UDP |
| **Parallel Swarming** | `asyncio.gather()` downloads 5 chunks simultaneously from peers |
| **Health-Scored Discovery** | UDP HELLO includes `psutil` metrics (RAM, CPU, disk) |
| **XOR DHT Routing** | Kademlia-style routing for chunk placement |
| **k-Replication** | Configurable redundancy (default k=3) |
| **Self-Healing** | Automatic re-replication when peers go offline |
| **Enterprise Frontend** | Sidebar nav, URL routing, Zustand state, Recharts, lucide-react |
| **Copy Hash UX** | One-click copy hash + quick download from file list |
| **Docker Compose** | Multi-stage builds, health checks, nginx production serving |
| **Native Scripts** | `setup.sh/bat` + `start.sh/bat` for zero-Docker deployment |

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/status` | Node status, peers, uptime, storage |
| `POST` | `/upload` | Upload + chunk + encrypt + Merkle manifest |
| `GET` | `/download/{hash}` | Download + decrypt + merge + integrity check |
| `GET` | `/files` | List all stored files with Merkle roots |
| `GET` | `/manifest/{hash}` | Fetch file manifest (for swarmed downloads) |
| `GET` | `/chunk/{hash}` | Fetch raw chunk bytes by hash |

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

### Docker vs Local

| Metric | Local | Docker | Overhead |
|--------|-------|--------|----------|
| 1MB Upload | ~45ms | 54ms | +20% |
| 1MB Download | ~30ms | 35ms | +17% |
| Frontend load | — | 2ms | nginx |

> Full benchmark data: [BENCHMARKS.md](BENCHMARKS.md)

---

## ⚙️ Configuration (`config.yaml`)

```yaml
node:
  node_id: "auto"
  name: "node-alpha"

network:
  discovery_port: 50000
  tcp_port: 50001
  discovery_interval: 5
  peer_timeout: 15

storage:
  chunk_dir: ".storage"
  chunk_size: 262144         # 256 KB

replication:
  factor: 3

api:
  host: "0.0.0.0"
  port: 8000
```

---

## 🔧 Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11, FastAPI, asyncio, uvicorn |
| Crypto | PyCryptodome (AES-256-GCM), PBKDF2-HMAC-SHA256 |
| Parallelism | `ProcessPoolExecutor` (GIL bypass), `asyncio.gather` |
| Discovery | UDP broadcast, `psutil` health metrics |
| Frontend | React 19, Vite 8, React Router, Zustand, Recharts, lucide-react |
| Storage | Local filesystem, JSON manifests, `FileResponse` streaming |
| DevOps | Docker, Docker Compose, nginx, multi-stage builds |

---

## 📄 Documentation

| Document | Description |
|----------|-------------|
| [PROGRESS.md](PROGRESS.md) | Phase-by-phase implementation tracker |
| [BENCHMARKS.md](BENCHMARKS.md) | All performance data and test results |

---

## 🐳 Docker

### Quick Start
```bash
docker compose up --build
```

| Service | URL | Port Mapping |
|---------|-----|--------------|
| **Dashboard** | http://localhost:3000 | 3000 → nginx:80 |
| **API** | http://localhost:8001 | 8001 → uvicorn:8001 |
| **TCP P2P** | — | 50001 → 50001 |
| **UDP Discovery** | — | 50000/udp → 50000/udp |

### Docker Files

| File | Purpose |
|------|---------|
| `backend/Dockerfile` | Python 3.11-slim + FastAPI + Uvicorn |
| `frontend/Dockerfile` | Multi-stage: Node 22 build → nginx:alpine |
| `docker-compose.yml` | Orchestrates both services with health checks |
| `.dockerignore` | Excludes venv, storage, logs from build context |

### Commands
```bash
# Build and start
docker compose up --build

# Run in background
docker compose up -d

# View logs
docker compose logs -f

# Stop
docker compose down

# Rebuild single service
docker compose up --build distristore-backend
```

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
