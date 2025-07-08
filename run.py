#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Inicialização do LLM Pessoal
Execute este arquivo para iniciar a aplicação
"""

import sys
import subprocess
import os
from pathlib import Path

def check_python_version():
    """Verificar se a versão do Python é adequada"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 ou superior é necessário!")
        print(f"Versão atual: {sys.version}")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detectado")
    return True

def check_ollama():
    """Verificar se o Ollama está instalado e funcionando"""
    try:
        result = subprocess.run(
            ["ollama", "list"], 
            capture_output=True, 
            text=True, 
            timeout=10
        )
        if result.returncode == 0:
            print("✅ Ollama está instalado e funcionando")
            return True
        else:
            print("⚠️  Ollama instalado mas não está funcionando")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("❌ Ollama não encontrado!")
        print("📥 Instale o Ollama em: https://ollama.com/")
        return False

def install_requirements():
    """Instalar dependências necessárias"""
    requirements_file = Path("requirements.txt")
    
    if not requirements_file.exists():
        print("📝 Criando arquivo requirements.txt...")
        with open(requirements_file, 'w', encoding='utf-8') as f:
            f.write("""fastapi==0.104.1
uvicorn[standard]==0.24.0
requests==2.31.0
torch==2.1.1
torchvision==0.16.1
diffusers==0.23.1
transformers==4.35.2
accelerate==0.24.1
jinja2==3.1.2
pydantic==2.5.0
pillow==10.1.0
""")
    
    print("📦 Instalando dependências...")
    try:
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ], check=True, capture_output=True, text=True)
        print("✅ Dependências instaladas com sucesso!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao instalar dependências: {e}")
        print(f"Saída: {e.stdout}")
        print(f"Erro: {e.stderr}")
        return False

def check_directories():
    """Criar diretórios necessários"""
    directories = ["static", "templates", "generated_images", "logs"]
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
    print("✅ Diretórios verificados/criados")

def main():
    """Função principal"""
    print("🚀 Iniciando LLM Pessoal...")
    print("=" * 50)
    
    # Verificações
    if not check_python_version():
        return 1
    
    check_directories()
    
    # Verificar Ollama
    ollama_ok = check_ollama()
    if not ollama_ok:
        print("\n⚠️  AVISO: Ollama não está funcionando.")
        print("A aplicação irá iniciar, mas o chat pode não funcionar.")
        print("Para instalar o Ollama:")
        print("1. Vá para https://ollama.com/")
        print("2. Baixe e instale o Ollama")
        print("3. Execute: ollama pull llama3.2")
        print()
    
    # Instalar dependências
    if not install_requirements():
        return 1
    
    print("\n🎉 Configuração completa!")
    print("🌐 Iniciando servidor web...")
    print("=" * 50)
    
    # Iniciar aplicação
    try:
        from app import main as app_main
        app_main()
    except ImportError as e:
        print(f"❌ Erro ao importar aplicação: {e}")
        print("Tentando executar diretamente...")
        os.system(f"{sys.executable} app.py")
    except KeyboardInterrupt:
        print("\n👋 Aplicação encerrada pelo utilizador")
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 