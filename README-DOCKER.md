# 🐳 LLM Pessoal - Guia Docker Completo

## 📋 Visão Geral

Esta versão da **LLM Pessoal** funciona 100% em containers Docker, oferecendo uma solução completa e isolada que resolve problemas de dependências e configuração. Inclui:

- **🤖 Ollama**: Modelos LLM locais (llama3.2, phi3, mistral, etc.)
- **🎨 Stable Diffusion**: Geração de imagens de alta qualidade
- **🌐 Interface Web**: Chat moderno e controle completo
- **⚙️ Configuração Automática**: Tudo pronto para usar
- **📊 Monitoramento**: Status em tempo real dos serviços

## 🚀 Início Rápido

### Windows

1. **Instalar Docker Desktop**
   ```
   https://www.docker.com/products/docker-desktop/
   ```

2. **Executar aplicação**
   ```batch
   # Método 1: Script Batch (mais simples)
   start-docker.bat
   
   # Método 2: PowerShell (mais controle)
   .\start-docker.ps1
   
   # Método 3: Manual
   docker-compose up -d
   ```

3. **Acessar interface**
   - 🌐 **Interface principal**: http://localhost:8001
   - 📊 **Status**: http://localhost:8001/api/status
   - 🔧 **Ollama**: http://localhost:11434

### Linux/macOS

```bash
# Clonar e iniciar
git clone <seu-repo>
cd "LLM pessoal"

# Tornar script executável
chmod +x docker-entrypoint.sh

# Iniciar aplicação
docker-compose up -d

# Ver logs
docker-compose logs -f
```

## 🏗️ Arquitetura Docker

### Serviços Principais

#### 1. Ollama (ollama)
- **Imagem**: `ollama/ollama:latest`
- **Porta**: 11434
- **Função**: Executar modelos LLM locais
- **Volume**: `docker-data/ollama`
- **Healthcheck**: Verifica se está funcionando

#### 2. LLM App (llm-app)
- **Build**: Dockerfile local
- **Porta**: 8001
- **Função**: Interface web e API
- **Volumes**: código, imagens, logs, cache
- **Dependências**: Aguarda Ollama estar saudável

#### 3. Model Downloader (model-downloader)
- **Execução**: Uma vez na inicialização
- **Função**: Baixar modelos essenciais automaticamente
- **Modelos**: llama3.2:latest, phi3:mini
- **Restart**: "no" (executa uma vez)

#### 4. Nginx (nginx) - Opcional
- **Perfil**: production
- **Função**: Proxy reverso e SSL
- **Portas**: 80, 443
- **Configuração**: nginx.conf

### Volumes Persistentes

```yaml
volumes:
  ollama_data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: ./docker-data/ollama
  huggingface_cache:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: ./docker-data/huggingface
  transformers_cache:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: ./docker-data/transformers
```

## 📁 Estrutura do Projeto

```
LLM pessoal/
├── 🐳 Docker Files
│   ├── Dockerfile                 # Container da aplicação
│   ├── docker-compose.yml         # Orquestração de serviços
│   └── docker-entrypoint.sh       # Script de inicialização
│
├── 🚀 Scripts de Execução
│   ├── start-docker.bat           # Windows (Batch)
│   └── start-docker.ps1           # Windows (PowerShell)
│
├── ⚙️ Configuração
│   ├── env.example                # Exemplo de configurações
│   ├── requirements.txt           # Dependências Python
│   └── config.py                  # Configurações da aplicação
│
├── 📱 Aplicação
│   ├── app.py                     # Servidor principal
│   ├── static/                    # CSS, JS, imagens
│   ├── templates/                 # Templates HTML
│   └── generated_images/          # Imagens geradas
│
└── 💾 Dados Persistentes
    ├── docker-data/
    │   ├── ollama/                # Modelos Ollama
    │   ├── huggingface/           # Cache Hugging Face
    │   └── transformers/          # Cache Transformers
    └── logs/                      # Logs da aplicação
```

## ⚡ Comandos Úteis

### Windows PowerShell
```powershell
# Iniciar aplicação
.\start-docker.ps1

# Ver status
.\start-docker.ps1 -Status

# Ver logs
.\start-docker.ps1 -Logs

# Parar aplicação
.\start-docker.ps1 -Stop

# Reconstruir containers
.\start-docker.ps1 -Rebuild

# Pular download de modelos
.\start-docker.ps1 -NoModels
```

### Comandos Docker Diretos
```bash
# Iniciar todos os serviços
docker-compose up -d

# Ver logs em tempo real
docker-compose logs -f

# Ver logs de um serviço específico
docker-compose logs -f llm-app

# Parar todos os serviços
docker-compose down

# Reconstruir e iniciar
docker-compose up -d --build

# Ver status dos containers
docker-compose ps

# Executar comando no container
docker-compose exec llm-app bash

# Ver uso de recursos
docker stats

# Limpar volumes (cuidado!)
docker-compose down -v
```

### Gestão de Modelos Ollama
```bash
# Listar modelos instalados
curl http://localhost:11434/api/tags

# Baixar modelo específico
curl -X POST http://localhost:11434/api/pull \
  -H "Content-Type: application/json" \
  -d '{"name": "llama3.2:latest"}'

# Executar comando no container Ollama
docker-compose exec ollama ollama list
docker-compose exec ollama ollama pull codellama:latest

# Ver informações do modelo
docker-compose exec ollama ollama show llama3.2:latest
```

