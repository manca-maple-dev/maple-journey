#!/bin/sh
# Railway startup script

PORT=${PORT:-8000}
python -m uvicorn server:app --host 0.0.0.0 --port $PORT
