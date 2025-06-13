#!/usr/bin/env python3
"""
Enhanced LLM Platform Setup Script
Following NetworkChuck's AI Hub approach
"""

import os
import sys
import subprocess
import secrets
import shutil
from pathlib import Path

def print_banner():
    """Print setup banner"""
    print("""
🚀 Enhanced LLM Platform Setup - NetworkChuck Style
================================================

Setting up your powerful AI hub with multiple providers!
""")

def check_requirements():
    """Check if required tools are installed"""
    print("📋 Checking requirements...")
    
    requirements = {
        'python': 'python --version',
        'docker': 'docker --version',
        'docker-compose': 'docker-compose --version'
    }
    
    missing = []
    for tool, cmd in requirements.items():
        try:
            result = subprocess.run(cmd.split(), capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ {tool}: {result.stdout.strip()}")
            else:
                missing.append(tool)
        except FileNotFoundError:
            missing.append(tool)
    
    if missing:
        print(f"❌ Missing requirements: {', '.join(missing)}")
        print("\nPlease install the missing tools and run setup again.")
        sys.exit(1)
    
    print("✅ All requirements satisfied!\n")

def generate_secrets():
    """Generate secure secrets for the application"""
    print("🔐 Generating secure secrets...")
    
    secrets_config = {
        'SECRET_KEY': secrets.token_hex(32),
        'LITELLM_MASTER_KEY': f"sk-{secrets.token_hex(16)}",
        'LITELLM_SALT_KEY': f"sk-{secrets.token_hex(16)}",
        'JWT_SECRET_KEY': secrets.token_hex(32)
    }
    
    return secrets_config

def setup_environment():
    """Setup environment configuration"""
    print("⚙️  Setting up environment configuration...")
    
    # Generate secrets
    secrets_config = generate_secrets()
    
    # Read template
    if os.path.exists('config.env.example'):
        with open('config.env.example', 'r') as f:
            template = f.read()
    else:
        template = """# Database Configuration
DATABASE_URL=sqlite:///app/data/enhanced_users.db
SECRET_KEY=your-secret-key-here

# AI Provider API Keys
OPENAI_API_KEY=your-openai-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key
GOOGLE_API_KEY=your-google-api-key
GROQ_API_KEY=your-groq-api-key

# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_DEFAULT_MODEL=llama3

# LiteLLM Configuration
LITELLM_MASTER_KEY=your-litellm-master-key
LITELLM_SALT_KEY=your-litellm-salt-key
LITELLM_PORT=4000

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# Application Settings
FLASK_ENV=development
FLASK_DEBUG=True
MAX_CHAT_HISTORY=100
DEFAULT_USER_BUDGET=20.00
ENABLE_USAGE_TRACKING=True

# Security Settings
JWT_SECRET_KEY=your-jwt-secret-key
BCRYPT_LOG_ROUNDS=12
RATE_LIMIT_STORAGE_URL=redis://localhost:6379/1
"""
    
    # Replace secrets in template
    for key, value in secrets_config.items():
        template = template.replace(f'your-{key.lower().replace("_", "-")}-here', value)
        template = template.replace(f'your-{key.lower().replace("_", "-")}', value)
    
    # Write config file
    with open('config.env', 'w') as f:
        f.write(template)
    
    print("✅ Environment configuration created at config.env")
    print("🔑 Secure secrets generated automatically")
    print("⚠️  Remember to add your AI provider API keys to config.env")

def setup_directories():
    """Create necessary directories"""
    print("📁 Creating directories...")
    
    directories = [
        'app/data',
        'backups',
        'logs',
        'ssl'
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created: {directory}")

def get_api_keys():
    """Interactive API key setup"""
    print("\n🔑 API Keys Setup")
    print("=" * 40)
    print("Enter your AI provider API keys (press Enter to skip):")
    
    api_keys = {}
    
    providers = {
        'OPENAI_API_KEY': 'OpenAI (for GPT models)',
        'ANTHROPIC_API_KEY': 'Anthropic (for Claude models)', 
        'GOOGLE_API_KEY': 'Google (for Gemini models)',
        'GROQ_API_KEY': 'Groq (for fast Llama/Mixtral)'
    }
    
    for key, description in providers.items():
        while True:
            api_key = input(f"{description}: ").strip()
            if not api_key:
                print(f"⏭️  Skipping {description}")
                break
            elif api_key.startswith(('sk-', 'gsk_', 'AIza', 'xai-')):
                api_keys[key] = api_key
                print(f"✅ {description} configured")
                break
            else:
                print("❌ Invalid API key format. Please check and try again.")
    
    # Update config.env with API keys
    if api_keys and os.path.exists('config.env'):
        with open('config.env', 'r') as f:
            config = f.read()
        
        for key, value in api_keys.items():
            config = config.replace(f'{key}=your-{key.lower().replace("_", "-")}', f'{key}={value}')
        
        with open('config.env', 'w') as f:
            f.write(config)
        
        print(f"✅ Updated config.env with {len(api_keys)} API keys")

def setup_ollama():
    """Setup Ollama for local models"""
    print("\n🦙 Ollama Setup")
    print("=" * 40)
    
    install_ollama = input("Install Ollama for local models? (y/N): ").strip().lower()
    
    if install_ollama == 'y':
        print("📥 Installing Ollama...")
        
        if sys.platform.startswith('linux') or sys.platform.startswith('darwin'):
            # Linux/macOS
            try:
                subprocess.run(['curl', '-fsSL', 'https://ollama.ai/install.sh'], check=True)
                subprocess.run(['sh'], check=True)
                print("✅ Ollama installed!")
                
                # Download models
                models = ['llama3', 'mistral', 'codellama']
                for model in models:
                    download = input(f"Download {model} model? (y/N): ").strip().lower()
                    if download == 'y':
                        print(f"📥 Downloading {model}...")
                        subprocess.run(['ollama', 'pull', model], check=True)
                        print(f"✅ {model} downloaded!")
                        
            except subprocess.CalledProcessError:
                print("❌ Failed to install Ollama. Please install manually from https://ollama.ai")
        else:
            print("🪟 For Windows, please download Ollama from: https://ollama.ai/download")
    else:
        print("⏭️  Skipping Ollama installation")

def docker_setup():
    """Setup with Docker"""
    print("\n🐳 Docker Setup")
    print("=" * 40)
    
    use_docker = input("Use Docker for easy setup? (Y/n): ").strip().lower()
    
    if use_docker != 'n':
        print("🚀 Starting services with Docker Compose...")
        
        try:
            # Build and start services
            subprocess.run(['docker-compose', 'up', '-d', '--build'], check=True)
            print("✅ All services started!")
            
            print("\n🌐 Your AI Platform is ready!")
            print("=" * 40)
            print("🔗 Main App: http://localhost:5000")
            print("🔗 LiteLLM UI: http://localhost:4000")
            print("🔗 Ollama: http://localhost:11434")
            print("\n👤 Default admin login:")
            print("   Username: admin")
            print("   Password: admin123")
            print("   ⚠️  Please change this password after first login!")
            
        except subprocess.CalledProcessError:
            print("❌ Docker setup failed. You can try manual installation.")
            return False
    else:
        print("⏭️  Skipping Docker setup")
        return False
    
    return True

def manual_setup():
    """Manual setup without Docker"""
    print("\n🛠️  Manual Setup")
    print("=" * 40)
    
    print("📦 Installing Python dependencies...")
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], check=True)
        print("✅ Dependencies installed!")
    except subprocess.CalledProcessError:
        print("❌ Failed to install dependencies")
        return False
    
    print("\n🗄️  Database setup...")
    try:
        subprocess.run([sys.executable, 'app.py', 'create-admin'], check=True)
        print("✅ Database initialized!")
    except subprocess.CalledProcessError:
        print("⚠️  Database setup may need manual intervention")
    
    print("\n🎯 To start the application manually:")
    print("1. Start Redis: redis-server")
    print("2. Start Ollama: ollama serve")
    print("3. Start LiteLLM: litellm --config litellm_config.yaml --port 4000")
    print("4. Start Flask app: python app.py")
    
    return True

def main():
    """Main setup function"""
    print_banner()
    
    # Check requirements
    check_requirements()
    
    # Setup directories
    setup_directories()
    
    # Setup environment
    setup_environment()
    
    # Get API keys
    get_api_keys()
    
    # Setup Ollama
    setup_ollama()
    
    # Try Docker setup first
    docker_success = docker_setup()
    
    # If Docker failed, offer manual setup
    if not docker_success:
        manual_setup()
    
    print("\n🎉 Setup Complete!")
    print("=" * 40)
    print("📚 Next steps:")
    print("1. Add your AI provider API keys to config.env")
    print("2. Access the web interface and change admin password")
    print("3. Create additional users with different roles")
    print("4. Start chatting with multiple AI models!")
    print("\n📖 For more info, check the README.md")
    print("🆘 For support, open an issue on GitHub")
    print("\n🚀 Happy AI chatting!")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Setup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Setup failed with error: {e}")
        sys.exit(1) 