#!/bin/bash
# docker-entrypoint.sh
# Script de inicialização para container Docker da LLM Pessoal

set -e

echo "🐳 Iniciando LLM Pessoal Docker..."

# Criar diretórios se não existirem
mkdir -p /app/static /app/templates /app/generated_images /app/logs
mkdir -p /app/cache/huggingface /app/cache/transformers

# Aguardar Ollama estar disponível
echo "⏳ Aguardando Ollama..."
while ! curl -f "${OLLAMA_HOST:-http://ollama:11434}/api/version" >/dev/null 2>&1; do
    echo "   Ollama não disponível, aguardando 5s..."
    sleep 5
done
echo "✅ Ollama conectado!"

# Verificar se PyTorch funciona
echo "🔍 Verificando PyTorch..."
python -c "
import torch
print(f'PyTorch: {torch.__version__}')
print(f'CUDA disponível: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'GPU: {torch.cuda.get_device_name(0)}')
    print(f'VRAM: {torch.cuda.get_device_properties(0).total_memory // (1024**3)}GB')
else:
    print('Usando CPU')
"

# Verificar Diffusers
echo "🎨 Verificando Stable Diffusion..."
python -c "
try:
    from diffusers.pipelines.stable_diffusion.pipeline_stable_diffusion import StableDiffusionPipeline
    print('✅ Diffusers disponível')
except ImportError as e:
    print(f'❌ Diffusers indisponível: {e}')
"

# Baixar modelos em background se necessário
if [ "${AUTO_DOWNLOAD_MODELS:-true}" = "true" ]; then
    echo "🤖 Verificando modelos..."
    (
        sleep 10  # Dar tempo para a app iniciar
        curl -f "${OLLAMA_HOST:-http://ollama:11434}/api/tags" >/dev/null 2>&1 && {
            echo "Verificando se modelos existem..."
            MODELS=$(curl -s "${OLLAMA_HOST:-http://ollama:11434}/api/tags" | python -c "
import json, sys
data = json.load(sys.stdin)
models = [m['name'] for m in data.get('models', [])]
print(' '.join(models))
")
            if [[ ! "$MODELS" =~ "llama3.2" ]]; then
                echo "📥 Baixando llama3.2:latest..."
                curl -s -X POST "${OLLAMA_HOST:-http://ollama:11434}/api/pull" \
                    -H "Content-Type: application/json" \
                    -d '{"name": "llama3.2:latest"}' >/dev/null
            fi
            if [[ ! "$MODELS" =~ "phi3" ]]; then
                echo "📥 Baixando phi3:mini..."
                curl -s -X POST "${OLLAMA_HOST:-http://ollama:11434}/api/pull" \
                    -H "Content-Type: application/json" \
                    -d '{"name": "phi3:mini"}' >/dev/null
            fi
        }
    ) &
fi

echo "🚀 Iniciando aplicação..."

# Executar comando passado ou aplicação padrão
if [ $# -eq 0 ]; then
    exec python app.py
else
    exec "$@"
fi 