<div align="center">

# DistriStore

### **A LAN-Optimized, Trackerless P2P Distributed Storage Framework**

*Encrypted. Content-addressed. Swarmed. Self-healing.*

<br/>

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Node](https://img.shields.io/badge/Node-22+-339933?style=flat-square&logo=node.js&logoColor=white)](https://nodejs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19-61DAFB?style=flat-square&logo=react&logoColor=black)](https://react.dev/)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-blue?style=flat-square)](#)
[![License](https://img.shields.io/badge/License-Apache%202.0-D22128?style=flat-square)](LICENSE)

<br/>

**Upload anywhere. Retrieve anywhere. No central server. No tracker. No trust assumptions.**

</div>

---

## Overview

**DistriStore** is a modular peer-to-peer storage framework engineered for high-throughput LAN deployments. It combines a Kademlia-inspired DHT, AES-256-GCM authenticated encryption, Merkle-verified content addressing, and parallel chunk swarming into a single coherent system — wrapped in an enterprise-grade React dashboard and a one-command deployment story for both **Windows** and **Linux/macOS**.

Files are split, encrypted, and replicated across the network. Any node can serve any file. Every chunk is cryptographically verifiable. The result is a storage fabric that survives node failures, scales horizontally, and never trusts the network it runs on.

<div align="center">
  <img src="docs/architecture_overview.png" alt="DistriStore Architecture Overview" width="85%"/>
</div>

---

## Table of Contents

- [Why DistriStore](#why-distristore)
- [Highlights](#highlights)
- [Quick Start](#quick-start)
- [Architecture](#architecture)
- [Feature Matrix](#feature-matrix)
- [REST API](#rest-api)
- [Performance](#performance)
- [Configuration](#configuration)
- [Testing](#testing)
- [Tech Stack](#tech-stack)
- [Documentation](#documentation)
- [License](#license)

---

## Why DistriStore

| | |
|---|---|
| **Trackerless by design** | UDP discovery + TCP handshake fallback. Nodes find each other without a coordinator — even through restrictive firewalls. |
| **Encryption you can trust** | AES-256-GCM authenticated encryption. Tampered chunks are mathematically impossible to accept silently. |
| **Verifiable at every level** | Merkle manifests with per-chunk SHA-256 proofs. Corruption is detected before data ever reaches the user. |
| **Built for throughput** | Streaming O(N) pipeline, `ProcessPoolExecutor` parallelism, and `asyncio.gather` swarmed downloads. 100 MB round-trips in **0.67 s**. |
| **Truly cross-node** | Upload on Node A, download from Node B by hash. The network resolves the rest. |
| **Production-grade UI** | A real React 19 + Vite dashboard — sidebar nav, live charts, sortable peer tables, dark-mode design tokens — not a debug page. |

---

## Highlights

<table>
<tr>
<td width="50%" valign="top">

### Security & Integrity
- **AES-256-GCM** authenticated encryption
- **PBKDF2-HMAC-SHA256** key derivation
- **Merkle tree** content addressing
- **Per-chunk proofs** for partial verification
- Automatic tamper rejection

</td>
<td width="50%" valign="top">

### Performance
- **0.67 s** end-to-end on 100 MB
- **8.52×** ProcessPool speedup
- **Dynamic chunk sizing**: 256KB / 1MB / 4MB auto-selected
- **O(1)** memory-stable downloads via `FileResponse`
- **Async disk I/O** via `asyncio.to_thread`
- Swarmed parallel chunk fetch

</td>
</tr>
<tr>
<td width="50%" valign="top">

### Networking
- UDP HELLO broadcasts + TCP handshake fallback
- `SO_REUSEADDR` shared discovery port
- OS-assigned dynamic TCP ports
- HTTP API auto-fallback (8888 → 8898)
- Health-scored peer ranking via `psutil`

</td>
<td width="50%" valign="top">

### Reliability
- **Sliding window** replication (window=20, selective retransmit)
- **k-copy replication** (default k=3)
- **Self-healing** chunk re-replication on failure
- **Heartbeat** liveness monitoring
- **XOR-distance** Kademlia routing
- Cross-node manifest + chunk fetch
- **1MB TCP buffers** for large chunk transfers

</td>
</tr>
</table>

---

## Quick Start

> **Prerequisites:** Python 3.11+ · Node.js 22+ (for the Vite frontend)
>
> **Note:** Docker is intentionally not part of the supported workflow — see [Deployment Notes](#deployment-notes).

### One-command setup

<table>
<tr>
<td valign="top">

**Linux / macOS**
```bash
cd distristore
./setup.sh    # venv + Python + Node deps
./start.sh    # backend + frontend
```

</td>
<td valign="top">

**Windows**
```cmd
cd distristore
setup.bat     :: venv + Python + Node deps
start.bat     :: backend + frontend
```

</td>
</tr>
</table>

### Manual setup

```bash
cd distristore
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Start the backend
python -m backend.main

# In another terminal — start the dashboard
cd frontend && npm install && npm run dev
```

### Multi-node testing

Spin up several peers on the same machine — each with its own identity and ports:

```bash
# Terminal 1 — Node Alpha
DS_NAME=node-alpha DS_API_PORT=8888 python -m backend.main

# Terminal 2 — Node Beta
DS_NAME=node-beta  DS_API_PORT=8889 DS_TCP_PORT=50002 python -m backend.main
```

> TCP P2P ports are OS-assigned. UDP discovery uses `SO_REUSEADDR` so multiple nodes share port `50000`.
> Cross-node downloads work transparently — upload on any node, retrieve on any other using the file hash.

---

## Architecture

<div align="center">
  <img src="docs/network_topology.png" alt="Network Topology" width="80%"/>
</div>

```
distristore/
├── backend/
│   ├── main.py                       FastAPI entry point + CORS
│   ├── api/routes.py                 REST endpoints (FileResponse streaming)
│   ├── node/
│   │   ├── node.py                   Node orchestrator
│   │   └── state.py                  Thread-safe state (asyncio locks)
│   ├── dht/
│   │   ├── routing.py                XOR distance + routing table
│   │   └── lookup.py                 Peer search / lookup
│   ├── network/
│   │   ├── discovery.py              UDP broadcast + health scoring
│   │   ├── protocol.py               JSON message schemas
│   │   └── connection.py             Async TCP connection manager
│   ├── file_engine/
│   │   ├── crypto.py                 AES-256-GCM + ProcessPoolExecutor
│   │   ├── chunker.py                O(1) generator chunking + O(N) merger
│   │   └── pipeline.py               Streaming chunk pipeline
│   ├── framework/client.py           Python SDK + async swarmed downloads
│   ├── strategies/
│   │   ├── selector.py               Heuristic peer scoring
│   │   └── replication.py            k-copy replication
│   ├── advanced/
│   │   ├── heartbeat.py              Peer liveness monitoring
│   │   └── self_healing.py           Auto chunk re-replication
│   ├── storage/local_store.py        Disk I/O for chunks + manifests
│   └── benchmark/benchmark.py        10-size throughput suite
├── frontend/                         Enterprise React + Vite dashboard
│   └── src/
│       ├── api/client.js             Singleton Axios + service functions
│       ├── store/useNetworkStore.js  Zustand auto-polling (3s) global state
│       ├── components/
│       │   ├── ui/                   Card, Button, CopyButton, StatCard
│       │   ├── layout/               Header, Sidebar
│       │   └── network/              NetworkTopology, TransferSpeedChart, PeerTable
│       ├── pages/                    Dashboard, Upload, Download, Settings
│       ├── App.jsx                   BrowserRouter + layout shell
│       └── index.css                 Design system + dark-mode tokens
├── docs/                             Architecture diagrams (PNG)
├── tests/                            Phase verification tests
├── config.yaml                       Node configuration
├── ARCHITECTURE.md                   System design + diagrams
├── BENCHMARKS.md                     Comprehensive performance data
└── PROGRESS.md                       Phase-by-phase tracker
```

---

## Feature Matrix

| Feature | Description |
|---|---|
| **AES-256-GCM** | Authenticated encryption — tampered chunks auto-rejected |
| **Merkle Manifests** | Content-addressed files with SHA-256 tree root + per-chunk proofs |
| **Cross-Node Downloads** | Upload on Node A, download on Node B — manifest + chunks fetched via peer HTTP API and cached locally |
| **O(N) Pipeline** | Streaming Read → Encrypt → Store with `ProcessPoolExecutor` parallelism |
| **O(1) Downloads** | `FileResponse` streaming — temp file served directly, zero RAM bloat |
| **Dynamic Ports** | TCP `port=0` (OS-assigned), API fallback `8888 → 8898`, `SO_REUSEADDR` UDP |
| **Parallel Swarming** | `asyncio.gather()` downloads chunks simultaneously from peers |
| **Dual Discovery** | UDP HELLO broadcasts + TCP handshake fallback (works through Windows Firewall) |
| **Health-Scored Peers** | `psutil` metrics (RAM, CPU, disk) in HELLO + `api_port` for cross-node HTTP |
| **XOR DHT Routing** | Kademlia-style routing for chunk placement |
| **k-Replication** | Configurable redundancy (default k=3) |
| **Self-Healing** | Automatic re-replication when peers go offline |
| **Enterprise Frontend** | Sidebar nav, URL routing, Zustand state, Recharts, lucide-react |
| **Copy-Hash UX** | One-click copy hash + quick download from file list |
| **Cross-Platform** | Windows + Linux/macOS — platform-independent APIs throughout |

---

## REST API

| Method | Endpoint | Description |
|---|---|---|
| `GET`  | `/status` | Node status, peers (with `api_port`), uptime, storage |
| `POST` | `/upload` | Upload + chunk + encrypt + Merkle manifest + replicate |
| `GET`  | `/download/{hash}?password=` | Download + decrypt + merge — fetches from peers if not local |
| `GET`  | `/files?local_only=false` | List files (local + peer merged, deduplicated) |
| `GET`  | `/manifest/{hash}` | Fetch file manifest (used by cross-node download) |
| `GET`  | `/chunk/{hash}` | Fetch raw chunk bytes (used by cross-node download) |

<div align="center">
  <img src="docs/sequence_upload.png" alt="Upload Sequence" width="48%"/>
  <img src="docs/sequence_download.png" alt="Download Sequence" width="48%"/>
</div>

---

## Performance

### Core Suite — AES-256-GCM + Merkle (avg **95.2 ms**)

| Size | Chunks | Encrypt | Decrypt | **Total** |
|---|---|---|---|---|
| 64 KB | 1   | 46 ms | 46 ms | **94 ms**  |
| 1 MB  | 4   | 32 ms | 35 ms | **68 ms**  |
| 10 MB | 40  | 71 ms | 88 ms | **174 ms** |

### 100 MB End-to-End

| Metric | Result |
|---|---|
| Chunk + Encrypt (400 chunks) | 0.38 s |
| Merge + Decrypt (400 chunks) | 0.29 s |
| **Total round-trip** | **0.67 s** |
| ProcessPool speedup | **8.52×** |
| O(N) linearity (10 → 100 MB) | 5.9× ratio ✅ |

> Figures reflect native local execution. Full data set: [BENCHMARKS.md](BENCHMARKS.md)

---

## Configuration

`config.yaml` — defaults that work out of the box, every value override-able by environment variable.

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

**Environment overrides:** `DS_NAME` · `DS_API_PORT` · `DS_TCP_PORT` · `DS_UDP_PORT`

---

## Testing

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
python -m tests.test_phase3_perf     # 100 MB O(N) performance test

# Full benchmark suite
python -m backend.benchmark.benchmark
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | Python 3.11 · FastAPI · asyncio · uvicorn |
| **Crypto** | PyCryptodome (AES-256-GCM) · PBKDF2-HMAC-SHA256 |
| **Parallelism** | `ProcessPoolExecutor` (GIL bypass) · `asyncio.gather` |
| **Discovery** | UDP broadcast + TCP handshake fallback · `psutil` health metrics |
| **Cross-Node** | `httpx` async client for peer manifest/chunk fetching |
| **Frontend** | React 19 · Vite 8 · React Router · Zustand · Recharts · lucide-react |
| **Storage** | Local filesystem · JSON manifests · `FileResponse` streaming |
| **Platforms** | Windows + Linux/macOS — cross-platform APIs throughout |
| **DevOps** | Native setup/start scripts (`setup.sh/.bat`, `start.sh/.bat`) |

---

## Documentation

| Document | Description |
|---|---|
| [ARCHITECTURE.md](ARCHITECTURE.md) | System design · class diagrams · sequence diagrams · ER diagrams |
| [BENCHMARKS.md](BENCHMARKS.md) | All performance data and test results |
| [PROGRESS.md](PROGRESS.md) | Phase-by-phase implementation tracker |

<div align="center">
  <img src="docs/class_diagram.png" alt="Class Diagram" width="48%"/>
  <img src="docs/er_diagram.png" alt="ER Diagram" width="48%"/>
</div>

---

## Deployment Notes

### Deployment scripts

| Script | Platform | Purpose |
|---|---|---|
| `setup.sh`  | Linux/macOS | Creates `.venv`, installs Python + Node deps |
| `setup.bat` | Windows     | Creates `.venv`, installs Python + Node deps |
| `start.sh`  | Linux/macOS | Starts backend (background) + frontend |
| `start.bat` | Windows     | Opens backend in new window + frontend |

### Why no Docker (for now)

Docker artifacts may still exist in the repository, but they are not part of the supported workflow. The active development and test loop is built around native execution (`setup.sh/.bat`, `start.sh/.bat`), and current code paths are validated there. Maintaining stale Docker instructions alongside an actively-evolving native flow created confusion, so it has been intentionally set aside until the containerized story is brought back to parity.

---

## License

Released under the **Apache License 2.0** — see [LICENSE](LICENSE) for the full text.

<div align="center">

<br/>

**Built for engineers who don't trust the network.**

<sub>If DistriStore helps you, a ⭐ on the repo goes a long way.</sub>

</div>
