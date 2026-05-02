# Changelog

All notable changes to this project will be documented in this file.

## [1.0.0] - Initial Release

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
