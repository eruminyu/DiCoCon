FROM python:3.12-slim

WORKDIR /app

# Pillow(WebP/GIF 처리)에 필요한 최소 시스템 라이브러리 설치
RUN apt-get update && apt-get install -y --no-install-recommends \
    libwebp-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY bot.py .
COPY cons_db.json .
COPY cons/ ./cons/

# 캐시 디렉터리 생성
RUN mkdir -p /app/cons /app/cache

EXPOSE 8000

CMD ["python", "-u", "bot.py"]
