# -*- coding: utf-8 -*-
"""
Configurações da LLM Pessoal
Centraliza todas as configurações da aplicação
"""

import os
from pathlib import Path
from typing import Optional, Dict, List, Any


class Settings:
    """Configurações principais da aplicação"""

    # Informações da aplicação
    APP_NAME: str = "LLM Pessoal"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = ("Assistente Inteligente Local com "
                            "Ollama e Stable Diffusion")

    # Configurações do servidor
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8001"))
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    RELOAD: bool = os.getenv("RELOAD", "false").lower() == "true"

    # Configurações do Ollama
    OLLAMA_HOST: str = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    OLLAMA_TIMEOUT: int = int(os.getenv("OLLAMA_TIMEOUT", "300"))
    DEFAULT_MODEL: str = os.getenv("DEFAULT_MODEL", "llama3.2:latest")
    MAX_TOKENS: int = int(os.getenv("MAX_TOKENS", "2048"))

    # Configurações do Stable Diffusion
    STABLE_DIFFUSION_MODEL: str = os.getenv(
        "STABLE_DIFFUSION_MODEL",
        "runwayml/stable-diffusion-v1-5"
    )
    DEVICE: str = os.getenv("DEVICE", "auto")  # auto, cuda, cpu
    ENABLE_MEMORY_EFFICIENT_ATTENTION: bool = True
    ENABLE_VAE_SLICING: bool = True

    # Configurações de diretórios
    BASE_DIR: Path = Path(__file__).parent
    STATIC_DIR: Path = BASE_DIR / "static"
    TEMPLATES_DIR: Path = BASE_DIR / "templates"
    GENERATED_IMAGES_DIR: Path = BASE_DIR / "generated_images"
    LOGS_DIR: Path = BASE_DIR / "logs"

    # Configurações de logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: Optional[str] = str(LOGS_DIR / "app.log")
    LOG_FORMAT: str = ("%(asctime)s - %(name)s - "
                       "%(levelname)s - %(message)s")

    # Configurações Windows/WSL
    WSL_OPTIMIZATION: bool = (
        os.getenv("WSL_OPTIMIZATION", "true").lower() == "true"
    )

    # Configurações de segurança
    CORS_ORIGINS: List[str] = ["*"]  # Em produção, especificar domínios
    MAX_CHAT_HISTORY: int = int(os.getenv("MAX_CHAT_HISTORY", "50"))
    MAX_IMAGE_SIZE: int = int(os.getenv("MAX_IMAGE_SIZE", "1024"))

    # Configurações de performance
    WORKERS: int = int(os.getenv("WORKERS", "1"))
    KEEP_ALIVE: int = int(os.getenv("KEEP_ALIVE", "5"))

    def __post_init__(self):
        """Criar diretórios necessários"""
        for directory in [
            self.STATIC_DIR,
            self.TEMPLATES_DIR,
            self.GENERATED_IMAGES_DIR,
            self.LOGS_DIR
        ]:
            directory.mkdir(exist_ok=True)


# Instância global das configurações
settings = Settings()


# Configurações específicas para modelos Ollama
OLLAMA_MODELS: Dict[str, Dict[str, Any]] = {
    "llama3.2:latest": {
        "name": "LLaMA 3.2",
        "description": "Modelo mais recente, excelente performance",
        "ram_required": "4GB",
        "recommended": True
    },
    "phi3:mini": {
        "name": "Phi-3 Mini",
        "description": "Modelo compacto e rápido",
        "ram_required": "2GB",
        "recommended": True
    },
    "llama3.1:latest": {
        "name": "LLaMA 3.1",
        "description": "Versão anterior estável",
        "ram_required": "4GB",
        "recommended": True
    },
    "mistral:latest": {
        "name": "Mistral 7B",
        "description": "Modelo rápido e eficiente",
        "ram_required": "4GB",
        "recommended": False
    },
    "codellama:latest": {
        "name": "Code Llama",
        "description": "Especializado em programação",
        "ram_required": "4GB",
        "recommended": False
    }
}


# Configurações para Stable Diffusion
STABLE_DIFFUSION_MODELS: Dict[str, Dict[str, Any]] = {
    "runwayml/stable-diffusion-v1-5": {
        "name": "Stable Diffusion 1.5",
        "description": "Modelo padrão, boa qualidade geral",
        "vram_required": "4GB",
        "recommended": True
    },
    "stabilityai/stable-diffusion-2-1": {
        "name": "Stable Diffusion 2.1",
        "description": "Versão mais recente, melhor qualidade",
        "vram_required": "6GB",
        "recommended": False
    },
    "runwayml/stable-diffusion-inpainting": {
        "name": "SD Inpainting",
        "description": "Especializado em edição de imagens",
        "vram_required": "4GB",
        "recommended": False
    }
}


