"""
DistriStore — Phase 5 Verification Test
Verification Gate 5: Start FastAPI server, upload and download a file via HTTP.

Run from distristore/ directory:
    python -m tests.test_phase5
"""

import os
import sys
import time
import subprocess
import shutil

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

API_PORT = 8765
TCP_PORT = 50099
UDP_PORT = 50098


def run_test():
    print("=" * 60)
    print("  DistriStore — Phase 5 Verification Test")
    print("=" * 60)

    venv_python = sys.executable
    project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    tmp_dir = os.path.join(project_dir, ".test_tmp_p5")
    os.makedirs(tmp_dir, exist_ok=True)

    env = {
        **os.environ,
        "PYTHONPATH": project_dir,
        "DS_NAME": "test-node",
        "DS_TCP_PORT": str(TCP_PORT),
        "DS_UDP_PORT": str(UDP_PORT),
    }

    print(f"\n[1/5] Starting FastAPI server on port {API_PORT}...")
    server = subprocess.Popen(
        [venv_python, "-m", "uvicorn", "backend.main:app",
         "--host", "127.0.0.1", "--port", str(API_PORT)],
        cwd=project_dir, env=env,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    time.sleep(4)

    if server.poll() is not None:
        _, stderr = server.communicate()
        print(f"  ❌ Server crashed on startup:\n{stderr.decode()[-500:]}")
        sys.exit(1)

    print(f"  ✅ Server started (PID={server.pid})")

    try:
        import httpx

        # Test status
        print("\n[2/5] Testing GET /status...")
        resp = httpx.get(f"http://127.0.0.1:{API_PORT}/status", timeout=10)
        assert resp.status_code == 200, f"Status: {resp.status_code}"
        status = resp.json()
        print(f"  Node: {status.get('name')} ({status.get('node_id', '')[:16]}...)")
        print("  ✅ Status working")

        # Upload
        print("\n[3/5] Testing POST /upload...")
        test_data = os.urandom(100 * 1024)
        test_file = os.path.join(tmp_dir, "upload_test.bin")
        with open(test_file, "wb") as f:
            f.write(test_data)

        with open(test_file, "rb") as f:
            resp = httpx.post(
                f"http://127.0.0.1:{API_PORT}/upload",
                files={"file": ("upload_test.bin", f)},
                data={"password": "testpass"},
                timeout=30,
            )
        assert resp.status_code == 200, f"Upload: {resp.status_code} {resp.text[:200]}"
        result = resp.json()
        file_hash = result["file_hash"]
        print(f"  Hash: {file_hash[:24]}... | Chunks: {result['chunks']}")
        print("  ✅ Upload successful")

        # List files
        print("\n[4/5] Testing GET /files...")
        resp = httpx.get(f"http://127.0.0.1:{API_PORT}/files", timeout=10)
        assert resp.status_code == 200
        files = resp.json().get("files", [])
        for fi in files:
            print(f"  - {fi['filename']} ({fi['size']} bytes)")
        print("  ✅ File listing working")

        # Download
        print("\n[5/5] Testing GET /download/{hash}...")
        resp = httpx.get(
            f"http://127.0.0.1:{API_PORT}/download/{file_hash}",
            params={"password": "testpass"},
            timeout=30,
        )
        assert resp.status_code == 200, f"Download: {resp.status_code}"
        assert resp.content == test_data, "Data mismatch!"
        print(f"  Downloaded {len(resp.content)} bytes ✅")

    finally:
        server.terminate()
        server.wait(timeout=5)
        shutil.rmtree(tmp_dir, ignore_errors=True)
        # Cleanup .storage from the test
        storage_dir = os.path.join(project_dir, ".storage")
        if os.path.exists(storage_dir):
            shutil.rmtree(storage_dir)

    print("\n" + "=" * 60)
    print("  ✅ PHASE 5 VERIFICATION PASSED — All checks green!")
    print("=" * 60)


if __name__ == "__main__":
    try:
        run_test()
    except Exception as e:
        print(f"\n  ❌ ERROR: {e}")
        import traceback; traceback.print_exc()
        sys.exit(1)
