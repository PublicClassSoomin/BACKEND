# 1. 빌드 속도를 위해 가벼운 이미지가 아닌 필요한 도구가 포함된 이미지를 권장할 때도 있습니다.
FROM python:3.11-slim

# 2. 필수 빌드 도구 설치 (ChromaDB 등은 컴파일이 필요할 수 있음)
RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 3. 중요: 소스 코드보다 requirements.txt를 먼저 복사해서 캐시를 활용합니다.
COPY requirements.txt .

# 4. 타임아웃을 늘리고 캐시 없이 설치
RUN pip install --no-cache-dir --default-timeout=100 -r requirements.txt

# 5. 마지막에 소스 코드 복사 (코드만 수정했을 때 패키지 재설치를 방지)
COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]