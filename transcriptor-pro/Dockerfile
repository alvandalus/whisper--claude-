# Dockerfile para Transcriptor Pro
# Imagen multi-stage para optimizar tamaño

# Stage 1: Builder
FROM python:3.11-slim as builder

WORKDIR /app

# Instalar dependencias de compilación
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements y instalar dependencias en un virtual env
COPY requirements.txt .
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim

LABEL maintainer="alvandalus"
LABEL description="Transcriptor Pro - Sistema de transcripción multi-proveedor"
LABEL version="1.0"

# Variables de entorno
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH" \
    DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# Instalar FFmpeg y dependencias runtime
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copiar virtual env desde builder
COPY --from=builder /opt/venv /opt/venv

# Copiar código de la aplicación
COPY src/ ./src/
COPY run.sh ./

# Crear directorios necesarios
RUN mkdir -p /app/transcripts /app/logs /app/INBOX /app/OUT

# Crear usuario no-root para ejecutar la app
RUN useradd -m -u 1000 transcriptor && \
    chown -R transcriptor:transcriptor /app

USER transcriptor

# Exponer puerto (si se implementa API REST en el futuro)
EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Comando por defecto
CMD ["python", "-m", "src.main"]
