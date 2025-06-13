# 🚀 Quick Start Guide - Enhanced LLM Platform

Get your **very powerful** AI hub running in minutes following NetworkChuck's approach!

## 🎯 Super Quick Setup (Docker)

```bash
# 1. Clone the repository
git clone <repository-url>
cd LLM-Sharkcoders

# 2. Run the setup script
python setup.py

# 3. You're done! 🎉
```

The setup script will:
- ✅ Check requirements
- ✅ Generate secure secrets  
- ✅ Create directories
- ✅ Configure environment
- ✅ Start all services with Docker
- ✅ Setup admin user

## 🌐 Access Your AI Hub

- **Main App**: http://localhost:5000
- **LiteLLM Admin**: http://localhost:4000
- **Ollama**: http://localhost:11434

**Default Login:**
- Username: `admin`
- Password: `admin123`
- ⚠️ **Change this immediately!**

## 🔑 Adding AI Provider Keys

1. Edit `config.env` file:
   ```bash
   # Add your API keys
   OPENAI_API_KEY=sk-your-openai-key
   ANTHROPIC_API_KEY=sk-your-anthropic-key
   GOOGLE_API_KEY=your-google-key
   GROQ_API_KEY=gsk_your-groq-key
   ```

2. Restart services:
   ```bash
   docker-compose restart
   ```

## 🎮 What You Can Do Now

### 1. **Single Model Chat**
- Go to "AI Chat"
- Select any available model
- Start chatting with streaming responses

### 2. **Multi-Model Comparison** 
- Go to "Multi-Model"
- Select multiple models
- Ask the same question to compare responses

### 3. **User Management** (Admin)
- Create users with different roles
- Set budgets and permissions
- Monitor usage and conversations

### 4. **Budget Control**
- Set monthly spending limits
- Track usage by model/provider
- Get alerts when approaching limits

## 👥 User Roles

| Role | Budget | Models | Features |
|------|--------|--------|----------|
| **Admin** | $1000 | All | Manage users, see all chats |
| **Premium** | $100 | OpenAI, Claude, Gemini, Ollama | Full access |
| **Standard** | $20 | OpenAI, Ollama | Basic models |
| **Basic** | $0 | Ollama only | Local models only |

## 💰 Cost Management

### API Costs (Pay-per-use):
- **GPT-4o**: ~$0.005 per 1k tokens
- **Claude 3.5**: ~$0.003 per 1k tokens  
- **Gemini Pro**: ~$0.0035 per 1k tokens
- **Ollama**: $0 (runs locally)

### Typical Monthly Costs:
- **Light user**: $2-5/month
- **Moderate user**: $5-15/month
- **Heavy user**: $15-50/month

## 🛠️ Manual Setup (Without Docker)

If you prefer manual setup:

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start Redis
redis-server

# 3. Start Ollama
ollama serve

# 4. Download models
ollama pull llama3
ollama pull mistral

# 5. Start LiteLLM
litellm --config litellm_config.yaml --port 4000

# 6. Start Flask app
python app.py
```

## 🔧 Troubleshooting

### Common Issues:

**LiteLLM not working?**
```bash
# Check logs
docker-compose logs litellm

# Make sure API keys are set
cat config.env | grep API_KEY
```

**Ollama models not loading?**
```bash
# Check available models
ollama list

# Pull missing models
ollama pull llama3
```

**Can't access the app?**
```bash
# Check if services are running
docker-compose ps

# Restart everything
docker-compose down && docker-compose up -d
```

**Database errors?**
```bash
# Reset database
rm app/data/enhanced_users.db
docker-compose restart app
```

## 🎯 Next Steps

1. **Add API Keys**: Get keys from AI providers
2. **Create Users**: Set up team members with appropriate roles
3. **Set Budgets**: Configure spending limits
4. **Start Chatting**: Test different models and compare responses
5. **Monitor Usage**: Check the analytics dashboard

## 📚 More Information

- **Full Documentation**: See [README.md](README.md)
- **NetworkChuck Tutorial**: https://youtu.be/Wjrdr0NU4Sk
- **LiteLLM Docs**: https://docs.litellm.ai
- **Ollama Models**: https://ollama.ai/library

## 🆘 Getting Help

Having issues? 
1. Check this guide first
2. Look at the full README.md
3. Check Docker logs: `docker-compose logs`
4. Open an issue on GitHub

## 🎉 You're Ready!

Your **powerful AI hub** is now running! You have:
- ✅ Multiple AI providers in one interface
- ✅ Budget control and user management  
- ✅ Local + cloud models
- ✅ Usage analytics and monitoring
- ✅ Multi-model comparison
- ✅ Streaming responses

**Start exploring the power of AI! 🚀** 