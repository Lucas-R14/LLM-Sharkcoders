#!/bin/bash
# LLM Pessoal - Script de Instalação para WSL Ubuntu
# Este script configura tudo o que é necessário para executar a LLM Pessoal no WSL

set -e  # Parar em caso de erro

echo "🚀 Iniciando instalação da LLM Pessoal no WSL..."

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Função para imprimir mensagens coloridas
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCESSO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[AVISO]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERRO]${NC} $1"
}

# Verificar se está no WSL
if ! grep -q Microsoft /proc/version; then
    print_warning "Este script foi otimizado para WSL. Pode funcionar noutra distribuição, mas não é garantido."
fi

# 1. Actualizar sistema
print_status "A actualizar o sistema Ubuntu..."
sudo apt update && sudo apt upgrade -y

# 2. Instalar dependências do sistema
print_status "A instalar dependências do sistema..."
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    git \
    curl \
    wget \
    build-essential \
    cmake \
    pkg-config \
    libssl-dev \
    libffi-dev \
    libxml2-dev \
    libxslt1-dev \
    libjpeg-dev \
    libpng-dev \
    zlib1g-dev \
    software-properties-common \
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release

# 3. Verificar Python
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
print_status "Versão do Python detectada: $PYTHON_VERSION"

if ! python3 -c "import sys; assert sys.version_info >= (3, 8)" 2>/dev/null; then
    print_error "Python 3.8+ é necessário. Por favor, actualize o Python."
    exit 1
fi

# 4. Criar ambiente virtual
print_status "A criar ambiente virtual Python..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    print_success "Ambiente virtual criado"
else
    print_warning "Ambiente virtual já existe"
fi

# 5. Activar ambiente virtual
print_status "A activar ambiente virtual..."
source venv/bin/activate

# 6. Actualizar pip
print_status "A actualizar pip..."
pip install --upgrade pip setuptools wheel

# 7. Instalar dependências Python
print_status "A instalar dependências Python..."
pip install -r requirements.txt

# 8. Verificar e instalar CUDA (se disponível)
print_status "A verificar suporte CUDA..."
if command -v nvidia-smi &> /dev/null; then
    print_success "NVIDIA GPU detectada"
    
    # Instalar PyTorch com CUDA
    print_status "A instalar PyTorch com suporte CUDA..."
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
else
    print_warning "NVIDIA GPU não detectada. A usar versão CPU do PyTorch."
    print_warning "Para melhor performance, considere configurar GPU passthrough no WSL2."
fi

# 9. Instalar Ollama
print_status "A instalar Ollama..."
if ! command -v ollama &> /dev/null; then
    curl -fsSL https://ollama.ai/install.sh | sh
    print_success "Ollama instalado"
else
    print_warning "Ollama já está instalado"
fi

# 10. Configurar Ollama para iniciar automaticamente
print_status "A configurar Ollama..."
if ! systemctl is-active --quiet ollama 2>/dev/null; then
    print_status "A criar serviço systemd para Ollama..."
    
    sudo tee /etc/systemd/system/ollama.service > /dev/null <<EOF
[Unit]
Description=Ollama Service
After=network-online.target

[Service]
ExecStart=/usr/local/bin/ollama serve
User=$USER
Group=$USER
Restart=always
RestartSec=3
Environment="PATH=/usr/local/bin:/usr/bin:/bin"
Environment="OLLAMA_HOST=0.0.0.0"

[Install]
WantedBy=default.target
EOF

    sudo systemctl daemon-reload
    sudo systemctl enable ollama
    sudo systemctl start ollama
    print_success "Serviço Ollama configurado e iniciado"
fi

# 11. Descarregar modelo padrão do Ollama
print_status "A descarregar modelo padrão do Ollama (llama2)..."
if ! ollama list | grep -q llama2; then
    print_status "A descarregar llama2 (isto pode demorar alguns minutos)..."
    ollama pull llama2
    print_success "Modelo llama2 descarregado"
