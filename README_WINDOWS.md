# �� LLM Pessoal - Guia Completo para Windows

## 🎉 INSTALAÇÃO COMPLETA! ✅

Parabéns! A sua **LLM Pessoal** está instalada e configurada no Windows. Esta é uma aplicação completa de IA local que combina chat inteligente e geração de imagens.

## 🚀 Como Iniciar

### Método 1: Script Batch (Recomendado)
```cmd
start_windows.bat
```

### Método 2: Script PowerShell
```powershell
.\start_windows.ps1
```

### Método 3: Manual
```cmd
venv\Scripts\python.exe app.py
```

## 🌐 Aceder à Aplicação

Abra o seu navegador e vá para: **http://localhost:8001**

## 📋 Funcionalidades Disponíveis

### 💬 Chat Inteligente
- ✅ **Interface moderna** de chat com streaming
- ✅ **Múltiplos modelos** (LLaMA 3.2, Phi-3, Mistral, Code Llama)
- ✅ **Histórico de conversação** persistente
- ✅ **Troca de modelos** em tempo real
- ⏳ **Modelos Ollama** (necessário download)

### 🎨 Geração de Imagens
- ✅ **Stable Diffusion** integrado
- ✅ **Controlos avançados** (dimensões, passos, guidance)
- ✅ **Prompt negativo** para melhor qualidade
- ✅ **Download de imagens** em alta resolução
- 💻 **Funciona com CPU** (mais lento mas funciona)

### ⚙️ Configurações e Monitoramento
- ✅ **Status em tempo real** dos serviços
- ✅ **Informações do sistema** (CPU, RAM, GPU)
- ✅ **Gestão de histórico** e limpeza
- ✅ **Logs detalhados** para troubleshooting

## 🦙 Configurar Modelos Ollama

Para o chat funcionar, precisa de baixar modelos:

### Modelos Recomendados (por ordem de prioridade)

```cmd
# 1. Modelo pequeno e rápido (recomendado para começar)
ollama pull phi3:mini

# 2. Modelo mais poderoso (precisa mais RAM)
ollama pull llama3.2:latest

# 3. Modelo especializado em código
ollama pull codellama:latest

# 4. Modelo rápido e eficiente
ollama pull mistral:latest
```

### Verificar Modelos Instalados
```cmd
ollama list
```

### Informações dos Modelos
```cmd
# Ver detalhes de um modelo
ollama show llama3.2:latest

# Ver uso de memória
ollama ps
```

## 💡 Guia de Utilização Detalhado

### Para Chat Inteligente

#### 1. Primeira Configuração
1. **Aguarde o download** de pelo menos um modelo Ollama
2. **Verifique o status** na aba Configurações
3. **Selecione um modelo** no dropdown

#### 2. Fluxo de Conversa
1. **Escolha o modelo** no seletor (ex: phi3:mini)
2. **Digite sua mensagem** no campo de texto
3. **Pressione Enter** ou clique em "Enviar"
4. **Aguarde a resposta** (aparece em streaming)
5. **Continue a conversa** naturalmente

#### 3. Dicas para Melhores Resultados
- **Seja específico**: "Explique como funciona a fotossíntese" vs "fotossíntese"
- **Use contexto**: O modelo lembra da conversa atual
- **Limpe histórico**: Use o botão de lixeira quando necessário
- **Troque modelos**: Experimente diferentes modelos para diferentes tarefas

### Para Geração de Imagens

#### 1. Interface de Imagens
- **Prompt Principal**: Descreva a imagem desejada
- **Prompt Negativo**: Especifique o que não deve aparecer
- **Controles de Tamanho**: 512x512, 768x768, 1024x1024
- **Parâmetros Avançados**: Passos e escala de orientação

#### 2. Fluxo de Geração
1. **Vá para a aba "Geração de Imagens"**
2. **Descreva a imagem** no campo principal
3. **Adicione prompt negativo** (opcional)
4. **Ajuste parâmetros** se necessário:
   - **Passos**: 10-50 (mais = melhor qualidade, mais lento)
   - **Escala**: 1-20 (mais = mais fiel ao prompt)
5. **Clique em "Gerar Imagem"**
6. **Aguarde a geração** (30-120 segundos)
7. **Faça download** da imagem gerada

#### 3. Dicas para Imagens
- **Prompts detalhados**: "Um gato siamês sentado em um jardim japonês ao pôr do sol, estilo realista"
- **Prompts negativos**: "borrão, baixa qualidade, distorção, arte digital"
- **Tamanhos**: 512x512 é mais rápido, 1024x1024 é mais detalhado
- **Passos**: 20-30 é um bom equilíbrio

## ⚡ Performance e Otimização

