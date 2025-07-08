# 🔧 Referência Técnica - LLM Pessoal

## 📋 Visão Geral Técnica

A **LLM Pessoal** é uma aplicação web moderna construída com FastAPI que integra múltiplos serviços de IA local. Esta documentação técnica fornece detalhes sobre arquitetura, APIs, configurações e desenvolvimento.

## 🏗️ Arquitetura do Sistema

### Diagrama de Arquitetura
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   AI Services   │
│   (HTML/CSS/JS) │◄──►│   (FastAPI)     │◄──►│   (Ollama/SD)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Static Files  │    │   Templates     │    │   Cache/Data    │
│   (CSS/JS/IMG)  │    │   (Jinja2)      │    │   (Volumes)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Componentes Principais

#### 1. Frontend (Interface Web)
- **Tecnologia**: HTML5, CSS3, JavaScript ES6+
- **Framework**: Vanilla JS com Fetch API
- **UI/UX**: Design responsivo com CSS Grid/Flexbox
- **Interatividade**: Streaming de respostas, tabs dinâmicas

#### 2. Backend (FastAPI)
- **Framework**: FastAPI 0.115.14
- **Servidor**: Uvicorn ASGI
- **Templates**: Jinja2
- **Validação**: Pydantic
- **CORS**: Middleware configurado

#### 3. Serviços de IA
- **Ollama**: Servidor local para modelos LLM
- **Stable Diffusion**: Pipeline de geração de imagens
- **PyTorch**: Framework de deep learning

## 🔌 APIs e Endpoints

### Endpoints Principais

#### Chat API
```python
POST /api/chat
{
    "message": "string",
    "model": "string",
    "stream": boolean
}
```

**Resposta (Streaming)**:
```json
{
    "response": "string",
    "done": boolean
}
```

#### Geração de Imagens
```python
POST /api/generate-image
{
    "prompt": "string",
    "negative_prompt": "string",
    "width": integer,
    "height": integer,
    "num_inference_steps": integer,
    "guidance_scale": float
}
```

**Resposta**:
```json
{
    "image_url": "string",
    "metadata": {
        "prompt": "string",
        "parameters": object
    }
}
```

#### Status e Monitoramento
```python
GET /api/status
GET /api/health
GET /api/models
GET /api/models/detailed
```

### Exemplos de Uso da API

#### Chat com Streaming
```bash
curl -X POST "http://localhost:8001/api/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Explique a fotossíntese",
    "model": "llama3.2:latest",
    "stream": true
  }'
```

#### Geração de Imagem
```bash
curl -X POST "http://localhost:8001/api/generate-image" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Um gato siamês em um jardim japonês",
    "negative_prompt": "borrão, baixa qualidade",
    "width": 512,
    "height": 512,
    "num_inference_steps": 20,
    "guidance_scale": 7.5
  }'
```

## ⚙️ Configurações Detalhadas

### Configurações do Servidor

```python
# app.py - Configurações principais
HOST = "0.0.0.0"           # Endereço de escuta
PORT = 8001                 # Porta do servidor
DEBUG = False               # Modo debug
RELOAD = False              # Auto-reload (desenvolvimento)
WORKERS = 1                 # Número de workers
KEEP_ALIVE = 5             # Keep-alive timeout
```

### Configurações Ollama

```python
# Configurações do cliente Ollama
OLLAMA_HOST = "http://localhost:11434"
OLLAMA_TIMEOUT = 300       # Timeout em segundos
DEFAULT_MODEL = "llama3.2:latest"
MAX_TOKENS = 2048          # Máximo de tokens por resposta
```

### Configurações Stable Diffusion

```python
# Configurações do pipeline SD
STABLE_DIFFUSION_MODEL = "runwayml/stable-diffusion-v1-5"
DEVICE = "auto"            # auto, cuda, cpu
ENABLE_MEMORY_EFFICIENT_ATTENTION = True
ENABLE_VAE_SLICING = True
```

### Configurações de Performance

```python
# Otimizações de memória
PYTORCH_CUDA_ALLOC_CONF = "max_split_size_mb:128"
PYTORCH_ENABLE_MPS_FALLBACK = "1"
HF_HUB_DISABLE_SYMLINKS = "1"
HF_HUB_DISABLE_SYMLINKS_WARNING = "1"
```

## 🗂️ Estrutura de Dados

### Modelos de Dados (Pydantic)

#### ChatRequest
```python
class ChatRequest(BaseModel):
    message: str
    model: str = "llama3.2:latest"
    stream: bool = True
```

#### ImageRequest
```python
class ImageRequest(BaseModel):
    prompt: str
    negative_prompt: str = ""
    width: int = 512
    height: int = 512
    num_inference_steps: int = 20
    guidance_scale: float = 7.5
```

### Estrutura de Diretórios

```
LLM-pessoal/
├── app.py                 # Servidor principal
├── config.py              # Configurações centralizadas
├── requirements.txt       # Dependências Python
├── docker-compose.yml     # Configuração Docker
├── Dockerfile            # Imagem Docker
├── static/               # Arquivos estáticos
│   ├── css/
│   │   └── style.css     # Estilos CSS
│   └── js/
│       └── app.js        # JavaScript
├── templates/            # Templates HTML
│   └── index.html        # Template principal
├── generated_images/     # Imagens geradas
├── logs/                # Logs da aplicação
└── cache/               # Cache de modelos
    ├── huggingface/     # Cache HF
    └── transformers/    # Cache Transformers
```

