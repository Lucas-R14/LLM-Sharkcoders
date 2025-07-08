# LLM Pessoal - Script de Inicialização para Windows (PowerShell)

Write-Host ""
Write-Host "===================================================" -ForegroundColor Blue
Write-Host "   🤖 LLM Pessoal - Assistente Inteligente Local" -ForegroundColor Yellow
Write-Host "===================================================" -ForegroundColor Blue
Write-Host ""

Write-Host "📋 A verificar dependências..." -ForegroundColor Cyan

# Verificar se o Ollama está em execução
$ollamaProcess = Get-Process -Name "ollama" -ErrorAction SilentlyContinue
if (-not $ollamaProcess) {
    Write-Host "🦙 A iniciar Ollama..." -ForegroundColor Yellow
    Start-Process -FilePath "ollama" -ArgumentList "serve" -WindowStyle Hidden
    Start-Sleep -Seconds 3
} else {
    Write-Host "✅ Ollama já está em execução" -ForegroundColor Green
}

# Verificar se o ambiente virtual existe
if (-not (Test-Path "venv\Scripts\python.exe")) {
    Write-Host "❌ Ambiente virtual não encontrado!" -ForegroundColor Red
    Write-Host "💡 Execute primeiro: python -m venv venv" -ForegroundColor Yellow
    Write-Host "💡 Depois instale: venv\Scripts\python.exe -m pip install -r requirements.txt" -ForegroundColor Yellow
    Read-Host "Pressione Enter para continuar..."
    exit 1
}

Write-Host "✅ Ambiente virtual encontrado" -ForegroundColor Green

# Verificar se as dependências estão instaladas
Write-Host "🔍 A verificar dependências Python..." -ForegroundColor Cyan
$testImports = & "venv\Scripts\python.exe" -c "
try:
    import fastapi, torch, diffusers, ollama
    print('SUCCESS')
except ImportError as e:
    print(f'ERROR: {e}')
"

if ($testImports -eq "SUCCESS") {
    Write-Host "✅ Todas as dependências estão instaladas" -ForegroundColor Green
} else {
    Write-Host "❌ Dependências em falta: $testImports" -ForegroundColor Red
    Write-Host "💡 Execute: venv\Scripts\python.exe -m pip install -r requirements.txt" -ForegroundColor Yellow
    Read-Host "Pressione Enter para continuar..."
    exit 1
}

# Iniciar a aplicação
Write-Host ""
Write-Host "🚀 A iniciar LLM Pessoal..." -ForegroundColor Green
Write-Host "🌐 A aplicação estará disponível em: http://localhost:8000" -ForegroundColor Cyan
Write-Host "💡 Pressione Ctrl+C para parar a aplicação" -ForegroundColor Yellow
Write-Host ""

# Abrir automaticamente no browser (opcional)
$openBrowser = Read-Host "Deseja abrir automaticamente no browser? (s/N)"
if ($openBrowser -eq "s" -or $openBrowser -eq "S") {
    Start-Sleep -Seconds 2
    Start-Process "http://localhost:8000"
}

# Executar a aplicação
try {
    & "venv\Scripts\python.exe" app.py
} catch {
    Write-Host "❌ Erro ao executar a aplicação: $_" -ForegroundColor Red
} finally {
    Write-Host ""
    Write-Host "👋 LLM Pessoal foi encerrada" -ForegroundColor Yellow
    Read-Host "Pressione Enter para sair..."
} 