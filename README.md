# LLM Pessoal 🤖

**Assistente Inteligente Local com IA Generativa**

Uma aplicação web completa que integra **modelos de linguagem local** (via Ollama) e **geração de imagens** (Stable Diffusion) em uma interface moderna e intuitiva. Tudo funciona localmente, garantindo total privacidade dos seus dados.

## 🌟 Funcionalidades Principais

### 💬 Chat Inteligente
- **Modelos Locais**: LLaMA 3.2, Phi-3 Mini, Mistral, Code Llama
- **Conversação Natural**: Interface de chat em tempo real
- **Streaming**: Respostas em tempo real com efeito de digitação
- **Histórico**: Mantém conversas organizadas
- **Múltiplos Modelos**: Troque entre modelos sem reiniciar

### 🎨 Geração de Imagens
- **Stable Diffusion**: Geração de imagens de alta qualidade
- **Controles Avançados**: Ajuste de parâmetros (passos, escala, tamanho)
- **Prompt Negativo**: Especifique o que não deve aparecer
- **Download**: Salve imagens geradas localmente
- **Múltiplos Formatos**: 512x512, 768x768, 1024x1024

### 🖥️ Interface Web Moderna
- **Design Responsivo**: Funciona em desktop e mobile
- **Tabs Organizadas**: Chat, Imagens e Configurações
- **Status em Tempo Real**: Monitoramento de serviços
- **Interface Intuitiva**: Fácil de usar para iniciantes

### 🔒 Privacidade Total
- **100% Local**: Nenhum dado enviado para a internet
- **Sem Telemetria**: Não coleta informações de uso
- **Dados Seguros**: Tudo fica no seu computador

## 🏗️ Arquitetura e Tecnologias

### Backend
- **FastAPI**: Framework web moderno e rápido
- **Uvicorn**: Servidor ASGI de alta performance
- **Pydantic**: Validação de dados e serialização
- **Jinja2**: Templates HTML dinâmicos

### IA e Machine Learning
- **Ollama**: Servidor local para modelos LLM
- **PyTorch**: Framework de deep learning
- **Diffusers**: Pipeline Stable Diffusion
- **Transformers**: Biblioteca Hugging Face
- **Accelerate**: Otimizações de performance

### Frontend
- **HTML5/CSS3**: Interface moderna e responsiva
- **JavaScript ES6+**: Interatividade e streaming
- **Font Awesome**: Ícones profissionais
- **CSS Grid/Flexbox**: Layout adaptativo

### Infraestrutura
- **Docker**: Containerização completa
- **Docker Compose**: Orquestração de serviços
- **Nginx**: Proxy reverso (opcional)
- **Volumes Persistentes**: Cache e dados

## 📋 Pré-requisitos do Sistema

### Mínimos
- **Sistema Operativo**: Windows 10+, macOS 10.15+, Ubuntu 18.04+
- **RAM**: 8GB (16GB recomendado)
- **Armazenamento**: 10GB livres
- **Python**: 3.8+ (3.10+ recomendado)

### Recomendados
- **GPU NVIDIA**: RTX 2060+ com 6GB+ VRAM
- **RAM**: 16GB+ para modelos maiores
- **SSD**: Para melhor performance de cache
- **CPU**: 4+ cores para processamento

