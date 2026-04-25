# DistriStore Frontend

> Enterprise-grade React dashboard for the DistriStore P2P DHT storage framework.

## Tech Stack

| Library | Purpose |
|---------|---------|
| React 19 | UI framework |
| Vite 8 | Build tooling + HMR |
| React Router | URL-based page routing |
| Zustand | Global state management (auto-polling) |
| Recharts | Real-time transfer speed charts |
| lucide-react | Consistent SVG icon library |
| Axios | HTTP client (singleton instance) |
| clsx | Dynamic CSS class composition |

## Architecture

```
src/
├── api/
│   └── client.js           # Centralized Axios instance + service functions
├── store/
│   └── useNetworkStore.js  # Zustand store — auto-polls /status every 3s
├── components/
│   ├── ui/                 # Atomic: Card, Button, CopyButton, StatCard
│   ├── layout/             # Header, Sidebar
│   └── network/            # NetworkTopology, TransferSpeedChart, PeerTable
├── pages/
│   ├── DashboardPage.jsx   # Stats, topology, charts, file list
│   ├── UploadPage.jsx      # Drag & drop + AES-256-GCM encryption
│   ├── DownloadPage.jsx    # Hash input + decryption download
│   └── SettingsPage.jsx    # Node info, security, performance specs
├── App.jsx                 # BrowserRouter + layout shell (no business logic)
└── index.css               # Design system: dark mode, glassmorphism, animations
```

## Design Rules

1. **Components never call Axios directly** — import from `api/client.js`
2. **No prop drilling** — Zustand store provides global state
3. **Atomic UI** — all pages use Card, Button, StatCard components
4. **URL routing** — `/upload`, `/download?hash=abc`, `/settings`

## Quick Start

```bash
npm install
npm run dev      # http://localhost:5173
```

## Environment

| Variable | Default | Description |
|----------|---------|-------------|
| `VITE_API_URL` | `http://localhost:8001` | Backend API base URL |

## Build

```bash
npm run build    # Output: dist/
```
