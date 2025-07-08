# start-docker.ps1
# Script PowerShell para LLM Pessoal com Docker

param(
    [switch]$Rebuild,
    [switch]$NoModels,
    [switch]$Logs,
    [switch]$Stop,
    [switch]$Status
)

# Configurações
$ProjectName = "LLM Pessoal"
$ComposeFile = "docker-compose.yml"
$AppUrl = "http://localhost:8001"
$StatusUrl = "$AppUrl/api/status"
$OllamaUrl = "http://localhost:11434"

# Cores para output
function Write-ColorOutput($ForegroundColor) {
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    if ($args) {
        Write-Output $args
    }
    $host.UI.RawUI.ForegroundColor = $fc
}

function Write-Header {
    Write-Host "===========================================" -ForegroundColor Cyan
    Write-Host "     $ProjectName - Docker Management     " -ForegroundColor Cyan
    Write-Host "===========================================" -ForegroundColor Cyan
    Write-Host ""
}

function Test-Docker {
    try {
        docker --version | Out-Null
        if ($LASTEXITCODE -ne 0) { throw }
        Write-ColorOutput Green "✅ Docker detectado"
    }
    catch {
        Write-ColorOutput Red "❌ Docker não encontrado!"
        Write-Host "Instale Docker Desktop: https://www.docker.com/products/docker-desktop/"
        exit 1
    }

    try {
        docker info | Out-Null
        if ($LASTEXITCODE -ne 0) { throw }
        Write-ColorOutput Green "✅ Docker está rodando"
    }
    catch {
        Write-ColorOutput Red "❌ Docker não está rodando!"
        Write-Host "Inicie Docker Desktop primeiro."
        exit 1
    }
}

function New-Directories {
    $dirs = @(
        "docker-data",
        "docker-data/ollama",
        "docker-data/huggingface", 
        "docker-data/transformers",
        "generated_images",
        "logs"
    )
    
    foreach ($dir in $dirs) {
        if (!(Test-Path $dir)) {
            New-Item -ItemType Directory -Path $dir -Force | Out-Null
        }
    }
    Write-ColorOutput Green "📁 Diretórios criados"
}

function Stop-Application {
    Write-ColorOutput Yellow "🛑 Parando aplicação..."
    docker-compose down
    Write-ColorOutput Green "✅ Aplicação parada"
}

function Start-Application {
    Write-ColorOutput Yellow "🚀 Iniciando $ProjectName..."
    
    if ($Rebuild) {
        Write-Host "🔨 Reconstruindo imagens..."
        docker-compose build --no-cache
    }
    
    # Iniciar Ollama primeiro
    Write-Host "🤖 Iniciando Ollama..."
    docker-compose up -d ollama
    
    # Aguardar Ollama
    Write-Host "⏳ Aguardando Ollama ficar disponível..."
    $timeout = 60
    $count = 0
    do {
        Start-Sleep 2
        $count += 2
        try {
            $response = Invoke-WebRequest -Uri "$OllamaUrl/api/version" -TimeoutSec 5 -ErrorAction SilentlyContinue
            if ($response.StatusCode -eq 200) {
                Write-ColorOutput Green "✅ Ollama conectado!"
                break
            }
        }
        catch {
            Write-Host "." -NoNewline
        }
    } while ($count -lt $timeout)
    
    if ($count -ge $timeout) {
        Write-ColorOutput Red "❌ Timeout aguardando Ollama"
        exit 1
    }
    
    # Iniciar aplicação
    Write-Host "🌐 Iniciando aplicação web..."
    docker-compose up -d llm-app
    
    # Baixar modelos se solicitado
    if (-not $NoModels) {
        Write-Host "📥 Baixando modelos essenciais..."
        docker-compose up model-downloader
    }
    
    Write-Host ""
    Write-ColorOutput Green "✅ $ProjectName iniciado com sucesso!"
    Write-Host ""
    Write-Host "🌐 Interface: $AppUrl" -ForegroundColor Cyan
    Write-Host "📊 Status: $StatusUrl" -ForegroundColor Cyan
    Write-Host "🔧 Ollama: $OllamaUrl" -ForegroundColor Cyan
    Write-Host ""
}

function Get-AppStatus {
    Write-Host "📊 Status da aplicação:" -ForegroundColor Cyan
    
    try {
        $status = Invoke-RestMethod -Uri $StatusUrl -TimeoutSec 10
        Write-Host "  Ollama: " -NoNewline
        if ($status.ollama) {
            Write-ColorOutput Green "✅ Online"
        } else {
            Write-ColorOutput Red "❌ Offline"
        }
        
        Write-Host "  Stable Diffusion: " -NoNewline
        if ($status.stable_diffusion) {
            Write-ColorOutput Green "✅ Carregado"
        } else {
            Write-ColorOutput Red "❌ Indisponível"
        }
        
        Write-Host "  Dispositivo: $($status.device)" -ForegroundColor Yellow
        Write-Host "  Modelos disponíveis: $($status.available_models)" -ForegroundColor Yellow
        Write-Host "  Versão: $($status.version)" -ForegroundColor Yellow
        
        if ($status.gpu_info -and $status.gpu_info -ne "N/A") {
            Write-Host "  GPU: $($status.gpu_info)" -ForegroundColor Green
        }
    }
    catch {
        Write-ColorOutput Red "❌ Não foi possível obter status"
        Write-Host "A aplicação pode não estar rodando."
    }
}

function Show-Logs {
    Write-Host "📋 Logs da aplicação (Ctrl+C para sair):" -ForegroundColor Cyan
    docker-compose logs -f
}

# Script principal
Write-Header
Test-Docker
New-Directories

if ($Stop) {
    Stop-Application
    exit 0
}

if ($Status) {
    Get-AppStatus
    exit 0
}

if ($Logs) {
    Show-Logs
    exit 0
}

# Parar containers existentes
docker-compose down 2>$null

# Iniciar aplicação
Start-Application

# Mostrar status
Start-Sleep 5
Get-AppStatus

Write-Host ""
Write-Host "💡 Dicas:" -ForegroundColor Yellow
Write-Host "  - Ver logs: .\start-docker.ps1 -Logs"
Write-Host "  - Status: .\start-docker.ps1 -Status" 
Write-Host "  - Parar: .\start-docker.ps1 -Stop"
Write-Host "  - Reconstruir: .\start-docker.ps1 -Rebuild"
Write-Host "" 