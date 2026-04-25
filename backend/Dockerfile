# ─────────────────────────────────────────────────────────
# DistriStore — Backend Dockerfile
# Python 3.11 slim | FastAPI + Uvicorn | AES-256-GCM
# ─────────────────────────────────────────────────────────

FROM python:3.11-slim

# System deps for pycryptodome build (if needed) + psutil
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc build-essential && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies first (cached layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy entire project (backend module + config + tests)
COPY backend/ ./backend/
COPY tests/ ./tests/
COPY config.yaml .

# Create storage directory
RUN mkdir -p /app/.storage

# Expose ports
#   8001  — FastAPI REST API
#   50001 — TCP P2P chunk transfer
#   50000 — UDP LAN discovery (broadcast)
EXPOSE 8001
EXPOSE 50001
EXPOSE 50000/udp

# Environment defaults (can be overridden in docker-compose)
ENV DS_NAME=distristore-node
ENV DS_TCP_PORT=50001
ENV DS_UDP_PORT=50000

# Health check — verify API is responding
HEALTHCHECK --interval=10s --timeout=5s --retries=5 --start-period=15s \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8001/status')" || exit 1

# Start FastAPI via Uvicorn
CMD ["python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8001"]
