FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
        fonts-liberation \
        libpango-1.0-0 \
        libpangoft2-1.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY api ./api
COPY agent ./agent
COPY core ./core
COPY db ./db
COPY pipeline ./pipeline
COPY reports ./reports
COPY skills ./skills
COPY architecture.html app.html README.md DEPLOY.md ./

RUN useradd --create-home --shell /usr/sbin/nologin plantsage \
    && mkdir -p /app/generated_reports /app/data/uploads \
    && chown -R plantsage:plantsage /app

USER plantsage

EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -fsS "http://127.0.0.1:${PORT:-8080}/health" || exit 1

CMD ["sh", "-c", "python -m uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