else
    print_warning "Modelo llama2 já está disponível"
fi

# 12. Criar estrutura de directórios
print_status "A criar directórios necessários..."
mkdir -p static/css static/js templates generated_images logs

# 13. Configurar variáveis de ambiente
print_status "A criar ficheiro de configuração..."
if [ ! -f ".env" ]; then
    cat > .env <<EOF
# Configuração da LLM Pessoal
OLLAMA_HOST=http://localhost:11434
STABLE_DIFFUSION_MODEL=runwayml/stable-diffusion-v1-5
DEVICE=auto
WSL_OPTIMIZATION=true
LOG_LEVEL=INFO
MAX_TOKENS=2048
PORT=8000
HOST=0.0.0.0
EOF
    print_success "Ficheiro .env criado"
fi

# 14. Criar script de inicialização
print_status "A criar script de inicialização..."
cat > start_llm.sh <<'EOF'
#!/bin/bash
# Script para iniciar a LLM Pessoal

# Activar ambiente virtual
source venv/bin/activate

# Verificar se Ollama está a correr
if ! pgrep -x "ollama" > /dev/null; then
    echo "A iniciar Ollama..."
    ollama serve &
    sleep 5
fi

# Iniciar a aplicação
echo "A iniciar LLM Pessoal..."
python app.py
EOF

chmod +x start_llm.sh

# 15. Criar script de actualização
cat > update_llm.sh <<'EOF'
#!/bin/bash
# Script para actualizar a LLM Pessoal

echo "A actualizar LLM Pessoal..."

# Activar ambiente virtual
source venv/bin/activate

# Actualizar dependências
pip install --upgrade -r requirements.txt

# Actualizar modelos Ollama
ollama pull llama2

echo "Actualização concluída!"
EOF

chmod +x update_llm.sh

# 16. Optimizações para WSL
print_status "A aplicar optimizações para WSL..."

# Configurar swap se necessário
SWAP_SIZE=$(free -m | grep Swap | awk '{print $2}')
if [ "$SWAP_SIZE" -lt 4096 ]; then
    print_warning "Swap insuficiente detectado ($SWAP_SIZE MB). Recomenda-se pelo menos 4GB."
    print_status "Para criar swap: sudo fallocate -l 4G /swapfile && sudo chmod 600 /swapfile && sudo mkswap /swapfile && sudo swapon /swapfile"
fi

# 17. Testar instalação
print_status "A testar instalação..."

# Testar Python
if python -c "import fastapi, torch, diffusers, ollama" 2>/dev/null; then
    print_success "Dependências Python importadas com sucesso"
else
    print_error "Erro ao importar dependências Python"
    exit 1
fi

# Testar Ollama
if curl -s http://localhost:11434/api/tags >/dev/null; then
    print_success "Ollama está a responder"
else
    print_warning "Ollama pode não estar completamente iniciado. Tente novamente em alguns segundos."
fi

# 18. Informações finais
print_success "Instalação concluída com sucesso!"
echo ""
echo "==============================================="
echo "🎉 LLM Pessoal instalada no WSL!"
echo "==============================================="
echo ""
echo "Para iniciar a aplicação:"
echo "  ./start_llm.sh"
echo ""
echo "A aplicação estará disponível em:"
echo "  http://localhost:8000"
echo ""
echo "Para actualizar:"
echo "  ./update_llm.sh"
echo ""
echo "Modelos Ollama disponíveis:"
ollama list 2>/dev/null || echo "  Execute 'ollama list' após o Ollama iniciar completamente"
echo ""
echo "Notas importantes:"
echo "  - Para GPU: configure GPU passthrough no WSL2"
echo "  - Para modelos maiores: considere aumentar a RAM/swap"
echo "  - O primeiro arranque pode ser lento devido ao download dos modelos"
echo ""
print_success "Instalação completa! Divirta-se com a sua LLM pessoal! 🚀" 