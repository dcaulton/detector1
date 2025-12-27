FROM nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04  # GPU base; swap to python:3.10-slim for CPU-only

ENV PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.10 python3-pip libsndfile1 ffmpeg && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY src/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ .
CMD ["python", "app.py"]
