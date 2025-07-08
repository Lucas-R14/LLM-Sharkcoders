#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Servidor principal da LLM Pessoal
Integra Ollama, Stable Diffusion e WebUI
Otimizado para Docker e Windows
"""

import json
import os
import logging
import time
from pathlib import Path
from typing import AsyncGenerator

import requests
import torch
import uvicorn
from fastapi import FastAPI, HTTPException, Request, File, UploadFile, Form
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Configurar variáveis de ambiente
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
os.environ["HF_HUB_DISABLE_SYMLINKS"] = "1"
os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "max_split_size_mb:128"

# Import Diffusers e PIL após configurar ambiente
try:
    from diffusers.pipelines.stable_diffusion.pipeline_stable_diffusion import (  # noqa: E501
        StableDiffusionPipeline
    )
    from PIL import Image
    diffusers_available = True
except ImportError:
    StableDiffusionPipeline = None
    Image = None
    diffusers_available = False

# Import Whisper e outros serviços
try:
    from whisper_service import whisper_service
    from health_check import health_checker
    from resource_manager import resource_manager
    whisper_available = True
except ImportError:
    whisper_service = None
    health_checker = None
    resource_manager = None
    whisper_available = False

# Configurar logging
logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class Config:
    """Configurações da aplicação com suporte Docker"""
    
    # Configurações do servidor
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", "8001"))
    
    # Configurações Ollama
    OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "300"))
    
    # Configurações Stable Diffusion
    STABLE_DIFFUSION_MODEL = os.getenv(
        "STABLE_DIFFUSION_MODEL", 
        "runwayml/stable-diffusion-v1-5"
    )
    
    # Configurações de dispositivo
    DEVICE = os.getenv("DEVICE", "auto")
    if DEVICE == "auto":
        DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
    
    # Outras configurações
    MAX_TOKENS = int(os.getenv("MAX_TOKENS", "2048"))
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"
    WSL_OPTIMIZATION = os.getenv("WSL_OPTIMIZATION", "true").lower() == "true"


config = Config()

# Modelos conhecidos com prioridade atualizada
KNOWN_MODELS = [
    {
        "name": "llama3.2:latest",
        "display": "LLaMA 3.2 (Recomendado)",
        "recommended": True
    },
    {
        "name": "phi3:mini",
        "display": "Phi-3 Mini (Rápido)",
        "recommended": True
    },
    {
        "name": "llama3.1:latest",
        "display": "LLaMA 3.1",
        "recommended": True
    },
    {
        "name": "mistral:latest",
        "display": "Mistral 7B",
        "recommended": False
    },
    {
        "name": "codellama:latest",
        "display": "Code Llama",
        "recommended": False
    }
]


class ChatRequest(BaseModel):
    """Modelo para requisição de chat"""
    message: str
    model: str = "llama3.2:latest"
    stream: bool = True


class ImageRequest(BaseModel):
    """Modelo para requisição de imagem"""
    prompt: str
    negative_prompt: str = ""
    width: int = 512
    height: int = 512
    num_inference_steps: int = 20
    guidance_scale: float = 7.5


class OllamaClient:
    """Cliente HTTP otimizado para Ollama em Docker"""

    def __init__(self, host: str):
        self.host = host.rstrip('/')
        self.session = requests.Session()

    def test_connection(self) -> bool:
        """Testar conexão com Ollama (com retry para Docker)"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                url = f"{self.host}/api/version"
                response = self.session.get(url, timeout=10)
                if response.status_code == 200:
                    logger.info(f"✅ Ollama conectado: {response.json()}")
                    return True
            except Exception as e:
                logger.warning(f"Tentativa {attempt + 1}/{max_retries}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2)
        return False

    def list_local_models(self):
        """Listar modelos instalados"""
        try:
            url = f"{self.host}/api/tags"
            response = self.session.get(url, timeout=30)
            if response.status_code == 200:
                data = response.json()
                models = [model["name"] for model in data.get("models", [])]
                logger.info(f"Modelos disponíveis: {models}")
                return models
            return []
        except Exception as e:
            logger.error(f"Erro ao listar modelos: {e}")
            return []

    def pull_model(self, model: str):
        """Instalar modelo"""
        try:
            logger.info(f"🤖 Instalando modelo: {model}")
            url = f"{self.host}/api/pull"
            payload = {"name": model}
            response = self.session.post(url, json=payload, timeout=900)
            success = response.status_code == 200
            if success:
                logger.info(f"✅ Modelo {model} instalado")
            else:
                logger.error(f"❌ Falha ao instalar {model}")
            return success
        except Exception as e:
            logger.error(f"Erro ao instalar modelo {model}: {e}")
            return False

    def generate_stream(self, model: str, prompt: str):
        """Gerar resposta em streaming"""
        url = f"{self.host}/api/generate"
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": True,
            "options": {
                "temperature": 0.7,
                "top_p": 0.9,
                "top_k": 40,
                "num_predict": config.MAX_TOKENS
            }
        }

        try:
            response = self.session.post(
                url, json=payload, stream=True, timeout=config.OLLAMA_TIMEOUT
            )
            response.raise_for_status()

            for line in response.iter_lines(decode_unicode=True):
                if line.strip():
                    try:
                        data = json.loads(line)
                        yield data
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            logger.error(f"Erro no streaming: {e}")
            yield {"error": str(e)}


