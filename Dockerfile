# Estágio 1: Build das dependências
FROM python:3.11-slim as builder

# Definir variáveis de ambiente para build
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Instalar dependências do sistema necessárias para build
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    cmake \
    pkg-config \
    libffi-dev \
    libssl-dev \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Criar diretório de trabalho
WORKDIR /build

# Copiar ficheiros de dependências
COPY requirements.txt .

# Criar ambiente virtual e instalar dependências
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Instalar dependências Python
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt

# Estágio 2: Runtime otimizado
FROM python:3.11-slim as runtime

# Definir variáveis de ambiente
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    DEBIAN_FRONTEND=noninteractive

# Criar utilizador não-root para segurança
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Instalar dependências de runtime
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copiar ambiente virtual do estágio de build
COPY --from=builder /opt/venv /opt/venv

# Criar diretórios necessários
RUN mkdir -p /app/cache/whisper \
             /app/cache/huggingface \
             /app/cache/transformers \
             /app/generated_images \
             /app/logs \
             /app/static \
             /app/templates \
    && chown -R appuser:appuser /app

# Definir diretório de trabalho
WORKDIR /app

# Copiar código da aplicação
COPY --chown=appuser:appuser . .

# Mudar para utilizador não-root
USER appuser

# Expor porta
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# Comando de inicialização
CMD ["python", "app.py"] 