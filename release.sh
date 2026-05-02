#!/bin/bash

echo "========================================="
echo "  Preparing DistriStore v1.0.0 Release"
echo "========================================="

echo "[1/3] Cleaning temporary caches..."
rm -rf .storage/
rm -rf backend/.benchmark_tmp/
rm -rf frontend/dist/
rm -rf .test_perf/
rm -rf .test_tmp*/
rm -f .test_upload.bin
find . -type d -name "__pycache__" -exec rm -rf {} +
echo "      Done."

echo "[2/3] Running sanity tests..."
source .venv/bin/activate
if python -m tests.test_phase1 && \
   python -m tests.test_phase5 && \
   python -m tests.test_phase13_throughput; then
    echo "      Tests passed."
else
    echo "      Tests FAILED! Aborting release."
    exit 1
fi

echo ""
echo "[3/3] Ready for v1.0.0!"
echo "========================================="
echo "To publish this release, run the following commands:"
echo ""
echo "  git add ."
echo "  git commit -m \"chore: prepare v1.0.0 release\""
echo "  git tag -a v1.0.0 -m \"Initial Release\""
echo "  git push origin main --tags"
echo "========================================="
