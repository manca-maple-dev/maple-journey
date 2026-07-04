FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy entire backend
COPY backend ./

# Copy startup script
COPY start.py /app/start.py

# Start server - Railway provides PORT env var (default 8000)
CMD ["python", "/app/start.py"]
