FROM python:3.11-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1

# ติดตั้ง libglib2.0 (fix libGL.so.1 error)
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Railway จะ inject $PORT ให้เสมอ
CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port ${PORT}"]