## 🔧 Desenvolvimento

### Ambiente de Desenvolvimento

#### Pré-requisitos
```bash
# Python 3.8+
python --version

# Pip atualizado
pip install --upgrade pip

# Git
git --version
```

#### Configuração Local
```bash
# Clone o repositório
git clone <url-do-repositorio>
cd LLM-pessoal

# Ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows

# Instalar dependências
pip install -r requirements.txt

# Instalar Ollama
# Windows/Mac: https://ollama.com/
# Linux: curl -fsSL https://ollama.com/install.sh | sh
```

#### Executar em Desenvolvimento
```bash
# Modo debug
export DEBUG=true
export LOG_LEVEL=DEBUG
export RELOAD=true

# Executar
python app.py
```

### Debugging

#### Logs Detalhados
```python
# config.py
LOG_LEVEL = "DEBUG"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
```

#### Verificar Serviços
```bash
# Verificar Ollama
curl http://localhost:11434/api/version

# Verificar aplicação
curl http://localhost:8001/api/health

# Ver logs
tail -f logs/app.log
```

### Testes

#### Testes Manuais
```bash
# Teste de chat
curl -X POST "http://localhost:8001/api/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello", "model": "phi3:mini"}'

# Teste de imagem
curl -X POST "http://localhost:8001/api/generate-image" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "test image"}'
```

#### Testes Automatizados (Futuro)
```python
# tests/test_api.py
import pytest
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

def test_chat_endpoint():
    response = client.post("/api/chat", json={
        "message": "Hello",
        "model": "phi3:mini"
    })
    assert response.status_code == 200
```

## 🐳 Docker

### Dockerfile
```dockerfile
FROM python:3.11-slim

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Instalar PyTorch
RUN pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu

# Copiar código
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Expor porta
EXPOSE 8001

# Comando de inicialização
CMD ["python", "app.py"]
```

### Docker Compose
```yaml
services:
  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama

  llm-app:
    build: .
    ports:
      - "8001:8001"
    volumes:
      - ./generated_images:/app/generated_images
      - ./logs:/app/logs
    depends_on:
      - ollama
```

## 🔒 Segurança

### Configurações de Segurança

#### CORS
```python
# Configuração CORS
CORS_ORIGINS = ["*"]  # Em produção, especificar domínios
```

#### Validação de Entrada
```python
# Pydantic valida automaticamente
class ChatRequest(BaseModel):
    message: str
    model: str = "llama3.2:latest"
    stream: bool = True
```

#### Rate Limiting (Futuro)
```python
# Implementação futura
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
```

## 📊 Monitoramento

### Métricas Disponíveis

#### Status dos Serviços
```python
GET /api/status
{
    "ollama_status": "online",
    "stable_diffusion_status": "online",
    "system_info": {
        "cpu_usage": 45.2,
        "memory_usage": 67.8,
        "gpu_usage": 23.1
    }
}
```

#### Logs Estruturados
```python
import logging
import json

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName
        }
        return json.dumps(log_entry)
```

### Alertas e Notificações

#### Health Checks
```python
@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }
```

## 🚀 Performance

### Otimizações Implementadas

#### Memória
- **VAE Slicing**: Reduz uso de VRAM
- **Memory Efficient Attention**: Otimização de atenção
- **Gradient Checkpointing**: Economia de memória

#### Velocidade
- **Streaming**: Respostas em tempo real
- **Caching**: Cache de modelos Hugging Face
- **Async/Await**: Operações assíncronas

#### GPU
- **CUDA**: Aceleração GPU automática
- **Mixed Precision**: FP16 quando disponível
- **Memory Pinning**: Otimização de transferência

### Benchmarks

#### Tempo de Resposta (Chat)
- **CPU (Intel i7)**: 2-5 segundos
- **GPU (RTX 3060)**: 0.5-2 segundos

#### Tempo de Geração (Imagens)
- **CPU**: 2-5 minutos
- **GPU (6GB VRAM)**: 30-60 segundos
- **GPU (8GB+ VRAM)**: 15-30 segundos

## 🔄 Manutenção

### Backup
```bash
# Backup de dados
tar -czf backup-$(date +%Y%m%d).tar.gz \
    generated_images/ \
    logs/ \
    cache/
```

### Atualizações
```bash
# Atualizar código
git pull origin main

# Atualizar dependências
pip install -r requirements.txt --upgrade

# Reconstruir Docker
docker-compose build --no-cache
```

### Limpeza
```bash
# Limpar cache
rm -rf cache/huggingface/*
rm -rf cache/transformers/*

# Limpar logs antigos
find logs/ -name "*.log" -mtime +30 -delete

# Limpar imagens antigas
find generated_images/ -name "*.png" -mtime +7 -delete
```

---

*Esta documentação técnica é atualizada regularmente conforme a aplicação evolui.* 