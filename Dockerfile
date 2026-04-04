FROM python:3.11-slim

WORKDIR /app

# 시스템 패키지
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl build-essential libpq-dev && rm -rf /var/lib/apt/lists/*

# Python 패키지
RUN pip install --no-cache-dir \
    fastapi uvicorn httpx psycopg2-binary pydantic paramiko pyyaml websockets

# 앱 복사
COPY apps/ apps/
COPY packages/ packages/
COPY contents/ contents/

ENV PYTHONPATH=/app

EXPOSE 9100

CMD ["python", "-m", "uvicorn", "apps.ccc-api.src.main:app", "--host", "0.0.0.0", "--port", "9100"]
