# 🚀 Enhanced LLM Platform - NetworkChuck Style AI Hub

Uma aplicação web **muito potente** para IA local e em nuvem, inspirada no tutorial do [NetworkChuck](https://youtu.be/Wjrdr0NU4Sk). Esta é uma plataforma completa de IA que conecta múltiplos provedores através de uma interface unificada com controle total sobre usuários, orçamentos e monitoramento.

---

## ✨ Funcionalidades Principais

### 🎯 **Seguindo os Passos do NetworkChuck:**
- **Multiple AI Providers**: OpenAI, Anthropic (Claude), Google (Gemini), Groq, Ollama
- **LiteLLM Integration**: Proxy inteligente para conectar todos os provedores
- **Budget Control**: Sistema de orçamento por usuário com alertas
- **User Management**: Roles, permissions, grupos e monitoramento
- **Real-time Monitoring**: Analytics completas de uso e custos
- **Multi-Model Comparison**: Compare respostas lado a lado
- **Local + Cloud**: Ollama local + APIs cloud em uma interface

### 🔥 **Funcionalidades Avançadas:**
- **Streaming Responses**: Respostas em tempo real
- **Chat Sessions**: Histórico persistente de conversas
- **Usage Analytics**: Dashboards com métricas detalhadas
- **Role-based Access**: Admin, Premium, Standard, Basic
- **Guardrails**: Sistema de prompts e limitações personalizáveis
- **Export/Import**: Backup de conversas em JSON
- **API Gateway**: LiteLLM como proxy para todas as APIs
- **Cost Tracking**: Monitoramento preciso de custos por token

---

## 🏗️ Arquitetura

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Flask App     │────│    LiteLLM      │────│  AI Providers   │
│   (Port 5000)   │    │   (Port 4000)   │    │  (OpenAI, etc)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌─────────────────┐              │
         └──────────────│     Redis       │──────────────┘
                        │   (Port 6379)   │
                        └─────────────────┘
                                 │
                        ┌─────────────────┐
                        │    Ollama       │──────┐
                        │  (Port 11434)   │      │
                        └─────────────────┘      │
                                 │               │
                   ┌─────────────────┐  ┌─────────────────┐
                   │   Open WebUI    │  │ Stable Diffusion│
                   │   (Port 8080)   │  │   (Port 7860)   │
                   └─────────────────┘  └─────────────────┘
                                 │
                        ┌─────────────────┐
                        │  Whisper API    │
                        │   (Port 5001)   │
                        └─────────────────┘
```

---

## 🚀 Instalação Rápida (Docker)

### 1. Clone o repositório
```bash
git clone <repository-url>
cd LLM-Sharkcoders
```

### 2. Configure as variáveis de ambiente
```bash
cp config.env.example config.env
# Edite config.env com suas API keys
```

### 3. Execute com Docker Compose
```bash
# Executar todos os serviços (requer GPU para melhor performance)
docker-compose up -d

# Ou executar apenas serviços específicos
docker-compose up -d app litellm ollama redis          # Serviços básicos
docker-compose up -d open-webui                        # Interface Ollama
docker-compose up -d stable-diffusion-webui            # Geração de imagens
docker-compose up -d whisper-api                       # Transcrição de áudio
```

**Nota**: Os serviços que requerem GPU (Ollama, Stable Diffusion, Whisper) estão configurados para deteção automática de GPU NVIDIA. Se não tiver GPU, remova ou comente as secções `deploy.resources` no `docker-compose.yml`.

### 4. Acesse a aplicação
- **App Principal**: http://localhost:5000
- **LiteLLM UI**: http://localhost:4000 (admin/admin123)
- **Ollama**: http://localhost:11434
- **Open WebUI**: http://localhost:8080 (Interface moderna para Ollama)
- **Stable Diffusion WebUI**: http://localhost:7860 (Geração de imagens)
- **Whisper API**: http://localhost:5001 (Transcrição de áudio)

---

## 🔧 Configuração Manual

### 1. Instale as dependências
```bash
python -m pip install -r requirements.txt
```

### 2. Configure o ambiente
```bash
# Copie e edite o arquivo de configuração
cp config.env.example .env
```

### 3. Configure os serviços externos

#### **Redis** (Para cache e rate limiting)
```bash
# Ubuntu/Debian
sudo apt install redis-server
redis-server

# Docker
docker run -d --name redis -p 6379:6379 redis:alpine
```

#### **Ollama** (Para modelos locais)
```bash
# Instale Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Baixe modelos
ollama pull llama3
ollama pull mistral
ollama pull codellama
```

#### **LiteLLM** (Proxy para APIs)
```bash
# Clone e configure LiteLLM
git clone https://github.com/BerriAI/litellm.git
cd litellm
pip install -e .

# Execute com nossa configuração
litellm --config ../litellm_config.yaml --port 4000
```

### 4. Execute a aplicação
```bash
python app.py
```

---

## 👥 Sistema de Usuários

### **Roles e Permissões:**

| Role | Budget Máximo | Modelos Disponíveis | Permissões Especiais |
|------|---------------|---------------------|---------------------|
| **Admin** | $1000/mês | Todos | Gerenciar usuários, ver todos os chats |
| **Premium** | $100/mês | OpenAI, Claude, Gemini, Ollama | Acesso completo aos modelos |
| **Standard** | $20/mês | OpenAI, Ollama | Modelos básicos |
| **Basic** | $0/mês | Apenas Ollama | Apenas modelos locais |

### **Usuário Admin Padrão:**
- **Username**: `admin`
- **Password**: `admin123` 
- **⚠️ MUDE A SENHA EM PRODUÇÃO!**

---

## 🎮 Como Usar

### **1. Dashboard Principal**
- Visualize seu uso atual e orçamento
- Acesse estatísticas de modelos utilizados
- Navegue entre funcionalidades

### **2. Chat Individual**
- Escolha qualquer modelo disponível
- Streaming de respostas em tempo real
- Histórico de conversas salvo automaticamente

### **3. Comparação Multi-Modelo**
- Teste a mesma pergunta em vários modelos
- Compare qualidade e velocidade
- Analise custos por resposta

### **4. Painel Admin** (Apenas admins)
- Gerencie usuários e permissões
- Configure orçamentos e limites
- Monitore uso do sistema
- Visualize analytics detalhadas

---

## 💰 Controle de Custos

### **Como Funciona:**
1. **APIs por Token**: Pague apenas pelo que usar
2. **Budgets por Usuário**: Limite gastos mensais
3. **Alertas Automáticos**: Avisos quando próximo ao limite
4. **Analytics Detalhadas**: Veja exatamente onde gasta

### **Custos Aproximados:**
- **GPT-4o**: ~$5-15/mês para uso moderado
- **Claude 3.5**: ~$3-10/mês para uso moderado  
- **Gemini**: ~$1-5/mês para uso moderado
- **Ollama**: $0 (local, apenas custos de energia)

---

## 🎨 **Serviços Adicionais de IA**

### **🌐 Open WebUI (Porta 8080)**
Interface moderna e intuitiva para interagir com modelos Ollama:
- **Funcionalidades**: Chat avançado, gestão de modelos, interface responsiva
- **Acesso**: http://localhost:8080
- **Conectividade**: Integração direta com Ollama

### **🎭 Stable Diffusion WebUI (Porta 7860)**
Geração de imagens com IA usando Stable Diffusion:
- **Funcionalidades**: Text-to-image, image-to-image, inpainting
- **Acesso**: http://localhost:7860
- **Requisitos**: GPU NVIDIA recomendada (configuração automática)
- **Modelos**: Download automático na primeira execução

### **🗣️ Whisper API (Porta 5001)**
Transcrição de áudio para texto usando Whisper.cpp:
- **Endpoint**: `POST /transcribe`
- **Formato**: Envio de ficheiros de áudio via form-data
- **Modelo**: Base English (pode ser alterado)
- **Exemplo de uso**:
```bash
curl -X POST -F "audio=@audio_file.wav" http://localhost:5001/transcribe
```

## 🔒 Segurança e Privacidade

### **Funcionalidades de Segurança:**
- **Guardrails**: Prompts de sistema para filtrar conteúdo
- **Rate Limiting**: Prevenção de spam e abuso
- **Role-based Access**: Controle granular de permissões
- **Chat Monitoring**: Admins podem monitorar conversas (se habilitado)
- **Budget Limits**: Prevenção de gastos excessivos

### **Dados Locais:**
- Modelos Ollama rodam 100% localmente
- Stable Diffusion executa localmente
- Whisper API processa áudio localmente
- Histórico de chats armazenado localmente
- Controle total sobre seus dados

---

## 🛠️ Comandos CLI

```bash
# Criar usuário admin
python app.py create-admin

# Resetar uso mensal de todos os usuários
python app.py reset-usage

# Listar todos os usuários
python app.py list-users

# Migrar banco de dados
flask db upgrade
```

---

## 📊 Monitoramento

### **Métricas Disponíveis:**
- Requests por dia/usuário/modelo
- Custos detalhados por provider
- Tempo de resposta médio
- Taxa de sucesso/erro
- Uso de tokens por modelo
- Padrões de uso por hora

### **Dashboards:**
- **User Dashboard**: Estatísticas pessoais
- **Admin Dashboard**: Visão geral do sistema
- **Analytics**: Métricas detalhadas e gráficos

---

## 🔧 Configuração Avançada

### **Variáveis de Ambiente Importantes:**
```bash
# AI Providers
OPENAI_API_KEY=your-key
ANTHROPIC_API_KEY=your-key
GOOGLE_API_KEY=your-key
GROQ_API_KEY=your-key

# LiteLLM
LITELLM_MASTER_KEY=your-master-key
LITELLM_SALT_KEY=your-salt-key

# Application
DEFAULT_USER_BUDGET=20.00
MAX_CHAT_HISTORY=100
ENABLE_USAGE_TRACKING=True
```

### **Personalização de Modelos:**
Edite `app/config.py` para:
- Adicionar novos modelos
- Ajustar custos por token
- Modificar permissões de roles
- Configurar limites de budget

---

## 🚨 Troubleshooting

### **Problemas Comuns:**

**1. LiteLLM não conecta:**
```bash
# Verifique se as API keys estão configuradas
docker-compose logs litellm
```

**2. Ollama models não carregam:**
```bash
# Baixe os modelos manualmente
ollama pull llama3
ollama list
```

**3. Redis connection error:**
```bash
# Verifique se Redis está rodando
docker-compose logs redis
redis-cli ping
```

**4. Budget não atualiza:**
```bash
# Reset manual se necessário
python app.py reset-usage
```

---

## 🎯 Roadmap

### **Próximas Funcionalidades:**
- [ ] **Voice Chat**: Integração com Whisper e TTS
- [ ] **Document Upload**: RAG com PDFs e documentos
- [ ] **Custom Models**: Fine-tuning de modelos locais
- [ ] **Teams**: Workspaces colaborativos
- [ ] **API Keys**: API externa para integração
- [ ] **Plugins**: Sistema de extensões
- [ ] **Mobile App**: React Native companion

---

## 🏆 Créditos

### **Inspirado por:**
- **[NetworkChuck](https://www.youtube.com/@NetworkChuck)** - Tutorial original e arquitetura
- **[LiteLLM](https://github.com/BerriAI/litellm)** - Proxy inteligente para APIs
- **[Ollama](https://ollama.ai/)** - Execução local de modelos
- **[Open WebUI](https://github.com/open-webui/open-webui)** - Interface inspiração

### **Tecnologias:**
- **Flask**: Framework web Python
- **SQLAlchemy**: ORM para banco de dados
- **Redis**: Cache e rate limiting
- **Docker**: Containerização
- **Chart.js**: Gráficos e analytics
- **Font Awesome**: Ícones

---

## 📝 Licença

MIT License - Veja [LICENSE](LICENSE) para detalhes.

---

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request

---

## 💬 Suporte

- **Issues**: Reporte bugs e solicite features
- **Discussions**: Tire dúvidas e compartilhe ideias
- **Discord**: [Link do servidor] (se houver)

---

**🎉 Agora você tem seu próprio AI Hub seguindo o estilo NetworkChuck! Divirta-se explorando o poder da IA! 🚀** 