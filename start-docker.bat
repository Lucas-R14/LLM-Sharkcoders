@echo off
REM start-docker.bat
REM Script para inicializar LLM Pessoal no Windows com Docker

echo ===========================================
echo    LLM Pessoal - Docker para Windows
echo ===========================================
echo.

REM Verificar se Docker está instalado
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker não encontrado! Por favor, instale Docker Desktop.
    echo https://www.docker.com/products/docker-desktop/
    pause
    exit /b 1
)

REM Verificar se Docker está rodando
docker info >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker não está rodando! Inicie Docker Desktop.
    pause
    exit /b 1
)

echo ✅ Docker detectado e rodando
echo.

REM Criar diretórios necessários
if not exist "docker-data" mkdir docker-data
if not exist "docker-data\ollama" mkdir docker-data\ollama
if not exist "docker-data\huggingface" mkdir docker-data\huggingface
if not exist "docker-data\transformers" mkdir docker-data\transformers
if not exist "generated_images" mkdir generated_images
if not exist "logs" mkdir logs

echo 📁 Diretórios criados
echo.

REM Parar containers existentes
echo 🛑 Parando containers existentes...
docker-compose down 2>nul

REM Construir e iniciar
echo 🔨 Construindo imagens...
docker-compose build

echo 🚀 Iniciando serviços...
docker-compose up -d ollama

echo ⏳ Aguardando Ollama (30s)...
timeout /t 30 /nobreak >nul

echo 🤖 Iniciando aplicação...
docker-compose up -d llm-app

echo 📥 Baixando modelos essenciais...
docker-compose up model-downloader

echo.
echo ✅ LLM Pessoal iniciado com sucesso!
echo.
echo 🌐 Acesse: http://localhost:8001
echo 📊 Status: http://localhost:8001/api/status
echo 🔧 Ollama: http://localhost:11434
echo.
echo 📝 Comandos úteis:
echo   - Ver logs: docker-compose logs -f
echo   - Parar: docker-compose down
echo   - Reiniciar: docker-compose restart
echo.
echo Pressione qualquer tecla para ver os logs...
pause >nul
docker-compose logs -f 