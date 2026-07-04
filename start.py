#!/usr/bin/env python
"""Entrypoint script to start the FastAPI server with proper PORT env var handling."""
import os
import subprocess
import sys

port = os.environ.get("PORT", "8000")
cmd = [sys.executable, "-m", "uvicorn", "server:app", "--host", "0.0.0.0", "--port", port]
print(f"🚀 Starting server on port {port}...", file=sys.stderr)
subprocess.run(cmd, cwd="/app")
