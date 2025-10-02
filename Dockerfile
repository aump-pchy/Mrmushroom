# Base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Prevent Python from buffering stdout/stderr
ENV PYTHONUNBUFFERED=1

# Install minimal system dependencies (no libGL needed)
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Replace opencv with headless to avoid libGL issue
RUN sed -i 's/opencv-python/opencv-python-headless/g' requirements.txt || true

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port (Railway will override with $PORT)
EXPOSE 8080

# Start command: expand $PORT correctly
CMD exec uvicorn app:app --host 0.0.0.0 --port ${PORT:-8080}