# Configurações para diferentes ambientes
ENVIRONMENT_CONFIGS: Dict[str, Dict[str, Any]] = {
    "development": {
        "DEBUG": True,
        "RELOAD": True,
        "LOG_LEVEL": "DEBUG",
        "HOST": "127.0.0.1"
    },
    "production": {
        "DEBUG": False,
        "RELOAD": False,
        "LOG_LEVEL": "INFO",
        "HOST": "0.0.0.0",
        "WORKERS": 4
    },
    "windows": {
        "WSL_OPTIMIZATION": False,
        "HOST": "127.0.0.1",
        "DEVICE": "auto"
    }
}


def get_device_info() -> Dict[str, Any]:
    """Obter informações sobre o dispositivo disponível"""
    try:
        import torch
        if torch.cuda.is_available():
            device = "cuda"
            gpu_name = torch.cuda.get_device_name(0)
            gpu_props = torch.cuda.get_device_properties(0)
            gpu_memory = gpu_props.total_memory // (1024**3)
            return {
                "device": device,
                "gpu_name": gpu_name,
                "gpu_memory_gb": gpu_memory,
                "cuda_available": True
            }
    except ImportError:
        pass

    return {
        "device": "cpu",
        "gpu_name": None,
        "gpu_memory_gb": 0,
        "cuda_available": False
    }


def validate_config() -> List[str]:
    """Validar configuração atual"""
    issues = []

    # Verificar diretórios
    for directory in [settings.STATIC_DIR, settings.TEMPLATES_DIR]:
        if not directory.exists():
            issues.append(f"Diretório não encontrado: {directory}")

    # Verificar Ollama
    try:
        import requests
        url = f"{settings.OLLAMA_HOST}/api/tags"
        response = requests.get(url, timeout=5)
        if response.status_code != 200:
            issues.append("Ollama não está acessível")
    except Exception as e:
        issues.append(f"Erro ao conectar ao Ollama: {e}")

    # Verificar PyTorch
    try:
        import torch
        if settings.DEVICE == "cuda" and not torch.cuda.is_available():
            issues.append("CUDA solicitado mas não disponível")
    except ImportError:
        issues.append("PyTorch não está instalado")

    return issues


def get_config_summary() -> Dict[str, Any]:
    """Obter resumo da configuração"""
    return {
        "app": {
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "description": settings.APP_DESCRIPTION
        },
        "server": {
            "host": settings.HOST,
            "port": settings.PORT,
            "debug": settings.DEBUG
        },
        "ollama": {
            "host": settings.OLLAMA_HOST,
            "default_model": settings.DEFAULT_MODEL,
            "max_tokens": settings.MAX_TOKENS
        },
        "stable_diffusion": {
            "model": settings.STABLE_DIFFUSION_MODEL,
            "device": settings.DEVICE
        },
        "paths": {
            "base": str(settings.BASE_DIR),
            "static": str(settings.STATIC_DIR),
            "templates": str(settings.TEMPLATES_DIR),
            "images": str(settings.GENERATED_IMAGES_DIR),
            "logs": str(settings.LOGS_DIR)
        }
    }


def main():
    """Teste das configurações"""
    print(f"🔧 {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"📁 Diretório base: {settings.BASE_DIR}")
    print(f"🌐 Servidor: {settings.HOST}:{settings.PORT}")
    print(f"🤖 Ollama: {settings.OLLAMA_HOST}")
    print(f"🎨 Stable Diffusion: {settings.STABLE_DIFFUSION_MODEL}")
    print(f"💻 Dispositivo: {settings.DEVICE}")

    print("\n🔍 Informações do dispositivo:")
    device_info = get_device_info()
    for key, value in device_info.items():
        print(f"  {key}: {value}")

    print("\n✅ Validação da configuração:")
    issues = validate_config()
    if issues:
        for issue in issues:
            print(f"  ❌ {issue}")
    else:
        print("  ✅ Configuração válida!")

    print("\n📋 Resumo da configuração:")
    summary = get_config_summary()
    for section, data in summary.items():
        print(f"  {section.upper()}:")
        for key, value in data.items():
            print(f"    {key}: {value}")


if __name__ == "__main__":
    main() 