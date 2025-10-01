FROM python:3.11-slim

# ติดตั้ง libGL + deps ที่จำเป็นสำหรับ OpenCV
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ติดตั้ง requirements ก่อน เพื่อ cache layer
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy code ทั้งหมด
COPY . .

EXPOSE 8000
CMD ["uvicorn", "app.app:app", "--host", "0.0.0.0", "--port", "8000"]