## 🔑 Configurações Avançadas

### Arquivo .env (Opcional)

Copie `env.example` para `.env` e ajuste:

```bash
# Configurações básicas
HOST=0.0.0.0
PORT=8001
OLLAMA_HOST=http://ollama:11434

# Stable Diffusion
STABLE_DIFFUSION_MODEL=runwayml/stable-diffusion-v1-5
DEVICE=auto

# Performance
WORKERS=1
KEEP_ALIVE=5

# Debug (desenvolvimento)
DEBUG=true
LOG_LEVEL=DEBUG

# Windows/WSL
WSL_OPTIMIZATION=true
```

### Configurações Docker Compose

#### Personalizar Portas
```yaml
services:
  llm-app:
    ports:
      - "8080:8001"  # Mudar porta externa
```

#### Adicionar Variáveis de Ambiente
```yaml
services:
  llm-app:
    environment:
      - CUSTOM_VAR=value
      - ANOTHER_VAR=value
```

#### Configurar Recursos
```yaml
services:
  llm-app:
    deploy:
      resources:
        limits:
          memory: 4G
          cpus: '2.0'
        reservations:
          memory: 2G
          cpus: '1.0'
```

## 🔧 Troubleshooting

### Problemas Comuns

#### Container não inicia
```bash
# Ver logs detalhados
docker-compose logs llm-app

# Verificar se portas estão livres
netstat -an | grep 8001

# Reconstruir imagem
docker-compose build --no-cache
```

#### Ollama não conecta
```bash
# Verificar se Ollama está rodando
docker-compose ps ollama

# Ver logs do Ollama
docker-compose logs ollama

# Reiniciar apenas Ollama
docker-compose restart ollama
```

#### Erro de memória
```bash
# Verificar uso de memória
docker stats

# Limpar cache não usado
docker system prune -a

# Aumentar memória do Docker (Windows/macOS)
# Docker Desktop > Settings > Resources > Memory
```

#### Modelos não baixam
```bash
# Verificar logs do downloader
docker-compose logs model-downloader

# Baixar manualmente
docker-compose exec ollama ollama pull llama3.2:latest

# Verificar espaço em disco
df -h
```

### Logs e Debug

#### Verificar Logs
```bash
# Logs de todos os serviços
docker-compose logs

# Logs em tempo real
docker-compose logs -f

# Logs de serviço específico
docker-compose logs -f llm-app

# Últimas 100 linhas
docker-compose logs --tail=100
```

#### Modo Debug
```yaml
services:
  llm-app:
    environment:
      - DEBUG=true
      - LOG_LEVEL=DEBUG
```

### Performance

#### Otimizações para GPU
```yaml
services:
  llm-app:
    runtime: nvidia
    environment:
      - NVIDIA_VISIBLE_DEVICES=all
      - NVIDIA_DRIVER_CAPABILITIES=compute,utility
```

#### Otimizações para CPU
```yaml
services:
  llm-app:
    environment:
      - DEVICE=cpu
      - ENABLE_MEMORY_EFFICIENT_ATTENTION=false
```

## 📊 Monitoramento

### Health Checks
- **Ollama**: Verifica se responde na API
- **LLM App**: Verifica se a aplicação está online
- **Intervalo**: 30 segundos
- **Timeout**: 10 segundos

### Métricas Disponíveis
```bash
# Status da aplicação
curl http://localhost:8001/api/status

# Health check
curl http://localhost:8001/api/health

# Informações do sistema
curl http://localhost:8001/api/system-info
```

## 🔄 Manutenção

### Atualizações
```bash
# Atualizar código
git pull origin main

# Reconstruir containers
docker-compose build --no-cache

# Reiniciar serviços
docker-compose up -d
```

### Backup
```bash
# Backup dos dados
tar -czf backup-$(date +%Y%m%d).tar.gz docker-data/ logs/

# Restaurar backup
tar -xzf backup-20231201.tar.gz
```

### Limpeza
```bash
# Limpar containers parados
docker container prune

# Limpar imagens não usadas
docker image prune

# Limpar volumes não usados
docker volume prune

# Limpeza completa
docker system prune -a
```

## 🚀 Produção

### Configuração para Produção
```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  nginx:
    profiles: ["production"]
    # ... configuração nginx
```

### SSL/HTTPS
```yaml
services:
  nginx:
    volumes:
      - ./ssl:/etc/nginx/ssl:ro
    ports:
      - "443:443"
```

### Load Balancing
```yaml
services:
  llm-app:
    deploy:
      replicas: 3
```

## 📚 Recursos Adicionais

### Documentação
- [Docker Compose](https://docs.docker.com/compose/)
- [Ollama](https://ollama.com/docs)
- [FastAPI](https://fastapi.tiangolo.com/)

### Comunidade
- [GitHub Issues](https://github.com/seu-repo/issues)
- [Discord](https://discord.gg/seu-servidor)

---

**🐳 Docker torna a LLM Pessoal fácil de usar em qualquer sistema!** 