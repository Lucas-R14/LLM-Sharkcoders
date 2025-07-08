@echo off
REM LLM Pessoal - Script de Inicialização para Windows
echo.
echo ===================================================
echo   🤖 LLM Pessoal - Assistente Inteligente Local
echo ===================================================
echo.

echo 📋 A verificar dependências...

REM Verificar se o Ollama está em execução
tasklist /FI "IMAGENAME eq ollama.exe" 2>NUL | find /I /N "ollama.exe">NUL
if "%ERRORLEVEL%"=="1" (
    echo 🦙 A iniciar Ollama...
    start /B ollama serve
    timeout /t 3 /nobreak >nul
) else (
    echo ✅ Ollama já está em execução
)

REM Verificar se o ambiente virtual existe
if not exist "venv\Scripts\python.exe" (
    echo ❌ Ambiente virtual não encontrado!
    echo 💡 Execute primeiro: python -m venv venv
    echo 💡 Depois instale: venv\Scripts\python.exe -m pip install -r requirements.txt
    pause
    exit /b 1
)

echo ✅ Ambiente virtual encontrado

REM Iniciar a aplicação
echo.
echo 🚀 A iniciar LLM Pessoal...
echo 🌐 A aplicação estará disponível em: http://localhost:8000
echo 💡 Pressione Ctrl+C para parar a aplicação
echo.

venv\Scripts\python.exe app.py

echo.
echo 👋 LLM Pessoal foi encerrada
pause 