### Com CPU apenas
- **Chat**: Funciona bem com modelos pequenos (phi3:mini)
- **Imagens**: 2-5 minutos por imagem
- **RAM**: 8GB mínimo, 16GB recomendado

### Com GPU NVIDIA
- **Chat**: Muito mais rápido
- **Imagens**: 30-60 segundos por imagem
- **VRAM**: 4GB mínimo, 8GB+ recomendado

### Otimizações para Windows
```cmd
# Verificar se CUDA está disponível
python -c "import torch; print(torch.cuda.is_available())"

# Instalar PyTorch com CUDA (se necessário)
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

## 🔧 Resolução de Problemas

### Ollama não Responde
```cmd
# Verificar se está em execução
tasklist | findstr ollama

# Reiniciar se necessário
taskkill /f /im ollama.exe
ollama serve

# Verificar porta
netstat -an | findstr 11434
```

### Aplicação não Inicia
```cmd
# Verificar dependências
venv\Scripts\python.exe -c "import fastapi, torch, diffusers, ollama"

# Reinstalar se necessário
venv\Scripts\python.exe -m pip install -r requirements.txt

# Verificar logs
type logs\app.log
```

### Stable Diffusion Lento
- Use dimensões menores (512x512)
- Reduza passos de inferência para 10-15
- Considere uma GPU NVIDIA para melhor performance
- Feche outras aplicações para liberar RAM

### Erro de Memória
```cmd
# Verificar uso de memória
wmic OS get TotalVisibleMemorySize,FreePhysicalMemory

# Limpar cache Python
venv\Scripts\python.exe -m pip cache purge
```

### Porta em Uso
```cmd
# Verificar portas
netstat -an | findstr 8001

# Mudar porta (editar app.py ou usar variável)
set PORT=8080
venv\Scripts\python.exe app.py
```

## 📂 Estrutura dos Ficheiros

```
LLM pessoal/
├── 🎯 start_windows.bat      # Script de arranque (Batch)
├── 🎯 start_windows.ps1      # Script de arranque (PowerShell)
├── 📱 app.py                 # Aplicação principal
├── ⚙️ config.py              # Configurações
├── 📋 requirements.txt       # Dependências Python
├── 🌐 templates/             # Interface web
│   └── index.html           # Template principal
├── 🎨 static/                # CSS e JavaScript
│   ├── css/style.css        # Estilos
│   └── js/app.js           # JavaScript
├── 📸 generated_images/      # Imagens geradas
├── 📊 logs/                 # Logs da aplicação
└── 🗂️ venv/                 # Ambiente virtual Python
```

## 🆘 Suporte e Troubleshooting

### Verificações Básicas
1. **Verifique se todos os serviços estão a funcionar**
2. **Consulte esta documentação**
3. **Reinicie a aplicação**
4. **Verifique se tem espaço em disco suficiente**

### Logs e Debug
```cmd
# Ver logs da aplicação
type logs\app.log

# Ver logs em tempo real
powershell "Get-Content logs\app.log -Wait"

# Modo debug
set DEBUG=true
venv\Scripts\python.exe app.py
```

### Informações do Sistema
```cmd
# Verificar Python
venv\Scripts\python.exe --version

# Verificar PyTorch
venv\Scripts\python.exe -c "import torch; print(torch.__version__)"

# Verificar CUDA
venv\Scripts\python.exe -c "import torch; print(torch.cuda.is_available())"
```

## 🚀 Próximos Passos

### 1. Configuração Inicial
1. **Baixe modelos Ollama** para usar o chat
2. **Experimente gerar imagens** com Stable Diffusion
3. **Explore as configurações** para optimizar a performance
4. **Personalize prompts** para melhores resultados

### 2. Otimizações Avançadas
- **GPU NVIDIA**: Instale drivers CUDA para melhor performance
- **RAM**: Considere 16GB+ para modelos maiores
- **SSD**: Use SSD para melhor velocidade de cache
- **Antivírus**: Adicione exceções para Python e Ollama

### 3. Personalização
- **Modelos customizados**: Experimente diferentes modelos Ollama
- **Prompts**: Crie prompts personalizados para suas necessidades
- **Interface**: Personalize CSS se necessário
- **Configurações**: Ajuste parâmetros no config.py

## 🎯 Início Rápido

1. **Execute**: `start_windows.bat`
2. **Aguarde** a aplicação iniciar (1-2 minutos)
3. **Abra**: http://localhost:8001
4. **Baixe um modelo**: `ollama pull phi3:mini`
5. **Divirta-se!** 🎉

**✨ A sua LLM pessoal está pronta para usar! 🚀**

---

*Desenvolvido especificamente para Windows com otimizações nativas.* 