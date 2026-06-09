FROM python:3.11-slim

# System deps for pyaudio + audio handling + faiss
RUN apt-get update && apt-get install -y \
    portaudio19-dev \
    ffmpeg \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

COPY backend backend

EXPOSE 8000 8501
