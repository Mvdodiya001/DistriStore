"""
DistriStore — Phase 13 Verification: Advanced Throughput & Reliability
Verifies dynamic chunk sizing logic, streaming limits, and async file I/O operations.
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from backend.file_engine.chunker import (
    get_optimal_chunk_size, 
    _CHUNK_256KB, 
    _CHUNK_1MB, 
    _CHUNK_4MB,
    _async_read_file_chunks,
    _async_write_bytes
)
from backend.network.connection import STREAM_LIMIT, BUFFER_SIZE

async def run_test():
    print("=" * 60)
    print("  DistriStore — Phase 13 Verification Test (Throughput & Reliability)")
    print("=" * 60)

    # 1. Test Dynamic Chunk Sizing Thresholds
    print("\n[1/3] Testing Dynamic Chunk Sizing logic...")
    
    # < 50MB should be 256KB
    assert get_optimal_chunk_size(10 * 1024 * 1024) == _CHUNK_256KB, "Failed <50MB threshold"
    
    # 50MB - 500MB should be 1MB
    assert get_optimal_chunk_size(100 * 1024 * 1024) == _CHUNK_1MB, "Failed 50-500MB threshold"
    
    # > 500MB should be 4MB
    assert get_optimal_chunk_size(1000 * 1024 * 1024) == _CHUNK_4MB, "Failed >500MB threshold"
    
    print("  ✅ Dynamic Chunk Sizing works correctly")

    # 2. Test TCP Buffer Limits are scaled correctly
    print("\n[2/3] Checking TCP Buffer Tuning...")
    assert BUFFER_SIZE >= 1048576, f"BUFFER_SIZE is {BUFFER_SIZE}, should be at least 1MB"
    assert STREAM_LIMIT >= 8388608, f"STREAM_LIMIT is {STREAM_LIMIT}, should be at least 8MB"
    print("  ✅ TCP Buffer constants tuned for 4MB chunks")

    # 3. Test Multithreaded Disk I/O wrappers
    print("\n[3/3] Testing Async Disk I/O wrappers...")
    test_file = "phase13_test_file.bin"
    test_data = b"hello async disk IO test"
    
    try:
        # Test async write
        await _async_write_bytes(test_file, test_data)
        assert os.path.exists(test_file), "Async write failed to create file"
        
        # Test async read chunks
        chunks = await _async_read_file_chunks(test_file, chunk_size=10)
        
        # We expect 3 chunks: [0:10], [10:20], [20:24]
        assert len(chunks) == 3, f"Expected 3 chunks, got {len(chunks)}"
        assert chunks[0][1] == b"hello asyn", "Chunk 0 mismatch"
        assert chunks[1][1] == b"c disk IO ", "Chunk 1 mismatch"
        assert chunks[2][1] == b"test", "Chunk 2 mismatch"
        
        print("  ✅ Async read/write via asyncio.to_thread works")
        
    finally:
        if os.path.exists(test_file):
            os.remove(test_file)

    print("\n" + "=" * 60)
    print("  ✅ PHASE 13 VERIFICATION PASSED")
    print("=" * 60)

if __name__ == "__main__":
    try:
        asyncio.run(run_test())
    except AssertionError as e:
        print(f"\n  ❌ VERIFICATION FAILED: {e}")
        sys.exit(1)