def load_stable_diffusion():
    """Carregar Stable Diffusion otimizado para Docker"""
    if not diffusers_available:
        logger.warning("❌ Diffusers não disponível")
        return None

    try:
        logger.info("🎨 Carregando Stable Diffusion...")
        device = config.DEVICE
        dtype = torch.float16 if device == "cuda" else torch.float32

        # Carregar pipeline com configurações otimizadas
        pipeline = StableDiffusionPipeline.from_pretrained(  # type: ignore
            config.STABLE_DIFFUSION_MODEL,
            torch_dtype=dtype,
            safety_checker=None,
            requires_safety_checker=False,
            cache_dir="/app/cache/huggingface",
            local_files_only=False
        )

        pipeline = pipeline.to(device)

        # Aplicar otimizações específicas do dispositivo
        if device == "cuda":
            try:
                pipeline.enable_memory_efficient_attention()
                pipeline.enable_vae_slicing()
                pipeline.enable_sequential_cpu_offload()
                logger.info("✅ Otimizações CUDA aplicadas")
            except Exception as e:
                logger.warning(f"Algumas otimizações CUDA falharam: {e}")
        else:
            try:
                pipeline.enable_vae_slicing()
                logger.info("✅ Otimizações CPU aplicadas")
            except Exception as e:
                logger.warning(f"Otimizações CPU falharam: {e}")

        logger.info(f"✅ Stable Diffusion pronto no {device}")
        return pipeline

    except Exception as e:
        logger.error(f"❌ Erro no Stable Diffusion: {e}")
        return None


