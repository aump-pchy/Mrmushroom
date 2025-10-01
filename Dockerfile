FROM python:3.11-slim

# ติดตั้ง libGL และ dependencies ที่จำเป็นสำหรับ OpenCV และ Ultralytics
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libopencv-dev \
    && rm -rf /var/lib/apt/lists/*

# ตั้ง working directory
WORKDIR /app

# ติดตั้ง dependencies ก่อน เพื่อใช้ layer cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# คัดลอกโค้ดทั้งหมดเข้ามา
COPY . .

# Expose port 8000
EXPOSE 8000

# คำสั่งรัน FastAPI
CMD ["uvicorn", "app.app:app", "--host", "0.0.0.0", "--port", "8000"]