### Software Obrigatório
- **Ollama**: [ollama.com](https://ollama.com)
- **Docker**: [docker.com](https://docker.com) (opcional)
- **Git**: Para clonar o repositório

## 🚀 Instalação e Configuração

### Método 1: Docker (Recomendado)

```bash
# 1. Clone o repositório
git clone <url-do-repositorio>
cd LLM-pessoal

# 2. Inicie com Docker Compose
docker-compose up -d

# 3. Acesse a aplicação
# Abra: http://localhost:8001
```

**Vantagens do Docker:**
- ✅ Instalação automática de dependências
- ✅ Configuração isolada
- ✅ Funciona em qualquer sistema
- ✅ Baixa modelos automaticamente

### Método 2: Instalação Local

```bash
# 1. Clone o repositório
git clone <url-do-repositorio>
cd LLM-pessoal

# 2. Crie ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows

# 3. Instale dependências
pip install -r requirements.txt

# 4. Instale Ollama
# Windows/Mac: Baixe de https://ollama.com/
# Linux:
curl -fsSL https://ollama.com/install.sh | sh

# 5. Baixe um modelo
ollama pull llama3.2:latest

# 6. Execute a aplicação
python app.py
```

### Método 3: Script de Inicialização

```bash
# Execute o script que faz tudo automaticamente
python run.py
```

## 📱 Guia de Utilização Passo a Passo

### 1. Primeira Execução

1. **Inicie a aplicação** (Docker ou local)
2. **Aguarde a inicialização** (pode demorar 1-2 minutos)
3. **Verifique o status** na aba Configurações
4. **Baixe um modelo** se necessário

### 2. Chat com IA

#### Interface Principal
- **Seletor de Modelo**: Escolha entre modelos disponíveis
- **Área de Chat**: Visualize conversas em tempo real
- **Campo de Mensagem**: Digite suas perguntas
- **Botão Enviar**: Ou pressione Enter

#### Fluxo de Conversa
1. **Selecione um modelo** no dropdown
2. **Digite sua mensagem** no campo de texto
3. **Pressione Enter** ou clique em "Enviar"
4. **Aguarde a resposta** (aparece em streaming)
5. **Continue a conversa** naturalmente

#### Dicas de Uso
- **Prompts claros**: Seja específico nas suas perguntas
- **Contexto**: O modelo lembra da conversa atual
- **Limpar histórico**: Use o botão de lixeira quando necessário
- **Trocar modelo**: Mude entre modelos sem perder contexto

### 3. Geração de Imagens

#### Interface de Imagens
- **Prompt Principal**: Descreva a imagem desejada
- **Prompt Negativo**: Especifique o que não deve aparecer
- **Controles de Tamanho**: 512x512, 768x768, 1024x1024
- **Parâmetros Avançados**: Passos e escala de orientação

#### Fluxo de Geração
1. **Vá para a aba "Geração de Imagens"**
2. **Descreva a imagem** no campo principal
3. **Adicione prompt negativo** (opcional)
4. **Ajuste parâmetros** se necessário:
   - **Passos**: 10-50 (mais = melhor qualidade, mais lento)
   - **Escala**: 1-20 (mais = mais fiel ao prompt)
5. **Clique em "Gerar Imagem"**
6. **Aguarde a geração** (30-120 segundos)
7. **Faça download** da imagem gerada

#### Dicas para Imagens
- **Prompts detalhados**: "Um gato siamês sentado em um jardim japonês ao pôr do sol"
- **Prompts negativos**: "borrão, baixa qualidade, distorção"
- **Tamanhos**: 512x512 é mais rápido, 1024x1024 é mais detalhado
- **Passos**: 20-30 é um bom equilíbrio

### 4. Configurações e Monitoramento

#### Aba Configurações
- **Status dos Serviços**: Ollama e Stable Diffusion
- **Informações do Sistema**: Dispositivo, memória, histórico
- **Ações**: Atualizar status, limpar histórico

#### Monitoramento
- **Verde**: Serviço funcionando
- **Vermelho**: Serviço com problema
- **Amarelo**: Serviço carregando

## 🔧 Configuração Avançada

### Modelos Suportados

| Modelo | Tamanho | RAM | Velocidade | Qualidade | Uso Recomendado |
|--------|---------|-----|------------|-----------|------------------|
| `phi3:mini` | ~2GB | 4GB | ⚡⚡⚡ | ⭐⭐⭐ | Chat rápido |
| `llama3.2:latest` | ~4GB | 8GB | ⚡⚡ | ⭐⭐⭐⭐ | Uso geral |
| `llama3.1:latest` | ~4GB | 8GB | ⚡⚡ | ⭐⭐⭐⭐ | Uso geral |
| `mistral:latest` | ~4GB | 8GB | ⚡⚡ | ⭐⭐⭐⭐ | Chat avançado |
| `codellama:latest` | ~4GB | 8GB | ⚡⚡ | ⭐⭐⭐⭐ | Programação |

### Variáveis de Ambiente

Crie um arquivo `.env` para personalizar:

```env
# Servidor
HOST=0.0.0.0
PORT=8001
DEBUG=false
RELOAD=false

# Ollama
OLLAMA_HOST=http://localhost:11434
OLLAMA_TIMEOUT=300
DEFAULT_MODEL=llama3.2:latest
MAX_TOKENS=2048

# Stable Diffusion
STABLE_DIFFUSION_MODEL=runwayml/stable-diffusion-v1-5
DEVICE=auto  # auto, cuda, cpu

# Performance
WORKERS=1
KEEP_ALIVE=5
LOG_LEVEL=INFO

# Windows/WSL
WSL_OPTIMIZATION=true
```

### Configuração GPU

#### NVIDIA CUDA
```bash
# Verificar CUDA
python -c "import torch; print(torch.cuda.is_available())"

# Instalar PyTorch com CUDA
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

#### Configuração Automática
A aplicação detecta automaticamente:
- **GPU NVIDIA**: Usa CUDA se disponível
- **GPU AMD**: Usa ROCm (se instalado)
- **CPU**: Fallback automático

### Otimizações de Performance

#### Para GPU
```env
DEVICE=cuda
ENABLE_MEMORY_EFFICIENT_ATTENTION=true
ENABLE_VAE_SLICING=true
```

#### Para CPU
```env
DEVICE=cpu
ENABLE_MEMORY_EFFICIENT_ATTENTION=false
```

## 🐛 Resolução de Problemas

### Problemas Comuns

#### Ollama não conecta
```bash
# Verificar se está rodando
ollama list

# Reiniciar serviço
ollama serve

# Verificar porta
netstat -an | grep 11434
```

#### Erro de memória
- **Solução**: Use modelos menores (`phi3:mini`)
- **Prevenção**: Feche outras aplicações
- **Configuração**: Use CPU em vez de GPU

#### Stable Diffusion lento
- **Reduzir tamanho**: Use 512x512
- **Menos passos**: 10-15 em vez de 20-30
- **Usar CPU**: Se VRAM insuficiente

#### Porta em uso
```bash
# Mudar porta
export PORT=8080
python app.py
```

### Logs e Debug

#### Verificar Logs
```bash
# Logs da aplicação
tail -f logs/app.log

# Logs do Docker
docker-compose logs -f llm-app
```

#### Modo Debug
```env
DEBUG=true
LOG_LEVEL=DEBUG
```

### Problemas Específicos

#### Windows
- **WSL**: Ative otimizações no `.env`
- **Antivírus**: Adicione exceções para Python
- **Firewall**: Permita Python e Ollama

#### Linux
- **Permissões**: `chmod +x run.py`
- **Dependências**: `sudo apt install python3-venv`

#### macOS
- **Homebrew**: `brew install ollama`
- **Permissões**: Permita Python no Security

## 📁 Estrutura do Projeto

```
LLM-pessoal/
├── app.py                 # Servidor principal FastAPI
├── config.py              # Configurações centralizadas
├── run.py                 # Script de inicialização
├── requirements.txt       # Dependências Python
├── docker-compose.yml     # Configuração Docker
├── Dockerfile            # Imagem Docker
├── .env                  # Variáveis de ambiente (criar)
├── static/               # Arquivos estáticos
│   ├── css/
│   │   └── style.css     # Estilos da interface
│   └── js/
│       └── app.js        # JavaScript da aplicação
├── templates/            # Templates HTML
│   └── index.html        # Interface principal
├── generated_images/     # Imagens geradas
├── logs/                # Logs da aplicação
├── cache/               # Cache de modelos
│   ├── huggingface/     # Cache HF
│   └── transformers/    # Cache Transformers
└── docker-data/         # Dados persistentes Docker
    ├── ollama/          # Modelos Ollama
    ├── huggingface/     # Cache HF
    └── transformers/    # Cache Transformers
```

## 🔄 Atualizações e Manutenção

### Atualizar Aplicação
```bash
# Backup (opcional)
cp -r generated_images/ backup_images/

# Atualizar código
git pull origin main

# Reinstalar dependências
pip install -r requirements.txt --upgrade

# Reiniciar
python app.py
```

### Atualizar Modelos
```bash
# Listar modelos
ollama list

# Atualizar modelo
ollama pull llama3.2:latest

# Remover modelo antigo
ollama rm llama3.1:latest
```

### Limpeza de Cache
```bash
# Limpar cache Python
pip cache purge

# Limpar cache HF
rm -rf cache/huggingface/*
rm -rf cache/transformers/*
```

## 🤝 Contribuições

### Como Contribuir
1. **Fork** o repositório
2. **Crie uma branch**: `git checkout -b feature/nova-funcionalidade`
3. **Commit**: `git commit -m 'Adiciona nova funcionalidade'`
4. **Push**: `git push origin feature/nova-funcionalidade`
5. **Pull Request**: Abra um PR com descrição detalhada

### Áreas para Contribuição
- **Novos modelos**: Adicionar suporte a outros LLMs
- **Interface**: Melhorias na UI/UX
- **Performance**: Otimizações de velocidade
- **Documentação**: Melhorar guias e exemplos
- **Testes**: Adicionar testes automatizados

## 📜 Licença

Este projeto está licenciado sob a **Licença MIT**. Veja o arquivo `LICENSE` para detalhes.

## 🆘 Suporte e Comunidade

### Canais de Ajuda
- **Issues GitHub**: Para bugs e problemas
- **Discussions**: Para perguntas e discussões
- **Wiki**: Documentação detalhada

### Informações de Debug
Ao reportar problemas, inclua:
- **Sistema Operativo**: Windows/Linux/macOS
- **Versão Python**: `python --version`
- **Logs**: Conteúdo de `logs/app.log`
- **Configuração**: Conteúdo do `.env`
- **Passos**: Como reproduzir o problema

## 🔮 Roadmap

### Próximas Funcionalidades
- [ ] **Voz**: Reconhecimento e síntese de voz
- [ ] **Múltiplos Usuários**: Sistema de contas
- [ ] **Plugins**: Sistema de extensões
- [ ] **API REST**: Endpoints para integração
- [ ] **Mobile App**: Aplicação nativa

### Melhorias Planejadas
- [ ] **Cache Inteligente**: Otimização de memória
- [ ] **Modelos Customizados**: Fine-tuning local
- [ ] **Interface Avançada**: Mais controles de imagem
- [ ] **Backup Automático**: Sistema de backup

---

**Desenvolvido com ❤️ para a comunidade portuguesa**

*Uma ferramenta poderosa para explorar IA local de forma segura e privada.* 