# Changelog

All notable changes to this project will be documented in this file.

## [2.1.0] - 2026-05-03

### Added — ZSTD Stream Compression (Phase 18)
- Per-chunk Zstandard compression (`zstandard>=0.22.0`) at level 3 for optimal speed/ratio balance.
- Compression runs inside `ProcessPoolExecutor` workers alongside AES-256-GCM crypto — fully bypasses the GIL.
- Upload flow: **Read → Compress → Encrypt → Store** (O(1) memory per chunk).
- Download flow: **Load → Decrypt → Decompress → Write** (O(1) memory per chunk).
- Backward-compatible: manifests without `compression: "zstd"` skip decompression (pre-Phase-18 files).
- SQLite schema migration: `compression` column auto-added to `manifests` table via `ALTER TABLE`.
- Upload API now returns `compressed_size`, `compression_ratio`, and `compression` fields.

---

## [2.0.0] - 2026-05-03

### Added — Storage Quotas & LRU Eviction (Phase 14)
- Configurable `max_storage_mb` quota (default 5 GB) to prevent disk exhaustion.
- Background garbage collector (`backend/advanced/garbage_collector.py`) runs a 60-second async loop.
- LRU eviction via `os.path.getatime()` — oldest-accessed chunks freed first.
- `/status` now reports `storage_used_mb` and `storage_max_mb`.

### Added — Zero-Trust Swarm Authentication (Phase 15)
- HMAC-SHA256 Pre-Shared Key (`swarm_key`) for both UDP and TCP.
- UDP broadcasts wrapped as `{"payload": ..., "signature": "<hmac_hex>"}` — unsigned packets silently dropped.
- TCP connections require an `AUTH` message within 2 seconds — invalid/missing auth closes the socket immediately.
- `/status` exposes `swarm_auth_active: true`.
- Frontend Settings page shows "Swarm PSK: Active" security badge.

### Added — SQLite Persistence (Phase 16)
- `NodeDatabase` class (`backend/storage/db.py`) replaces flat JSON manifest files with a persistent SQLite database.
- Tables: `peers` (routing table) and `manifests` (file metadata + chunk lists).
- Historical peers loaded from SQLite on boot — instant startup, no cold discovery.
- All database writes use `asyncio.to_thread()` with WAL journal mode for non-blocking concurrent access.

### Changed — Cross-Platform Binary Protocol (Phase 17)
- **TCP pipeline**: Replaced JSON serialization with `msgpack` binary protocol using 4-byte length-prefixed framing.
- **Base64 eliminated**: Chunk data sent as raw `bytes` via msgpack — ~33% bandwidth savings.
- **UDP metadata**: Switched from stdlib `json` to `orjson` (3-10x faster serialization).
- **Windows tuning**: Added `WindowsProactorEventLoopPolicy` for native IOCP async performance.
- New dependencies: `msgpack>=1.0.8`, `orjson>=3.9.0`.

### Changed
- Storage quota increased from 1 GB to 5 GB default to support large file uploads.
- Test suite updated to use HMAC-signed discovery packets.

---

## [1.0.0] - 2026-05-02

### Features
- **Security**: AES-256-GCM authenticated encryption and Merkle Tree content addressing for tamper-proof chunking.
- **Dynamic Chunking**: Intelligently switches chunk sizes based on file size (256KB for <50MB, 1MB for 50-500MB, 4MB for >500MB).
- **P2P Discovery**: UDP HELLO broadcasts combined with OS-assigned dynamic TCP handshakes for robust peer discovery.
- **Enterprise UI**: React 19 + Vite dashboard featuring dynamic charts, topology visualizations, and Zustand state auto-polling.
- **Self-Healing**: Automated sliding window chunk replication (k=3) with configurable selective retransmission for dropped connections.

### Performance
- **Multithreaded Disk I/O**: Offloaded `asyncio.to_thread` reads/writes completely unblocking the event loop.
- **Parallel Cryptography**: Bypassed Python's GIL using `ProcessPoolExecutor` for blazing-fast chunk encryption.
- **O(1) Memory Streaming**: Linear throughput regardless of file size by directly streaming file chunks via `FileResponse`.

### Deployment
- **Cross-Platform Scripts**: Included native deploy wrappers (`setup.sh`/`start.sh` and `.bat` equivalents) for instant bootstrapping on Windows/Linux/macOS.
- **NAT Traversal Ready**: Tested compatibility with Tailscale/ZeroTier virtual networks for cross-internet mesh linking.
