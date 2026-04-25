"""
DistriStore — Phase 2.3 Verification: Parallel Swarming

Tests:
  1. Upload a file via API
  2. Fetch manifest via /manifest/{hash}
  3. Download individual chunks via /chunk/{hash}
  4. Parallel (swarmed) download all chunks using asyncio.gather
  5. Compare sequential vs parallel download speed

Run: python -m tests.test_phase2_swarm
"""

import asyncio
import os
import sys
import time
import subprocess
import shutil

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

API_PORT = 8766
TCP_PORT = 50089
UDP_PORT = 50088


async def run_parallel_test(file_hash: str, base_url: str):
    """Run the parallel chunk download test."""
    import httpx

    # Fetch manifest
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(f"{base_url}/manifest/{file_hash}")
        assert resp.status_code == 200, f"Manifest fetch failed: {resp.status_code}"
        manifest = resp.json()

    chunks_info = manifest["chunks"]
    total_chunks = len(chunks_info)
    print(f"  Manifest: {total_chunks} chunks, merkle_root={manifest.get('merkle_root', '')[:20]}...")

    # Sequential download
    print(f"\n  Sequential download ({total_chunks} chunks)...")
    t0 = time.perf_counter()
    seq_data = []
    async with httpx.AsyncClient(timeout=30) as client:
        for info in chunks_info:
            resp = await client.get(f"{base_url}/chunk/{info['chunk_hash']}")
            assert resp.status_code == 200
            seq_data.append(resp.content)
    seq_time = time.perf_counter() - t0
    seq_bytes = sum(len(d) for d in seq_data)
    print(f"  Sequential: {seq_bytes} bytes in {seq_time*1000:.1f}ms")

    # Parallel download (asyncio.gather with concurrency=5)
    print(f"\n  Parallel swarmed download (concurrency=5)...")
    t0 = time.perf_counter()
    par_data = [None] * total_chunks
    semaphore = asyncio.Semaphore(5)

    async def fetch(idx, chunk_hash):
        async with semaphore:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(f"{base_url}/chunk/{chunk_hash}")
                assert resp.status_code == 200
                par_data[idx] = resp.content

    await asyncio.gather(*[
        fetch(info["index"], info["chunk_hash"])
        for info in chunks_info
    ])
    par_time = time.perf_counter() - t0
    par_bytes = sum(len(d) for d in par_data if d)
    print(f"  Parallel:   {par_bytes} bytes in {par_time*1000:.1f}ms")

    # Verify data matches
    assert seq_bytes == par_bytes, "Byte count mismatch!"
    for i in range(total_chunks):
        assert seq_data[i] == par_data[i], f"Chunk {i} data mismatch!"

    speedup = seq_time / par_time if par_time > 0 else 0
    print(f"\n  Speedup: {speedup:.2f}x faster with swarming")
    return seq_time, par_time


def run_test():
    print("=" * 65)
    print("  DistriStore — Phase 2.3: Parallel Swarming Verification")
    print("=" * 65)

    venv_python = os.path.join(os.path.dirname(__file__), "..", ".venv", "bin", "python")
    project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    tmp_dir = os.path.join(project_dir, ".test_swarm")
    os.makedirs(tmp_dir, exist_ok=True)

    env = {
        **os.environ,
        "PYTHONPATH": project_dir,
        "DS_NAME": "swarm-node",
        "DS_TCP_PORT": str(TCP_PORT),
        "DS_UDP_PORT": str(UDP_PORT),
    }

    # Start server
    print(f"\n[1/4] Starting server on port {API_PORT}...")
    server = subprocess.Popen(
        [venv_python, "-m", "uvicorn", "backend.main:app",
         "--host", "127.0.0.1", "--port", str(API_PORT)],
        cwd=project_dir, env=env,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    time.sleep(4)
    if server.poll() is not None:
        _, stderr = server.communicate()
        print(f"  ❌ Server crashed:\n{stderr.decode()[-300:]}")
        sys.exit(1)
    print(f"  ✅ Server started (PID={server.pid})")

    try:
        import httpx
        base_url = f"http://127.0.0.1:{API_PORT}"

        # Upload a larger file (2MB -> ~8 chunks)
        print(f"\n[2/4] Uploading 2MB test file...")
        test_data = os.urandom(2 * 1024 * 1024)
        test_file = os.path.join(tmp_dir, "swarm_test.bin")
        with open(test_file, "wb") as f:
            f.write(test_data)

        with open(test_file, "rb") as f:
            resp = httpx.post(
                f"{base_url}/upload",
                files={"file": ("swarm_test.bin", f)},
                data={"password": "swarm-pass"},
                timeout=30,
            )
        assert resp.status_code == 200, f"Upload failed: {resp.text[:200]}"
        result = resp.json()
        file_hash = result["file_hash"]
        print(f"  Uploaded: {result['chunks']} chunks, hash={file_hash[:24]}...")
        print(f"  Merkle root: {result['manifest'].get('merkle_root', '')[:24]}...")
        print("  ✅ Upload successful")

        # Test manifest endpoint
        print(f"\n[3/4] Testing /manifest and /chunk endpoints...")
        resp = httpx.get(f"{base_url}/manifest/{file_hash}", timeout=10)
        assert resp.status_code == 200
        manifest = resp.json()
        assert "merkle_root" in manifest
        assert len(manifest["chunks"]) == result["chunks"]
        print(f"  /manifest: ✅ ({len(manifest['chunks'])} chunks)")

        # Test single chunk endpoint
        chunk_hash = manifest["chunks"][0]["chunk_hash"]
        resp = httpx.get(f"{base_url}/chunk/{chunk_hash}", timeout=10)
        assert resp.status_code == 200
        assert resp.headers.get("x-chunk-hash") == chunk_hash
        print(f"  /chunk: ✅ ({len(resp.content)} bytes)")

        # Parallel swarming test
        print(f"\n[4/4] Testing parallel swarming download...")
        seq_t, par_t = asyncio.run(run_parallel_test(file_hash, base_url))

    finally:
        server.terminate()
        server.wait(timeout=5)
        shutil.rmtree(tmp_dir, ignore_errors=True)
        storage_dir = os.path.join(project_dir, ".storage")
        if os.path.exists(storage_dir):
            shutil.rmtree(storage_dir)

    print("\n" + "=" * 65)
    print("  ✅ PHASE 2.3 VERIFICATION PASSED — Parallel Swarming Working!")
    print("=" * 65)


if __name__ == "__main__":
    try:
        run_test()
    except Exception as e:
        print(f"\n  ❌ ERROR: {e}")
        import traceback; traceback.print_exc()
        sys.exit(1)
