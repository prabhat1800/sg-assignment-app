# Stage 1: build Python dependencies into an isolated virtualenv.
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
 PYTHONUNBUFFERED=1 \
 PIP_DISABLE_PIP_VERSION_CHECK=1 \
 PATH="/opt/venv/bin:$PATH"

WORKDIR /app

RUN python -m venv /opt/venv
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: runtime image with only app code and prebuilt virtualenv.
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
 PYTHONUNBUFFERED=1 \
 PATH="/opt/venv/bin:$PATH"

WORKDIR /app

RUN apt-get update\
 && apt-get upgrade -y \
 && rm -rf /var/lib/apt/lists/*

COPY --from=builder /opt/venv /opt/venv
COPY app ./app

EXPOSE 8000

# Lightweight container health probe that checks the app health endpoint.
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
 CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2).read()"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]