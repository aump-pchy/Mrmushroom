FROM python:3.11-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1

# ติดตั้ง libglib2.0 (แก้ libGL.so.1)
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

