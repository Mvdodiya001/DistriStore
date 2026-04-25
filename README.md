# DistriStore 🔗

> **LAN-Optimized P2P Distributed Hash Table (DHT) Storage Framework**

A modular, trackerless peer-to-peer file storage system that uses XOR-distance DHT routing, AES-256 encryption, dynamic peer scoring, and automatic self-healing replication.

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+ (for frontend)

### Backend Setup
```bash
cd distristore
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Start a node
python -m backend.main
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### Running Multiple Nodes (for testing)
```bash
# Terminal 1 - Node Alpha
DS_NAME=node-alpha DS_TCP_PORT=50001 DS_UDP_PORT=50000 \
  uvicorn backend.main:app --port 8000

# Terminal 2 - Node Beta
DS_NAME=node-beta DS_TCP_PORT=50003 DS_UDP_PORT=50000 \
  uvicorn backend.main:app --port 8001
```

---

## 📦 Architecture

```
distristore/
├── backend/
│   ├── main.py                 # FastAPI Entry point
│   ├── api/routes.py           # REST API endpoints
│   ├── node/
│   │   ├── node.py             # Node orchestrator
│   │   └── state.py            # Thread-safe state (asyncio locks)
│   ├── dht/
│   │   ├── routing.py          # XOR distance & routing table
│   │   └── lookup.py           # Peer search logic
│   ├── network/
│   │   ├── discovery.py        # UDP broadcast LAN discovery
│   │   ├── protocol.py         # JSON message schemas
│   │   └── connection.py       # Async TCP connection manager
│   ├── file_engine/
│   │   ├── chunker.py          # File splitting & merging
│   │   └── crypto.py           # PBKDF2 + AES-256 encryption
│   ├── framework/client.py     # Python SDK
│   ├── strategies/
│   │   ├── selector.py         # Heuristic peer scoring
│   │   └── replication.py      # k-copy replication logic
│   ├── advanced/
│   │   ├── heartbeat.py        # Peer liveness monitoring
│   │   └── self_healing.py     # Auto chunk re-replication
│   ├── storage/local_store.py  # Disk I/O for chunks
│   └── benchmark/benchmark.py  # Performance testing
├── frontend/                   # React + Vite dashboard
├── config.yaml                 # Node configuration
└── tests/                      # Phase verification tests
```

---

## 🔑 Key Features

| Feature | Description |
|---------|-------------|
| **LAN Discovery** | UDP broadcast auto-finds peers on your network |
| **XOR DHT** | Simplified Kademlia-style routing for chunk placement |
| **AES-256 Encryption** | Password-derived key encryption per chunk |
| **Heuristic Scoring** | `score = free_space + uptime - latency` for smart peer selection |
| **k-Replication** | Configurable redundancy (default k=3) |
| **Self-Healing** | Automatic re-replication when peers go offline |
| **REST API** | Upload, download, status via HTTP |
| **Python SDK** | `client.upload("file.txt", password="...")` |
| **React Dashboard** | Real-time monitoring with glassmorphism UI |

---

## 🧪 Running Tests

```bash
# Phase 1: Node discovery & TCP connections
python -m tests.test_phase1

# Phase 2: File chunking, encryption, integrity
python -m tests.test_phase2

# Phase 3: XOR routing & protocol messages
python -m tests.test_phase3

# Phase 4: Multi-node chunk replication
python -m tests.test_phase4

# Phase 5: API endpoints (upload/download via HTTP)
python -m tests.test_phase5

# Benchmark (10 files, 64KB–10MB)
python -m backend.benchmark.benchmark
```

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/status` | Node status, peers, uptime |
| `POST` | `/upload` | Upload + chunk + encrypt a file |
| `GET` | `/download/{hash}` | Download + decrypt + merge a file |
| `GET` | `/files` | List all stored file manifests |

---

## ⚙️ Configuration (`config.yaml`)

```yaml
node:
  node_id: "auto"           # Auto-generates 40-char hex ID
  name: "node-alpha"

network:
  discovery_port: 50000      # UDP broadcast port
  tcp_port: 50001            # TCP data transfer port
  discovery_interval: 5      # Broadcast every 5 seconds
  peer_timeout: 15           # Drop peer after 15s silence

storage:
  chunk_dir: ".storage"
  chunk_size: 262144         # 256 KB per chunk

replication:
  factor: 3                  # k=3 copies

api:
  host: "0.0.0.0"
  port: 8000
```

---

## 📊 Benchmark Results (Sample)

| Size | Chunks | Encrypt | Store | Load | Decrypt | Total |
|------|--------|---------|-------|------|---------|-------|
| 64 KB | 1 | 1.2ms | 0.3ms | 0.2ms | 1.1ms | 2.8ms |
| 1 MB | 4 | 17ms | 0.9ms | 0.7ms | 16ms | 35ms |
| 10 MB | 40 | 170ms | 4.5ms | 4.7ms | 165ms | 344ms |

---

## License

MIT
