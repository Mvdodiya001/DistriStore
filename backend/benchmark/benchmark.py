"""
DistriStore — Benchmark Script
Automated testing: uploads files of varying sizes, measures latency
and turnaround time, logs results to CSV.
"""

import asyncio
import csv
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))

from backend.utils.logger import setup_logging, get_logger
from backend.file_engine.chunker import chunk_file, merge_chunks
from backend.file_engine.crypto import sha256_hash
from backend.storage.local_store import LocalStore

logger = get_logger("benchmark")

# Test file sizes: 10 files from 64KB to 10MB
TEST_SIZES = [
    64 * 1024,        # 64 KB
    128 * 1024,       # 128 KB
    256 * 1024,       # 256 KB
    512 * 1024,       # 512 KB
    1024 * 1024,      # 1 MB
    2 * 1024 * 1024,  # 2 MB
    3 * 1024 * 1024,  # 3 MB
    4 * 1024 * 1024,  # 4 MB
    5 * 1024 * 1024,  # 5 MB
    10 * 1024 * 1024, # 10 MB
]


def format_bytes(b):
    if b < 1024: return f"{b} B"
    if b < 1024**2: return f"{b/1024:.1f} KB"
    return f"{b/1024**2:.1f} MB"


def run_benchmark():
    setup_logging("INFO")
    print("=" * 70)
    print("  DistriStore — Benchmark Suite")
    print("=" * 70)

    tmp_dir = os.path.join(os.path.dirname(__file__), "..", ".benchmark_tmp")
    os.makedirs(tmp_dir, exist_ok=True)
    store = LocalStore(os.path.join(tmp_dir, ".storage"))

    csv_path = os.path.join(os.path.dirname(__file__), "..", "benchmark_results.csv")
    results = []

    password = "benchmark-password"

    print(f"\nRunning {len(TEST_SIZES)} tests...\n")
    print(f"{'Size':>10} │ {'Chunk':>6} │ {'Encrypt':>10} │ {'Store':>10} │ {'Load':>10} │ {'Decrypt':>10} │ {'Total':>10} │ {'Status'}")
    print("─" * 90)

    for i, size in enumerate(TEST_SIZES):
        test_file = os.path.join(tmp_dir, f"test_{i}.bin")

        # Generate random data
        data = os.urandom(size)
        with open(test_file, "wb") as f:
            f.write(data)

        try:
            # 1. Chunk + Encrypt
            t0 = time.perf_counter()
            manifest, chunks = chunk_file(test_file, password=password)
            t_chunk = time.perf_counter() - t0

            # 2. Store to disk
            t0 = time.perf_counter()
            for info, chunk_data in zip(manifest.chunks, chunks):
                store.save_chunk(info.chunk_hash, chunk_data)
            store.save_manifest(manifest.file_hash, manifest.to_dict())
            t_store = time.perf_counter() - t0

            # 3. Load from disk
            t0 = time.perf_counter()
            loaded = [store.load_chunk(info.chunk_hash) for info in manifest.chunks]
            t_load = time.perf_counter() - t0

            # 4. Decrypt + Merge
            t0 = time.perf_counter()
            restored = merge_chunks(manifest, loaded, password=password)
            t_merge = time.perf_counter() - t0

            total = t_chunk + t_store + t_load + t_merge

            # Verify integrity
            ok = (sha256_hash(restored) == sha256_hash(data))
            status = "✅ PASS" if ok else "❌ FAIL"

            results.append({
                "file_size_bytes": size,
                "file_size_human": format_bytes(size),
                "num_chunks": len(chunks),
                "chunk_encrypt_ms": round(t_chunk * 1000, 2),
                "store_ms": round(t_store * 1000, 2),
                "load_ms": round(t_load * 1000, 2),
                "decrypt_merge_ms": round(t_merge * 1000, 2),
                "total_ms": round(total * 1000, 2),
                "integrity": "PASS" if ok else "FAIL",
            })

            print(f"{format_bytes(size):>10} │ {len(chunks):>6} │ {t_chunk*1000:>8.1f}ms │ {t_store*1000:>8.1f}ms │ {t_load*1000:>8.1f}ms │ {t_merge*1000:>8.1f}ms │ {total*1000:>8.1f}ms │ {status}")

        except Exception as e:
            print(f"{format_bytes(size):>10} │ ERROR: {e}")
            results.append({
                "file_size_bytes": size,
                "file_size_human": format_bytes(size),
                "error": str(e),
            })

        # Cleanup test file
        os.unlink(test_file)

    # Write CSV
    print(f"\n📄 Writing results to: {csv_path}")
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "file_size_bytes", "file_size_human", "num_chunks",
            "chunk_encrypt_ms", "store_ms", "load_ms",
            "decrypt_merge_ms", "total_ms", "integrity"
        ])
        writer.writeheader()
        for r in results:
            if "error" not in r:
                writer.writerow(r)

    # Cleanup
    import shutil
    shutil.rmtree(tmp_dir, ignore_errors=True)

    # Summary
    if results:
        avg_total = sum(r.get("total_ms", 0) for r in results if "total_ms" in r) / len([r for r in results if "total_ms" in r])
        all_pass = all(r.get("integrity") == "PASS" for r in results if "integrity" in r)
        print(f"\n{'─' * 70}")
        print(f"  Average turnaround: {avg_total:.1f}ms")
        print(f"  All integrity checks: {'✅ PASSED' if all_pass else '❌ FAILED'}")

    print("\n" + "=" * 70)
    print("  ✅ BENCHMARK COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    run_benchmark()