class LLMPersonal:
    """Aplicação principal otimizada para Docker"""

    def __init__(self):
        self.app = FastAPI(
            title="LLM Pessoal",
            description="Assistente Local com Docker",
            version="1.0.0"
        )
        self.ollama_client = None
        self.sd_pipeline = None
        self.chat_history = []
        self.available_models = []

        self.setup_cors()
        self.setup_directories()
        self.setup_routes()
        self.app.add_event_handler("startup", self.initialize_models)

    def setup_cors(self):
        """Configurar CORS para Docker"""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    def setup_directories(self):
        """Criar diretórios necessários"""
        dirs = [
            "static", "templates", "generated_images", "logs",
            "cache/huggingface", "cache/transformers"
        ]
        for directory in dirs:
            Path(directory).mkdir(parents=True, exist_ok=True)
        logger.info("📁 Diretórios criados")

    async def initialize_models(self):
        """Inicializar modelos com retry para Docker"""
        try:
            # Inicializar Ollama com retry
            self.ollama_client = OllamaClient(config.OLLAMA_HOST)

            if self.ollama_client.test_connection():
                local_models = self.ollama_client.list_local_models()

                # Verificar modelos disponíveis
                for model in KNOWN_MODELS:
                    if any(model["name"] in local for local in local_models):
                        self.available_models.append(model)

                # Se não há modelos, usar lista padrão
                if not self.available_models:
                    logger.info("Usando modelos padrão")
                    self.available_models = KNOWN_MODELS[:3]
            else:
                logger.warning("❌ Ollama offline - usando modelos padrão")
                self.available_models = KNOWN_MODELS[:3]

            # Inicializar Stable Diffusion em background
            try:
                self.sd_pipeline = load_stable_diffusion()
            except Exception as e:
                logger.error(f"Stable Diffusion falhou: {e}")
                self.sd_pipeline = None

        except Exception as e:
            logger.error(f"Erro na inicialização: {e}")

    def setup_routes(self):
        """Configurar todas as rotas da API"""
        # Arquivos estáticos
        self.app.mount(
            "/static", StaticFiles(directory="static"), name="static"
        )
        self.app.mount(
            "/images",
            StaticFiles(directory="generated_images"),
            name="images"
        )

        templates = Jinja2Templates(directory="templates")

        @self.app.get("/", response_class=HTMLResponse)
        async def home(request: Request):
            return templates.TemplateResponse(
                "index.html", {"request": request}
            )

        @self.app.get("/api/models")
        async def get_models():
            """Retornar lista de modelos disponíveis"""
            if self.available_models:
                models = [m["name"] for m in self.available_models]
            else:
                models = ["llama3.2:latest", "phi3:mini"]
            return {"models": models}

        @self.app.get("/api/models/detailed")
        async def get_detailed_models():
            """Retornar informações detalhadas dos modelos"""
            models = self.available_models or KNOWN_MODELS[:3]
            return {"models": models}

        @self.app.post("/api/chat")
        async def chat(request: ChatRequest):
            """Endpoint principal de chat"""
            try:
                if (not self.ollama_client or  
                        not self.ollama_client.test_connection()):
                    raise HTTPException(
                        status_code=503,
                        detail="Ollama indisponível - verifique container"
                    )

                # Adicionar ao histórico
                self.chat_history.append({
                    "role": "user",
                    "content": request.message
                })

                if request.stream:
                    return StreamingResponse(
                        self.stream_response(request.message, request.model),
                        media_type="text/plain"
                    )
                else:
                    # Modo não-streaming
                    prompt = f"Utilizador: {request.message}\nAssistente: "
                    full_response = ""

                    for chunk in self.ollama_client.generate_stream(
                        request.model, prompt
                    ):
                        if "response" in chunk:
                            full_response += chunk["response"]
                        if chunk.get("done", False):
                            break

                    self.chat_history.append({
                        "role": "assistant",
                        "content": full_response
                    })
                    return {"response": full_response}

            except Exception as e:
                logger.error(f"Erro no chat: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/api/generate-image")
        async def generate_image(request: ImageRequest):
            """Endpoint de geração de imagens"""
            try:
                if not self.sd_pipeline:
                    raise HTTPException(
                        status_code=503,
                        detail="Stable Diffusion indisponível"
                    )

                logger.info(f"🎨 Gerando: {request.prompt[:50]}...")
                
                # Gerar imagem com método correto
                output = self.sd_pipeline(  # type: ignore
                    prompt=request.prompt,
                    negative_prompt=request.negative_prompt,
                    num_inference_steps=request.num_inference_steps,
                    guidance_scale=request.guidance_scale
                )
                result = output.images[0]  # type: ignore

                # Salvar
                timestamp = int(time.time())
                filename = f"generated_{timestamp}.png"
                filepath = Path("generated_images") / filename
                result.save(filepath)

                logger.info(f"✅ Imagem salva: {filename}")
                return {
                    "success": True,
                    "image_url": f"/images/{filename}",
                    "filename": filename
                }

            except Exception as e:
                logger.error(f"Erro na geração de imagem: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/api/clear-history")
        async def clear_history():
            """Limpar histórico de chat"""
            self.chat_history.clear()
            return {"success": True, "message": "Histórico limpo"}

        @self.app.get("/api/status")
        async def get_status():
            """Status completo da aplicação"""
            ollama_ok = (
                self.ollama_client and
                self.ollama_client.test_connection()
            )
            
            # Informações do sistema
            gpu_info = "N/A"
            if torch.cuda.is_available():
                gpu_info = torch.cuda.get_device_name(0)
                
            return {
                "ollama": ollama_ok,
                "stable_diffusion": self.sd_pipeline is not None,
                "device": config.DEVICE,
                "gpu_info": gpu_info,
                "chat_history_length": len(self.chat_history),
                "available_models": len(self.available_models),
                "diffusers_available": diffusers_available,
                "version": "1.0.0-docker"
            }

        @self.app.get("/api/health")
        async def health_check():
            """Health check para Docker"""
            if health_checker:
                return await health_checker.run_all_checks()
            return {"status": "healthy", "timestamp": time.time()}

        # ===============================
        # ENDPOINTS WHISPER
        # ===============================
        
        @self.app.post("/api/whisper/transcribe")
        async def transcribe_audio(
            audio: UploadFile = File(...),
            language: str = Form("pt")
        ):
            """
            Endpoint para transcrição de áudio.
            
            Args:
                audio: Ficheiro de áudio
                language: Código do idioma (pt, en, es, etc.)
            """
            if not whisper_service:
                raise HTTPException(status_code=503, detail="Whisper não disponível")
            
            try:
                # Verificar tipo de ficheiro
                if not audio.content_type.startswith('audio/'):
                    raise HTTPException(status_code=400, detail="Ficheiro deve ser de áudio")
                
                # Ler dados do áudio
                audio_data = await audio.read()
                
                # Reservar recursos
                if not resource_manager.reserve_whisper():
                    raise HTTPException(status_code=503, detail="Recursos não disponíveis")
                
                try:
                    # Transcrever
                    result = whisper_service.transcribe(audio_data, language)
                    
                    if "error" in result:
                        raise HTTPException(status_code=500, detail=result["error"])
                    
                    return JSONResponse(content=result)
                    
                finally:
                    # Libertar recursos
                    resource_manager.release_whisper()
                    
            except Exception as e:
                logger.error(f"Erro na transcrição: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/api/whisper/status")
        async def get_whisper_status():
            """Retorna o status do serviço Whisper."""
            if not whisper_service:
                return {"loaded": False, "error": "Whisper não disponível"}
            return whisper_service.get_status()

        @self.app.post("/api/whisper/load")
        async def load_whisper_model(model_name: str = "openai/whisper-small"):
            """Carrega um modelo Whisper específico."""
            if not whisper_service:
                raise HTTPException(status_code=503, detail="Whisper não disponível")
            
            try:
                whisper_service.model_name = model_name
                whisper_service.is_loaded = False
                
                success = whisper_service.load_model()
                
                if success:
                    return {"message": f"Modelo {model_name} carregado com sucesso"}
                else:
                    raise HTTPException(status_code=500, detail="Falha ao carregar modelo")
                    
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/api/chat/voice")
        async def chat_with_voice(
            audio: UploadFile = File(...),
            model: str = Form("llama3.2:latest"),
            language: str = Form("pt")
        ):
            """
            Endpoint combinado: transcreve áudio e envia para chat.
            
            Args:
                audio: Ficheiro de áudio
                model: Modelo LLM a utilizar
                language: Idioma para transcrição
            """
            if not whisper_service:
                raise HTTPException(status_code=503, detail="Whisper não disponível")
            
            try:
                # Verificar Ollama
                if not self.ollama_client or not self.ollama_client.test_connection():
                    raise HTTPException(status_code=503, detail="Ollama indisponível")
                
                # Transcrever áudio
                audio_data = await audio.read()
                transcription_result = whisper_service.transcribe(audio_data, language)
                
                if "error" in transcription_result:
                    raise HTTPException(status_code=500, detail=transcription_result["error"])
                
                transcribed_text = transcription_result["text"]
                
                # Enviar para chat (reutilizar lógica existente)
                prompt = f"Utilizador: {transcribed_text}\nAssistente: "
                chat_response = ""
                
                for chunk in self.ollama_client.generate_stream(model, prompt):
                    if "response" in chunk:
                        chat_response += chunk["response"]
                    if chunk.get("done", False):
                        break
                
                return {
                    "transcription": transcription_result,
                    "chat_response": chat_response,
                    "original_text": transcribed_text
                }
                
            except Exception as e:
                logger.error(f"Erro no chat por voz: {e}")
                raise HTTPException(status_code=500, detail=str(e))

    async def stream_response(
        self, message: str, model: str
    ) -> AsyncGenerator[str, None]:
        """Stream de chat otimizado"""
        try:
            if not self.ollama_client:
                error_data = json.dumps({"error": "Ollama indisponível"})
                yield f"data: {error_data}\n\n"
                return

            prompt = f"Utilizador: {message}\nAssistente: "
            full_response = ""

            for chunk in self.ollama_client.generate_stream(model, prompt):
                if "error" in chunk:
                    error_data = json.dumps({"error": chunk["error"]})
                    yield f"data: {error_data}\n\n"
                    return

                if "response" in chunk:
                    content = chunk["response"]
                    full_response += content
                    content_data = json.dumps({"content": content})
                    yield f"data: {content_data}\n\n"

                if chunk.get("done", False):
                    break

            # Adicionar ao histórico
            self.chat_history.append({
                "role": "assistant",
                "content": full_response
            })
            done_data = json.dumps({"done": True})
            yield f"data: {done_data}\n\n"

        except Exception as e:
            error_msg = f"Erro no chat: {str(e)}"
            logger.error(error_msg)
            error_data = json.dumps({"error": error_msg})
            yield f"data: {error_data}\n\n"


def main():
    """Função principal otimizada para Docker"""
    logger.info("🐳 Iniciando LLM Pessoal no Docker...")
    logger.info("📊 Configurações:")
    logger.info(f"   Host: {config.HOST}:{config.PORT}")
    logger.info(f"   Ollama: {config.OLLAMA_HOST}")
    logger.info(f"   Dispositivo: {config.DEVICE}")
    logger.info(f"   Debug: {config.DEBUG}")
    logger.info(f"   Diffusers: {diffusers_available}")

    app_instance = LLMPersonal()

    uvicorn.run(
        app_instance.app,
        host=config.HOST,
        port=config.PORT,
        reload=config.DEBUG,
        access_log=True,
        log_level="info"
    )


if __name__ == "__main__":
    main() 