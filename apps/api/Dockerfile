# SecureAI Studio API — production image.
# Build context is apps/api. Works on Cloud Run / Fly.io / any container host.
# The platform provides $PORT (Cloud Run defaults to 8080).
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8080

WORKDIR /app

# Dependencies first for better layer caching.
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Application source (tests excluded via .dockerignore).
COPY src ./src

# Run as a non-root user.
RUN useradd -m appuser
USER appuser

EXPOSE 8080

# Gunicorn with Uvicorn workers. Shell form so ${PORT} is expanded at runtime.
CMD exec gunicorn src.main:app \
    -k uvicorn.workers.UvicornWorker \
    -b "0.0.0.0:${PORT}" \
    --workers "${WEB_CONCURRENCY:-2}" \
    --timeout 60 \
    --access-logfile - --error-logfile -
