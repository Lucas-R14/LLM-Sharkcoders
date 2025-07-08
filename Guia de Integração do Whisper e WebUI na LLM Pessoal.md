
# Guia de Integração do Whisper e WebUI na LLM Pessoal

## 1. Planeamento da Arquitetura Melhorada

Este guia detalha a integração do modelo de reconhecimento de fala Whisper e uma interface de utilizador web (WebUI) dedicada ao seu projeto de LLM pessoal, com foco na melhoria da robustez da infraestrutura Docker. A arquitetura atual, baseada em FastAPI, Ollama e Stable Diffusion, será estendida para incorporar estas novas funcionalidades de forma eficiente e escalável.

### 1.1. Integração do Whisper

A integração do Whisper permitirá que a sua aplicação processe áudio (voz) e o transcreva para texto, que poderá então ser utilizado como entrada para os modelos de linguagem (LLMs). Existem várias abordagens para integrar o Whisper, mas a mais eficiente para este projeto será a utilização de uma biblioteca Python como `transformers` da Hugging Face, que já suporta o Whisper e pode ser facilmente integrada com o FastAPI. O processamento de áudio pode ser intensivo em recursos, especialmente para modelos maiores do Whisper, por isso, a gestão de hardware (GPU) será crucial.

**Pontos Chave:**
*   **Backend:** O FastAPI será o ponto de entrada para o áudio, recebendo-o e encaminhando-o para o módulo Whisper. O resultado da transcrição (texto) será então passado para o módulo de chat existente.
*   **Modelos Whisper:** Serão utilizados modelos pré-treinados do Whisper, com a possibilidade de escolher entre diferentes tamanhos (e.g., `tiny`, `base`, `small`, `medium`, `large`) dependendo dos requisitos de precisão e desempenho.
*   **Hardware:** A utilização de GPU será prioritária para o processamento do Whisper, aproveitando a configuração CUDA já existente para o Stable Diffusion. Será necessário garantir que o ambiente Docker tenha acesso adequado à GPU.
*   **Formato de Áudio:** A aplicação deverá suportar formatos de áudio comuns, como WAV ou MP3, e realizar a conversão necessária antes do processamento pelo Whisper.

### 1.2. Integração da WebUI

A WebUI será a interface através da qual os utilizadores interagirão com a funcionalidade de reconhecimento de fala. Esta interface será construída como parte do frontend existente, mantendo a consistência do design e a experiência do utilizador. Será adicionada uma nova secção ou aba dedicada à funcionalidade de voz.

**Pontos Chave:**
*   **Frontend:** A interface será desenvolvida utilizando HTML, CSS e JavaScript, seguindo a estrutura atual do projeto. Será necessário um componente para gravação de áudio (via microfone do navegador) ou upload de ficheiros de áudio.
*   **Comunicação:** A comunicação entre o frontend e o backend (FastAPI) para o envio de áudio e receção de transcrições será feita via requisições assíncronas (AJAX/Fetch API).
*   **Feedback Visual:** A WebUI deverá fornecer feedback visual ao utilizador durante o processo de gravação, upload e transcrição do áudio (e.g., indicadores de gravação, barras de progresso, mensagens de status).
*   **Reutilização de Componentes:** Sempre que possível, serão reutilizados os componentes de UI existentes para manter a consistência e acelerar o desenvolvimento.

### 1.3. Melhorias na Robustez do Docker

Para garantir que a adição do Whisper e da WebUI não comprometa a estabilidade e a facilidade de implantação, serão implementadas melhorias na configuração do Docker. O objetivo é tornar o ambiente mais resiliente a falhas, mais fácil de depurar e mais otimizado para o uso de recursos.

**Pontos Chave:**
*   **Imagens Docker Otimizadas:** Serão revistas as imagens Docker existentes para garantir que contêm apenas as dependências necessárias, reduzindo o tamanho da imagem e o tempo de construção. Será considerada a utilização de imagens multi-stage builds.
*   **Gestão de Recursos:** Serão configurados limites de recursos (CPU, memória) para os contêineres no `docker-compose.yml` para evitar que um serviço consuma todos os recursos do sistema.
*   **Monitoramento e Logs:** Será aprimorada a recolha e visualização de logs para facilitar a depuração de problemas. Será explorada a integração com ferramentas de monitoramento se necessário.
*   **Volumes Persistentes:** Será garantida a persistência de dados importantes, como modelos do Whisper e cache, através de volumes Docker, evitando downloads repetidos e perda de dados.
*   **Redes Docker:** Será revista a configuração de rede para garantir uma comunicação eficiente e segura entre os contêineres (FastAPI, Ollama, etc.).
*   **Saúde dos Contêineres:** Serão adicionadas verificações de saúde (health checks) aos contêineres para que o Docker possa detetar e reiniciar automaticamente serviços que falharam.

Este planeamento servirá como base para as próximas fases de implementação, garantindo uma abordagem estruturada e eficiente para a integração das novas funcionalidades.



## 2. Guia de Implementação do Whisper

A integração do Whisper no seu projeto de LLM pessoal permitirá adicionar capacidades de reconhecimento de fala, transformando áudio em texto que pode ser processado pelos modelos de linguagem existentes. Esta secção fornece um guia detalhado para implementar esta funcionalidade de forma robusta e eficiente.

### 2.1. Instalação e Configuração das Dependências

O primeiro passo para integrar o Whisper é instalar as dependências necessárias. O Whisper pode ser utilizado através da biblioteca `transformers` da Hugging Face, que oferece uma interface Python simples e eficiente. Além disso, será necessário instalar bibliotecas para processamento de áudio.

**Dependências Principais:**

Para adicionar ao seu `requirements.txt`, inclua as seguintes dependências:

```
transformers>=4.30.0
torch>=2.0.0
torchaudio>=2.0.0
librosa>=0.10.0
soundfile>=0.12.0
pydub>=0.25.0
ffmpeg-python>=0.2.0
```

A biblioteca `transformers` fornece acesso aos modelos Whisper pré-treinados, enquanto `torch` e `torchaudio` são necessários para o processamento de tensores e áudio. A `librosa` é uma biblioteca poderosa para análise de áudio, `soundfile` permite ler e escrever ficheiros de áudio, `pydub` facilita a manipulação de áudio, e `ffmpeg-python` é necessário para conversão entre formatos de áudio.

**Configuração do Sistema:**

Para garantir que o FFmpeg está disponível no sistema (necessário para processamento de áudio), adicione ao seu `Dockerfile`:

```dockerfile
# Instalar FFmpeg para processamento de áudio
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*
```

### 2.2. Implementação do Módulo Whisper

Crie um novo ficheiro `whisper_service.py` no diretório raiz do projeto para encapsular toda a lógica relacionada com o Whisper:

```python
import torch
import torchaudio
import librosa
import numpy as np
from transformers import WhisperProcessor, WhisperForConditionalGeneration
from typing import Optional, Union
import logging
import os
from pathlib import Path
import tempfile
from pydub import AudioSegment
import io

logger = logging.getLogger(__name__)

class WhisperService:
    """
    Serviço para reconhecimento de fala usando Whisper.
    Suporta múltiplos modelos e formatos de áudio.
    """
    
    def __init__(self, model_name: str = "openai/whisper-small", device: str = "auto"):
        """
        Inicializa o serviço Whisper.
        
        Args:
            model_name: Nome do modelo Whisper a utilizar
            device: Dispositivo para processamento ('auto', 'cuda', 'cpu')
        """
        self.model_name = model_name
        self.device = self._get_device(device)
        self.processor = None
        self.model = None
        self.is_loaded = False
        
        # Cache para modelos
        self.cache_dir = Path("cache/whisper")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"WhisperService inicializado com modelo {model_name} no dispositivo {self.device}")
    
    def _get_device(self, device: str) -> str:
        """Determina o dispositivo a utilizar."""
        if device == "auto":
            if torch.cuda.is_available():
                return "cuda"
            else:
                return "cpu"
        return device
    
    def load_model(self) -> bool:
        """
        Carrega o modelo Whisper.
        
        Returns:
            True se o modelo foi carregado com sucesso
        """
        try:
            logger.info(f"A carregar modelo Whisper: {self.model_name}")
            
            # Carregar processor e modelo
            self.processor = WhisperProcessor.from_pretrained(
                self.model_name,
                cache_dir=str(self.cache_dir)
            )
            
            self.model = WhisperForConditionalGeneration.from_pretrained(
                self.model_name,
                cache_dir=str(self.cache_dir)
            )
            
            # Mover modelo para o dispositivo apropriado
            self.model = self.model.to(self.device)
            
            # Otimizações para inferência
            self.model.eval()
            if self.device == "cuda":
                self.model = self.model.half()  # Usar precisão half para economizar VRAM
            
            self.is_loaded = True
            logger.info(f"Modelo Whisper carregado com sucesso no dispositivo {self.device}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao carregar modelo Whisper: {e}")
            self.is_loaded = False
            return False
    
    def preprocess_audio(self, audio_data: Union[bytes, str, Path]) -> np.ndarray:
        """
        Pré-processa áudio para o formato esperado pelo Whisper.
        
        Args:
            audio_data: Dados de áudio (bytes, caminho do ficheiro, ou Path)
            
        Returns:
            Array numpy com áudio processado
        """
        try:
            # Se for bytes, salvar temporariamente
            if isinstance(audio_data, bytes):
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                    temp_file.write(audio_data)
                    temp_path = temp_file.name
                
                # Carregar áudio
                audio_segment = AudioSegment.from_file(temp_path)
                
                # Limpar ficheiro temporário
                os.unlink(temp_path)
                
            else:
                # Carregar diretamente do caminho
                audio_segment = AudioSegment.from_file(str(audio_data))
            
            # Converter para mono e 16kHz (formato esperado pelo Whisper)
            audio_segment = audio_segment.set_channels(1).set_frame_rate(16000)
            
            # Converter para array numpy
            audio_array = np.array(audio_segment.get_array_of_samples(), dtype=np.float32)
            
            # Normalizar para [-1, 1]
            if audio_segment.sample_width == 2:  # 16-bit
                audio_array = audio_array / 32768.0
            elif audio_segment.sample_width == 4:  # 32-bit
                audio_array = audio_array / 2147483648.0
            
            logger.info(f"Áudio pré-processado: {len(audio_array)} amostras, {len(audio_array)/16000:.2f}s")
            return audio_array
            
        except Exception as e:
            logger.error(f"Erro no pré-processamento de áudio: {e}")
            raise
    
    def transcribe(self, audio_data: Union[bytes, str, Path], language: str = "pt") -> dict:
        """
        Transcreve áudio para texto.
        
        Args:
            audio_data: Dados de áudio
            language: Código do idioma (pt, en, es, etc.)
            
        Returns:
            Dicionário com resultado da transcrição
        """
        if not self.is_loaded:
            if not self.load_model():
                return {"error": "Falha ao carregar modelo Whisper"}
        
        try:
            # Pré-processar áudio
            audio_array = self.preprocess_audio(audio_data)
            
            # Processar com Whisper
            inputs = self.processor(
                audio_array,
                sampling_rate=16000,
                return_tensors="pt"
            )
            
            # Mover inputs para o dispositivo
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # Gerar transcrição
            with torch.no_grad():
                # Forçar idioma se especificado
                forced_decoder_ids = self.processor.get_decoder_prompt_ids(
                    language=language,
                    task="transcribe"
                )
                
                predicted_ids = self.model.generate(
                    inputs["input_features"],
                    forced_decoder_ids=forced_decoder_ids,
                    max_length=448,
                    num_beams=5,
                    temperature=0.0
                )
            
            # Decodificar resultado
            transcription = self.processor.batch_decode(
                predicted_ids,
                skip_special_tokens=True
            )[0]
            
            # Limpar texto
            transcription = transcription.strip()
            
            logger.info(f"Transcrição concluída: {len(transcription)} caracteres")
            
            return {
                "text": transcription,
                "language": language,
                "model": self.model_name,
                "device": self.device,
                "duration": len(audio_array) / 16000
            }
            
        except Exception as e:
            logger.error(f"Erro na transcrição: {e}")
            return {"error": str(e)}
    
    def get_status(self) -> dict:
        """Retorna o status do serviço."""
        return {
            "loaded": self.is_loaded,
            "model": self.model_name,
            "device": self.device,
            "cuda_available": torch.cuda.is_available(),
            "memory_usage": self._get_memory_usage()
        }
    
    def _get_memory_usage(self) -> dict:
        """Retorna informações sobre uso de memória."""
        memory_info = {}
        
        if torch.cuda.is_available() and self.device == "cuda":
            memory_info["gpu_allocated"] = torch.cuda.memory_allocated() / 1024**3  # GB
            memory_info["gpu_reserved"] = torch.cuda.memory_reserved() / 1024**3    # GB
            memory_info["gpu_total"] = torch.cuda.get_device_properties(0).total_memory / 1024**3  # GB
        
        return memory_info

# Instância global do serviço
whisper_service = WhisperService()
```

### 2.3. Integração com FastAPI

Agora, integre o serviço Whisper com o seu backend FastAPI. Adicione os seguintes endpoints ao seu `app.py`:

```python
from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.responses import JSONResponse
import tempfile
import os
from whisper_service import whisper_service

# Adicionar aos endpoints existentes

@app.post("/api/whisper/transcribe")
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
    try:
        # Verificar tipo de ficheiro
        if not audio.content_type.startswith('audio/'):
            raise HTTPException(status_code=400, detail="Ficheiro deve ser de áudio")
        
        # Ler dados do áudio
        audio_data = await audio.read()
        
        # Transcrever
        result = whisper_service.transcribe(audio_data, language)
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.error(f"Erro na transcrição: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/whisper/status")
async def get_whisper_status():
    """Retorna o status do serviço Whisper."""
    return whisper_service.get_status()

@app.post("/api/whisper/load")
async def load_whisper_model(model_name: str = "openai/whisper-small"):
    """Carrega um modelo Whisper específico."""
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

@app.post("/api/chat/voice")
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
    try:
        # Transcrever áudio
        audio_data = await audio.read()
        transcription_result = whisper_service.transcribe(audio_data, language)
        
        if "error" in transcription_result:
            raise HTTPException(status_code=500, detail=transcription_result["error"])
        
        transcribed_text = transcription_result["text"]
        
        # Enviar para chat (reutilizar lógica existente)
        chat_response = await chat_with_ollama(transcribed_text, model)
        
        return {
            "transcription": transcription_result,
            "chat_response": chat_response,
            "original_text": transcribed_text
        }
        
    except Exception as e:
        logger.error(f"Erro no chat por voz: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

### 2.4. Configuração de Modelos Whisper

O Whisper oferece vários modelos com diferentes tamanhos e capacidades. Crie um ficheiro `whisper_config.py` para gerir estas configurações:

```python
"""
Configurações para modelos Whisper.
"""

WHISPER_MODELS = {
    "tiny": {
        "name": "openai/whisper-tiny",
        "size": "~39 MB",
        "vram": "~1 GB",
        "speed": "⚡⚡⚡⚡⚡",
        "quality": "⭐⭐",
        "languages": 99,
        "description": "Modelo mais rápido, qualidade básica"
    },
    "base": {
        "name": "openai/whisper-base",
        "size": "~74 MB", 
        "vram": "~1 GB",
        "speed": "⚡⚡⚡⚡",
        "quality": "⭐⭐⭐",
        "languages": 99,
        "description": "Bom equilíbrio velocidade/qualidade"
    },
    "small": {
        "name": "openai/whisper-small",
        "size": "~244 MB",
        "vram": "~2 GB", 
        "speed": "⚡⚡⚡",
        "quality": "⭐⭐⭐⭐",
        "languages": 99,
        "description": "Qualidade boa, velocidade razoável"
    },
    "medium": {
        "name": "openai/whisper-medium",
        "size": "~769 MB",
        "vram": "~5 GB",
        "speed": "⚡⚡",
        "quality": "⭐⭐⭐⭐⭐",
        "languages": 99,
        "description": "Alta qualidade, mais lento"
    },
    "large": {
        "name": "openai/whisper-large-v2",
        "size": "~1550 MB",
        "vram": "~10 GB",
        "speed": "⚡",
        "quality": "⭐⭐⭐⭐⭐",
        "languages": 99,
        "description": "Máxima qualidade, mais lento"
    }
}

SUPPORTED_LANGUAGES = {
    "pt": "Português",
    "en": "English", 
    "es": "Español",
    "fr": "Français",
    "de": "Deutsch",
    "it": "Italiano",
    "ja": "日本語",
    "ko": "한국어",
    "zh": "中文",
    "ru": "Русский",
    "ar": "العربية"
}

AUDIO_FORMATS = [
    "audio/wav",
    "audio/mp3", 
    "audio/m4a",
    "audio/ogg",
    "audio/flac",
    "audio/webm"
]

DEFAULT_CONFIG = {
    "model": "small",
    "language": "pt",
    "max_duration": 300,  # 5 minutos
    "chunk_size": 30,     # 30 segundos por chunk
    "temperature": 0.0,
    "beam_size": 5
}
```

### 2.5. Gestão de Recursos e Otimizações

Para garantir que o Whisper funciona eficientemente sem comprometer outros serviços, implemente um sistema de gestão de recursos:

```python
import psutil
import threading
import time
from typing import Optional

class ResourceManager:
    """
    Gestor de recursos para otimizar o uso de CPU/GPU entre serviços.
    """
    
    def __init__(self):
        self.whisper_active = False
        self.stable_diffusion_active = False
        self.lock = threading.Lock()
        
    def can_use_whisper(self) -> bool:
        """Verifica se é seguro usar o Whisper agora."""
        with self.lock:
            # Verificar uso de memória
            memory_percent = psutil.virtual_memory().percent
            if memory_percent > 85:
                return False
            
            # Verificar se Stable Diffusion está ativo
            if self.stable_diffusion_active:
                return False
                
            return True
    
    def reserve_whisper(self) -> bool:
        """Reserva recursos para o Whisper."""
        with self.lock:
            if self.can_use_whisper():
                self.whisper_active = True
                return True
            return False
    
    def release_whisper(self):
        """Liberta recursos do Whisper."""
        with self.lock:
            self.whisper_active = False
    
    def get_optimal_model(self) -> str:
        """Retorna o modelo Whisper mais adequado baseado nos recursos disponíveis."""
        available_memory = psutil.virtual_memory().available / (1024**3)  # GB
        
        if available_memory > 10:
            return "medium"
        elif available_memory > 5:
            return "small" 
        elif available_memory > 2:
            return "base"
        else:
            return "tiny"

# Instância global
resource_manager = ResourceManager()
```

Esta implementação detalhada do Whisper fornece uma base sólida para reconhecimento de fala na sua aplicação. O sistema é modular, eficiente e integra-se perfeitamente com a arquitetura FastAPI existente. A próxima secção abordará a criação da interface de utilizador para esta funcionalidade.


## 3. Guia de Implementação da WebUI

A interface de utilizador web (WebUI) para a funcionalidade Whisper deve integrar-se harmoniosamente com o design existente da aplicação, proporcionando uma experiência intuitiva e profissional. Esta secção detalha a implementação completa da interface, desde os componentes básicos até às funcionalidades avançadas.

### 3.1. Estrutura da Interface

A WebUI será implementada como uma nova aba na interface existente, mantendo a consistência visual e funcional. A estrutura seguirá o padrão estabelecido pelas abas de Chat e Geração de Imagens, mas com componentes específicos para gravação e processamento de áudio.

**Componentes Principais:**

A interface será composta por quatro componentes principais: o gravador de áudio, o carregador de ficheiros, o visualizador de transcrições e o painel de configurações. O gravador de áudio permitirá aos utilizadores gravar diretamente através do microfone do navegador, com feedback visual em tempo real. O carregador de ficheiros suportará múltiplos formatos de áudio e fornecerá validação antes do upload. O visualizador de transcrições apresentará os resultados de forma clara e permitirá edição e cópia do texto. O painel de configurações oferecerá controlo sobre modelos, idiomas e parâmetros de transcrição.

### 3.2. Implementação HTML

Adicione a seguinte estrutura HTML ao seu ficheiro `templates/index.html`, integrando-a com as abas existentes:

```html
<!-- Adicionar à secção de abas existente -->
<div class="tab-button" data-tab="voice" id="voice-tab">
    <i class="fas fa-microphone"></i>
    <span>Reconhecimento de Voz</span>
</div>

<!-- Adicionar à secção de conteúdo das abas -->
<div id="voice-content" class="tab-content">
    <div class="voice-container">
        <!-- Cabeçalho da secção -->
        <div class="voice-header">
            <h2><i class="fas fa-microphone"></i> Reconhecimento de Voz</h2>
            <p>Transcreva áudio para texto usando modelos Whisper avançados</p>
        </div>

        <!-- Painel de configurações -->
        <div class="voice-config-panel">
            <div class="config-row">
                <div class="config-group">
                    <label for="whisper-model">Modelo Whisper:</label>
                    <select id="whisper-model" class="config-select">
                        <option value="tiny">Tiny (Rápido)</option>
                        <option value="base">Base (Equilibrado)</option>
                        <option value="small" selected>Small (Recomendado)</option>
                        <option value="medium">Medium (Alta Qualidade)</option>
                        <option value="large">Large (Máxima Qualidade)</option>
                    </select>
                </div>
                
                <div class="config-group">
                    <label for="voice-language">Idioma:</label>
                    <select id="voice-language" class="config-select">
                        <option value="pt" selected>Português</option>
                        <option value="en">English</option>
                        <option value="es">Español</option>
                        <option value="fr">Français</option>
                        <option value="de">Deutsch</option>
                        <option value="it">Italiano</option>
                    </select>
                </div>
                
                <div class="config-group">
                    <label for="auto-chat">Enviar para Chat:</label>
                    <input type="checkbox" id="auto-chat" class="config-checkbox">
                    <span class="checkbox-label">Automático</span>
                </div>
            </div>
        </div>

        <!-- Área principal de gravação/upload -->
        <div class="voice-main-area">
            <!-- Gravador de áudio -->
            <div class="audio-recorder">
                <div class="recorder-visual">
                    <div class="recording-indicator" id="recording-indicator">
                        <div class="pulse-ring"></div>
                        <div class="microphone-icon">
                            <i class="fas fa-microphone" id="mic-icon"></i>
                        </div>
                    </div>
                    
                    <div class="recording-info">
                        <div class="recording-time" id="recording-time">00:00</div>
                        <div class="recording-status" id="recording-status">Pronto para gravar</div>
                    </div>
                </div>
                
                <div class="recorder-controls">
                    <button id="start-recording" class="btn btn-primary">
                        <i class="fas fa-microphone"></i>
                        Iniciar Gravação
                    </button>
                    <button id="stop-recording" class="btn btn-secondary" disabled>
                        <i class="fas fa-stop"></i>
                        Parar Gravação
                    </button>
                    <button id="play-recording" class="btn btn-outline" disabled>
                        <i class="fas fa-play"></i>
                        Reproduzir
                    </button>
                </div>
            </div>

            <!-- Separador -->
            <div class="voice-separator">
                <span>ou</span>
            </div>

            <!-- Upload de ficheiro -->
            <div class="audio-upload">
                <div class="upload-area" id="audio-upload-area">
                    <div class="upload-icon">
                        <i class="fas fa-cloud-upload-alt"></i>
                    </div>
                    <div class="upload-text">
                        <h3>Carregar Ficheiro de Áudio</h3>
                        <p>Arraste um ficheiro aqui ou clique para selecionar</p>
                        <small>Suporta: MP3, WAV, M4A, OGG, FLAC (máx. 10MB)</small>
                    </div>
                    <input type="file" id="audio-file-input" accept="audio/*" hidden>
                </div>
                
                <div class="file-info" id="file-info" style="display: none;">
                    <div class="file-details">
                        <i class="fas fa-file-audio"></i>
                        <span class="file-name" id="file-name"></span>
                        <span class="file-size" id="file-size"></span>
                    </div>
                    <button class="btn btn-small btn-outline" id="remove-file">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            </div>
        </div>

        <!-- Botão de transcrição -->
        <div class="transcribe-section">
            <button id="transcribe-btn" class="btn btn-primary btn-large" disabled>
                <i class="fas fa-language"></i>
                <span>Transcrever Áudio</span>
                <div class="loading-spinner" style="display: none;"></div>
            </button>
        </div>

        <!-- Área de resultados -->
        <div class="transcription-results" id="transcription-results" style="display: none;">
            <div class="results-header">
                <h3><i class="fas fa-file-alt"></i> Transcrição</h3>
                <div class="results-actions">
                    <button class="btn btn-small btn-outline" id="copy-transcription">
                        <i class="fas fa-copy"></i> Copiar
                    </button>
                    <button class="btn btn-small btn-outline" id="edit-transcription">
                        <i class="fas fa-edit"></i> Editar
                    </button>
                    <button class="btn btn-small btn-primary" id="send-to-chat">
                        <i class="fas fa-comments"></i> Enviar para Chat
                    </button>
                </div>
            </div>
            
            <div class="transcription-content">
                <div class="transcription-text" id="transcription-text" contenteditable="false"></div>
                <div class="transcription-meta" id="transcription-meta"></div>
            </div>
        </div>

        <!-- Status do Whisper -->
        <div class="whisper-status" id="whisper-status">
            <div class="status-item">
                <span class="status-label">Status do Whisper:</span>
                <span class="status-value" id="whisper-status-value">
                    <i class="fas fa-circle status-indicator"></i>
                    Verificando...
                </span>
            </div>
            <div class="status-item">
                <span class="status-label">Modelo Carregado:</span>
                <span class="status-value" id="whisper-model-status">Nenhum</span>
            </div>
            <div class="status-item">
                <span class="status-label">Dispositivo:</span>
                <span class="status-value" id="whisper-device-status">-</span>
            </div>
        </div>
    </div>
</div>
```

### 3.3. Estilos CSS

Adicione os seguintes estilos ao seu ficheiro `static/css/style.css` para criar uma interface moderna e responsiva:

```css
/* Estilos para a aba de reconhecimento de voz */
.voice-container {
    max-width: 800px;
    margin: 0 auto;
    padding: 20px;
}

.voice-header {
    text-align: center;
    margin-bottom: 30px;
}

.voice-header h2 {
    color: var(--primary-color);
    margin-bottom: 10px;
    font-size: 2rem;
}

.voice-header p {
    color: var(--text-secondary);
    font-size: 1.1rem;
}

/* Painel de configurações */
.voice-config-panel {
    background: var(--card-background);
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 30px;
    border: 1px solid var(--border-color);
}

.config-row {
    display: flex;
    gap: 20px;
    align-items: end;
    flex-wrap: wrap;
}

.config-group {
    display: flex;
    flex-direction: column;
    gap: 8px;
    min-width: 150px;
}

.config-group label {
    font-weight: 600;
    color: var(--text-primary);
    font-size: 0.9rem;
}

.config-select {
    padding: 10px 12px;
    border: 2px solid var(--border-color);
    border-radius: 8px;
    background: var(--input-background);
    color: var(--text-primary);
    font-size: 0.95rem;
    transition: all 0.3s ease;
}

.config-select:focus {
    outline: none;
    border-color: var(--primary-color);
    box-shadow: 0 0 0 3px rgba(74, 144, 226, 0.1);
}

.config-checkbox {
    width: 18px;
    height: 18px;
    accent-color: var(--primary-color);
}

.checkbox-label {
    color: var(--text-secondary);
    font-size: 0.9rem;
}

/* Área principal */
.voice-main-area {
    display: flex;
    flex-direction: column;
    gap: 30px;
    margin-bottom: 30px;
}

/* Gravador de áudio */
.audio-recorder {
    background: var(--card-background);
    border-radius: 16px;
    padding: 30px;
    text-align: center;
    border: 2px solid var(--border-color);
    transition: all 0.3s ease;
}

.recorder-visual {
    margin-bottom: 30px;
}

.recording-indicator {
    position: relative;
    display: inline-block;
    margin-bottom: 20px;
}

.pulse-ring {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    width: 120px;
    height: 120px;
    border: 3px solid var(--primary-color);
    border-radius: 50%;
    opacity: 0;
    animation: pulse 2s infinite;
}

.recording-indicator.recording .pulse-ring {
    opacity: 1;
    animation: pulse 1s infinite;
}

@keyframes pulse {
    0% {
        transform: translate(-50%, -50%) scale(0.8);
        opacity: 1;
    }
    100% {
        transform: translate(-50%, -50%) scale(1.2);
        opacity: 0;
    }
}

.microphone-icon {
    width: 80px;
    height: 80px;
    background: var(--primary-color);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-size: 2rem;
    transition: all 0.3s ease;
}

.recording-indicator.recording .microphone-icon {
    background: var(--danger-color);
    animation: recordingPulse 1s infinite alternate;
}

@keyframes recordingPulse {
    0% { transform: scale(1); }
    100% { transform: scale(1.1); }
}

.recording-info {
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.recording-time {
    font-size: 1.5rem;
    font-weight: 600;
    color: var(--primary-color);
    font-family: 'Courier New', monospace;
}

.recording-status {
    color: var(--text-secondary);
    font-size: 1rem;
}

.recorder-controls {
    display: flex;
    gap: 15px;
    justify-content: center;
    flex-wrap: wrap;
}

/* Separador */
.voice-separator {
    text-align: center;
    position: relative;
    margin: 20px 0;
}

.voice-separator::before {
    content: '';
    position: absolute;
    top: 50%;
    left: 0;
    right: 0;
    height: 1px;
    background: var(--border-color);
}

.voice-separator span {
    background: var(--background-color);
    padding: 0 20px;
    color: var(--text-secondary);
    font-weight: 500;
    position: relative;
    z-index: 1;
}

/* Upload de áudio */
.audio-upload {
    background: var(--card-background);
    border-radius: 16px;
    border: 2px solid var(--border-color);
    transition: all 0.3s ease;
}

.upload-area {
    padding: 40px 20px;
    text-align: center;
    cursor: pointer;
    transition: all 0.3s ease;
    border-radius: 14px;
}

.upload-area:hover {
    background: var(--hover-background);
    border-color: var(--primary-color);
}

.upload-area.dragover {
    background: rgba(74, 144, 226, 0.1);
    border-color: var(--primary-color);
    transform: scale(1.02);
}

.upload-icon {
    font-size: 3rem;
    color: var(--primary-color);
    margin-bottom: 20px;
}

.upload-text h3 {
    color: var(--text-primary);
    margin-bottom: 10px;
    font-size: 1.3rem;
}

.upload-text p {
    color: var(--text-secondary);
    margin-bottom: 10px;
}

.upload-text small {
    color: var(--text-muted);
    font-size: 0.85rem;
}

.file-info {
    padding: 20px;
    background: var(--success-background);
    border-top: 1px solid var(--border-color);
    display: flex;
    align-items: center;
    justify-content: space-between;
    border-radius: 0 0 14px 14px;
}

.file-details {
    display: flex;
    align-items: center;
    gap: 12px;
    color: var(--success-color);
}

.file-details i {
    font-size: 1.2rem;
}

.file-name {
    font-weight: 600;
}

.file-size {
    color: var(--text-secondary);
    font-size: 0.9rem;
}

/* Secção de transcrição */
.transcribe-section {
    text-align: center;
    margin-bottom: 30px;
}

.btn-large {
    padding: 15px 30px;
    font-size: 1.1rem;
    min-width: 200px;
    position: relative;
}

.loading-spinner {
    position: absolute;
    right: 15px;
    top: 50%;
    transform: translateY(-50%);
    width: 20px;
    height: 20px;
    border: 2px solid transparent;
    border-top: 2px solid currentColor;
    border-radius: 50%;
    animation: spin 1s linear infinite;
}

@keyframes spin {
    0% { transform: translateY(-50%) rotate(0deg); }
    100% { transform: translateY(-50%) rotate(360deg); }
}

/* Resultados da transcrição */
.transcription-results {
    background: var(--card-background);
    border-radius: 16px;
    border: 2px solid var(--border-color);
    overflow: hidden;
    margin-bottom: 30px;
}

.results-header {
    background: var(--primary-color);
    color: white;
    padding: 20px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 15px;
}

.results-header h3 {
    margin: 0;
    font-size: 1.2rem;
}

.results-actions {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
}

.results-actions .btn {
    background: rgba(255, 255, 255, 0.1);
    border-color: rgba(255, 255, 255, 0.3);
    color: white;
}

.results-actions .btn:hover {
    background: rgba(255, 255, 255, 0.2);
}

.results-actions .btn-primary {
    background: rgba(255, 255, 255, 0.9);
    color: var(--primary-color);
}

.transcription-content {
    padding: 25px;
}

.transcription-text {
    background: var(--input-background);
    border: 2px solid var(--border-color);
    border-radius: 12px;
    padding: 20px;
    min-height: 120px;
    font-size: 1.05rem;
    line-height: 1.6;
    color: var(--text-primary);
    margin-bottom: 15px;
    transition: all 0.3s ease;
}

.transcription-text[contenteditable="true"] {
    border-color: var(--primary-color);
    box-shadow: 0 0 0 3px rgba(74, 144, 226, 0.1);
}

.transcription-meta {
    display: flex;
    gap: 20px;
    flex-wrap: wrap;
    font-size: 0.9rem;
    color: var(--text-secondary);
}

.transcription-meta span {
    background: var(--tag-background);
    padding: 4px 8px;
    border-radius: 6px;
}

/* Status do Whisper */
.whisper-status {
    background: var(--card-background);
    border-radius: 12px;
    padding: 20px;
    border: 1px solid var(--border-color);
}

.status-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 0;
    border-bottom: 1px solid var(--border-color);
}

.status-item:last-child {
    border-bottom: none;
}

.status-label {
    font-weight: 600;
    color: var(--text-primary);
}

.status-value {
    display: flex;
    align-items: center;
    gap: 8px;
    color: var(--text-secondary);
}

.status-indicator {
    font-size: 0.8rem;
}

.status-indicator.online {
    color: var(--success-color);
}

.status-indicator.offline {
    color: var(--danger-color);
}

.status-indicator.loading {
    color: var(--warning-color);
}

/* Responsividade */
@media (max-width: 768px) {
    .voice-container {
        padding: 15px;
    }
    
    .config-row {
        flex-direction: column;
        align-items: stretch;
    }
    
    .recorder-controls {
        flex-direction: column;
        align-items: center;
    }
    
    .results-header {
        flex-direction: column;
        align-items: stretch;
        text-align: center;
    }
    
    .results-actions {
        justify-content: center;
    }
    
    .transcription-meta {
        justify-content: center;
    }
}

/* Animações de entrada */
.voice-container > * {
    animation: fadeInUp 0.6s ease-out;
}

@keyframes fadeInUp {
    from {
        opacity: 0;
        transform: translateY(20px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}
```

### 3.4. Implementação JavaScript

Crie um novo ficheiro `static/js/voice.js` para gerir toda a lógica da interface de voz:

```javascript
/**
 * Módulo de Reconhecimento de Voz
 * Gere gravação, upload e transcrição de áudio
 */

class VoiceInterface {
    constructor() {
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.recordedBlob = null;
        this.isRecording = false;
        this.recordingStartTime = null;
        this.recordingTimer = null;
        this.currentAudioFile = null;
        
        this.initializeElements();
        this.bindEvents();
        this.checkWhisperStatus();
        
        // Verificar suporte do navegador
        this.checkBrowserSupport();
    }
    
    initializeElements() {
        // Elementos de gravação
        this.startRecordingBtn = document.getElementById('start-recording');
        this.stopRecordingBtn = document.getElementById('stop-recording');
        this.playRecordingBtn = document.getElementById('play-recording');
        this.recordingIndicator = document.getElementById('recording-indicator');
        this.recordingTime = document.getElementById('recording-time');
        this.recordingStatus = document.getElementById('recording-status');
        this.micIcon = document.getElementById('mic-icon');
        
        // Elementos de upload
        this.audioUploadArea = document.getElementById('audio-upload-area');
        this.audioFileInput = document.getElementById('audio-file-input');
        this.fileInfo = document.getElementById('file-info');
        this.fileName = document.getElementById('file-name');
        this.fileSize = document.getElementById('file-size');
        this.removeFileBtn = document.getElementById('remove-file');
        
        // Elementos de transcrição
        this.transcribeBtn = document.getElementById('transcribe-btn');
        this.transcriptionResults = document.getElementById('transcription-results');
        this.transcriptionText = document.getElementById('transcription-text');
        this.transcriptionMeta = document.getElementById('transcription-meta');
        
        // Elementos de controlo
        this.whisperModel = document.getElementById('whisper-model');
        this.voiceLanguage = document.getElementById('voice-language');
        this.autoChat = document.getElementById('auto-chat');
        
        // Elementos de ação
        this.copyTranscriptionBtn = document.getElementById('copy-transcription');
        this.editTranscriptionBtn = document.getElementById('edit-transcription');
        this.sendToChatBtn = document.getElementById('send-to-chat');
        
        // Elementos de status
        this.whisperStatusValue = document.getElementById('whisper-status-value');
        this.whisperModelStatus = document.getElementById('whisper-model-status');
        this.whisperDeviceStatus = document.getElementById('whisper-device-status');
    }
    
    bindEvents() {
        // Eventos de gravação
        this.startRecordingBtn.addEventListener('click', () => this.startRecording());
        this.stopRecordingBtn.addEventListener('click', () => this.stopRecording());
        this.playRecordingBtn.addEventListener('click', () => this.playRecording());
        
        // Eventos de upload
        this.audioUploadArea.addEventListener('click', () => this.audioFileInput.click());
        this.audioUploadArea.addEventListener('dragover', (e) => this.handleDragOver(e));
        this.audioUploadArea.addEventListener('dragleave', (e) => this.handleDragLeave(e));
        this.audioUploadArea.addEventListener('drop', (e) => this.handleDrop(e));
        this.audioFileInput.addEventListener('change', (e) => this.handleFileSelect(e));
        this.removeFileBtn.addEventListener('click', () => this.removeFile());
        
        // Eventos de transcrição
        this.transcribeBtn.addEventListener('click', () => this.transcribeAudio());
        
        // Eventos de ação
        this.copyTranscriptionBtn.addEventListener('click', () => this.copyTranscription());
        this.editTranscriptionBtn.addEventListener('click', () => this.toggleEdit());
        this.sendToChatBtn.addEventListener('click', () => this.sendToChat());
        
        // Eventos de configuração
        this.whisperModel.addEventListener('change', () => this.loadWhisperModel());
    }
    
    checkBrowserSupport() {
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            this.showError('O seu navegador não suporta gravação de áudio');
            this.startRecordingBtn.disabled = true;
            return false;
        }
        return true;
    }
    
    async checkWhisperStatus() {
        try {
            const response = await fetch('/api/whisper/status');
            const status = await response.json();
            
            this.updateStatusDisplay(status);
            
            if (!status.loaded) {
                await this.loadWhisperModel();
            }
            
        } catch (error) {
            console.error('Erro ao verificar status do Whisper:', error);
            this.updateStatusDisplay({ loaded: false, error: error.message });
        }
    }
    
    updateStatusDisplay(status) {
        const indicator = this.whisperStatusValue.querySelector('.status-indicator');
        
        if (status.loaded) {
            indicator.className = 'fas fa-circle status-indicator online';
            this.whisperStatusValue.innerHTML = '<i class="fas fa-circle status-indicator online"></i> Online';
            this.whisperModelStatus.textContent = status.model || 'Desconhecido';
            this.whisperDeviceStatus.textContent = status.device || 'CPU';
        } else {
            indicator.className = 'fas fa-circle status-indicator offline';
            this.whisperStatusValue.innerHTML = '<i class="fas fa-circle status-indicator offline"></i> Offline';
            this.whisperModelStatus.textContent = 'Nenhum';
            this.whisperDeviceStatus.textContent = '-';
        }
    }
    
    async loadWhisperModel() {
        const modelName = this.whisperModel.value;
        
        try {
            this.whisperStatusValue.innerHTML = '<i class="fas fa-circle status-indicator loading"></i> Carregando...';
            
            const response = await fetch('/api/whisper/load', {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: `model_name=openai/whisper-${modelName}`
            });
            
            if (response.ok) {
                await this.checkWhisperStatus();
                this.showSuccess(`Modelo ${modelName} carregado com sucesso`);
            } else {
                throw new Error('Falha ao carregar modelo');
            }
            
        } catch (error) {
            console.error('Erro ao carregar modelo:', error);
            this.showError('Erro ao carregar modelo Whisper');
            this.updateStatusDisplay({ loaded: false });
        }
    }
    
    async startRecording() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ 
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true
                }
            });
            
            this.mediaRecorder = new MediaRecorder(stream, {
                mimeType: 'audio/webm;codecs=opus'
            });
            
            this.audioChunks = [];
            
            this.mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    this.audioChunks.push(event.data);
                }
            };
            
            this.mediaRecorder.onstop = () => {
                this.recordedBlob = new Blob(this.audioChunks, { type: 'audio/webm' });
                this.enableTranscription();
                
                // Parar todas as faixas de áudio
                stream.getTracks().forEach(track => track.stop());
            };
            
            this.mediaRecorder.start(1000); // Gravar em chunks de 1 segundo
            this.isRecording = true;
            this.recordingStartTime = Date.now();
            
            this.updateRecordingUI(true);
            this.startRecordingTimer();
            
        } catch (error) {
            console.error('Erro ao iniciar gravação:', error);
            this.showError('Erro ao aceder ao microfone. Verifique as permissões.');
        }
    }
    
    stopRecording() {
        if (this.mediaRecorder && this.isRecording) {
            this.mediaRecorder.stop();
            this.isRecording = false;
            this.updateRecordingUI(false);
            this.stopRecordingTimer();
        }
    }
    
    playRecording() {
        if (this.recordedBlob) {
            const audioUrl = URL.createObjectURL(this.recordedBlob);
            const audio = new Audio(audioUrl);
            audio.play();
            
            // Limpar URL após reprodução
            audio.onended = () => URL.revokeObjectURL(audioUrl);
        }
    }
    
    updateRecordingUI(recording) {
        if (recording) {
            this.recordingIndicator.classList.add('recording');
            this.recordingStatus.textContent = 'A gravar...';
            this.startRecordingBtn.disabled = true;
            this.stopRecordingBtn.disabled = false;
            this.micIcon.className = 'fas fa-stop';
        } else {
            this.recordingIndicator.classList.remove('recording');
            this.recordingStatus.textContent = 'Gravação concluída';
            this.startRecordingBtn.disabled = false;
            this.stopRecordingBtn.disabled = true;
            this.playRecordingBtn.disabled = false;
            this.micIcon.className = 'fas fa-microphone';
        }
    }
    
    startRecordingTimer() {
        this.recordingTimer = setInterval(() => {
            const elapsed = Date.now() - this.recordingStartTime;
            const minutes = Math.floor(elapsed / 60000);
            const seconds = Math.floor((elapsed % 60000) / 1000);
            this.recordingTime.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        }, 1000);
    }
    
    stopRecordingTimer() {
        if (this.recordingTimer) {
            clearInterval(this.recordingTimer);
            this.recordingTimer = null;
        }
    }
    
    handleDragOver(e) {
        e.preventDefault();
        this.audioUploadArea.classList.add('dragover');
    }
    
    handleDragLeave(e) {
        e.preventDefault();
        this.audioUploadArea.classList.remove('dragover');
    }
    
    handleDrop(e) {
        e.preventDefault();
        this.audioUploadArea.classList.remove('dragover');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            this.processFile(files[0]);
        }
    }
    
    handleFileSelect(e) {
        const file = e.target.files[0];
        if (file) {
            this.processFile(file);
        }
    }
    
    processFile(file) {
        // Validar tipo de ficheiro
        if (!file.type.startsWith('audio/')) {
            this.showError('Por favor, selecione um ficheiro de áudio válido');
            return;
        }
        
        // Validar tamanho (máx. 10MB)
        if (file.size > 10 * 1024 * 1024) {
            this.showError('O ficheiro é muito grande. Máximo: 10MB');
            return;
        }
        
        this.currentAudioFile = file;
        this.displayFileInfo(file);
        this.enableTranscription();
    }
    
    displayFileInfo(file) {
        this.fileName.textContent = file.name;
        this.fileSize.textContent = this.formatFileSize(file.size);
        this.fileInfo.style.display = 'flex';
        this.audioUploadArea.style.display = 'none';
    }
    
    removeFile() {
        this.currentAudioFile = null;
        this.fileInfo.style.display = 'none';
        this.audioUploadArea.style.display = 'block';
        this.audioFileInput.value = '';
        this.disableTranscription();
    }
    
    enableTranscription() {
        this.transcribeBtn.disabled = false;
    }
    
    disableTranscription() {
        this.transcribeBtn.disabled = true;
    }
    
    async transcribeAudio() {
        const audioData = this.recordedBlob || this.currentAudioFile;
        
        if (!audioData) {
            this.showError('Nenhum áudio disponível para transcrição');
            return;
        }
        
        try {
            this.setTranscribing(true);
            
            const formData = new FormData();
            formData.append('audio', audioData, 'audio.webm');
            formData.append('language', this.voiceLanguage.value);
            
            const endpoint = this.autoChat.checked ? '/api/chat/voice' : '/api/whisper/transcribe';
            
            const response = await fetch(endpoint, {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                throw new Error(`Erro HTTP: ${response.status}`);
            }
            
            const result = await response.json();
            
            if (this.autoChat.checked) {
                this.displayCombinedResult(result);
            } else {
                this.displayTranscription(result);
            }
            
        } catch (error) {
            console.error('Erro na transcrição:', error);
            this.showError('Erro ao transcrever áudio: ' + error.message);
        } finally {
            this.setTranscribing(false);
        }
    }
    
    setTranscribing(transcribing) {
        const spinner = this.transcribeBtn.querySelector('.loading-spinner');
        const text = this.transcribeBtn.querySelector('span');
        
        if (transcribing) {
            this.transcribeBtn.disabled = true;
            spinner.style.display = 'block';
            text.textContent = 'A transcrever...';
        } else {
            this.transcribeBtn.disabled = false;
            spinner.style.display = 'none';
            text.textContent = 'Transcrever Áudio';
        }
    }
    
    displayTranscription(result) {
        this.transcriptionText.textContent = result.text;
        this.updateTranscriptionMeta(result);
        this.transcriptionResults.style.display = 'block';
        
        // Scroll para os resultados
        this.transcriptionResults.scrollIntoView({ behavior: 'smooth' });
    }
    
    displayCombinedResult(result) {
        this.displayTranscription(result.transcription);
        
        // Mostrar também a resposta do chat se disponível
        if (result.chat_response) {
            this.showSuccess('Texto enviado para o chat com sucesso');
            // Aqui poderia integrar com a interface de chat existente
        }
    }
    
    updateTranscriptionMeta(result) {
        const duration = result.duration ? `${result.duration.toFixed(1)}s` : 'N/A';
        const model = result.model || 'Desconhecido';
        const language = result.language || 'Desconhecido';
        const device = result.device || 'CPU';
        
        this.transcriptionMeta.innerHTML = `
            <span>Duração: ${duration}</span>
            <span>Modelo: ${model}</span>
            <span>Idioma: ${language}</span>
            <span>Dispositivo: ${device}</span>
        `;
    }
    
    copyTranscription() {
        const text = this.transcriptionText.textContent;
        navigator.clipboard.writeText(text).then(() => {
            this.showSuccess('Texto copiado para a área de transferência');
        }).catch(() => {
            this.showError('Erro ao copiar texto');
        });
    }
    
    toggleEdit() {
        const isEditable = this.transcriptionText.contentEditable === 'true';
        
        if (isEditable) {
            this.transcriptionText.contentEditable = 'false';
            this.editTranscriptionBtn.innerHTML = '<i class="fas fa-edit"></i> Editar';
            this.showSuccess('Edição guardada');
        } else {
            this.transcriptionText.contentEditable = 'true';
            this.transcriptionText.focus();
            this.editTranscriptionBtn.innerHTML = '<i class="fas fa-save"></i> Guardar';
        }
    }
    
    sendToChat() {
        const text = this.transcriptionText.textContent.trim();
        
        if (!text) {
            this.showError('Nenhum texto para enviar');
            return;
        }
        
        // Integrar com a interface de chat existente
        // Assumindo que existe uma função global para enviar mensagens
        if (typeof sendMessage === 'function') {
            sendMessage(text);
            this.showSuccess('Texto enviado para o chat');
        } else {
            // Fallback: copiar para área de transferência
            this.copyTranscription();
            this.showInfo('Texto copiado. Cole na área de chat manualmente.');
        }
    }
    
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
    
    showSuccess(message) {
        this.showNotification(message, 'success');
    }
    
    showError(message) {
        this.showNotification(message, 'error');
    }
    
    showInfo(message) {
        this.showNotification(message, 'info');
    }
    
    showNotification(message, type) {
        // Implementar sistema de notificações
        // Por agora, usar alert simples
        console.log(`${type.toUpperCase()}: ${message}`);
        
        // Criar notificação visual
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, 5000);
    }
}

// Inicializar quando o DOM estiver pronto
document.addEventListener('DOMContentLoaded', () => {
    // Verificar se estamos na aba de voz
    const voiceTab = document.getElementById('voice-tab');
    if (voiceTab) {
        window.voiceInterface = new VoiceInterface();
    }
});
```

### 3.5. Integração com a Interface Existente

Para integrar completamente a nova funcionalidade com a interface existente, adicione o seguinte código ao seu ficheiro `static/js/app.js`:

```javascript
// Adicionar ao sistema de abas existente
function initializeVoiceTab() {
    const voiceTab = document.getElementById('voice-tab');
    const voiceContent = document.getElementById('voice-content');
    
    if (voiceTab && voiceContent) {
        voiceTab.addEventListener('click', () => {
            // Ativar aba de voz
            document.querySelectorAll('.tab-button').forEach(tab => tab.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
            
            voiceTab.classList.add('active');
            voiceContent.classList.add('active');
            
            // Verificar status do Whisper quando a aba for ativada
            if (window.voiceInterface) {
                window.voiceInterface.checkWhisperStatus();
            }
        });
    }
}

// Função para integração com chat
function sendMessageFromVoice(text) {
    // Mudar para a aba de chat
    const chatTab = document.getElementById('chat-tab');
    const chatContent = document.getElementById('chat-content');
    
    if (chatTab && chatContent) {
        chatTab.click();
        
        // Preencher campo de mensagem
        const messageInput = document.getElementById('message-input');
        if (messageInput) {
            messageInput.value = text;
            messageInput.focus();
        }
    }
}

// Adicionar à inicialização existente
document.addEventListener('DOMContentLoaded', () => {
    initializeVoiceTab();
    
    // Tornar função disponível globalmente
    window.sendMessage = sendMessageFromVoice;
});
```

Esta implementação completa da WebUI fornece uma interface moderna, intuitiva e totalmente funcional para a funcionalidade de reconhecimento de voz. A interface integra-se perfeitamente com o design existente e oferece todas as funcionalidades necessárias para uma experiência de utilizador excepcional.


## 4. Melhorias na Robustez do Docker

A containerização robusta é fundamental para garantir que a adição do Whisper e da WebUI não comprometa a estabilidade, performance e facilidade de manutenção da aplicação. Esta secção apresenta uma abordagem abrangente para otimizar a infraestrutura Docker, implementando melhores práticas que tornarão o sistema mais resiliente, eficiente e fácil de gerir.

### 4.1. Otimização do Dockerfile

O Dockerfile atual será reestruturado para implementar builds multi-stage, reduzir o tamanho da imagem e melhorar a segurança. A abordagem multi-stage permite separar as dependências de build das dependências de runtime, resultando em imagens mais leves e seguras.

**Dockerfile Otimizado:**

```dockerfile
# Estágio 1: Build das dependências
FROM python:3.11-slim as builder

# Definir variáveis de ambiente para build
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Instalar dependências do sistema necessárias para build
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    cmake \
    pkg-config \
    libffi-dev \
    libssl-dev \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Criar diretório de trabalho
WORKDIR /build

# Copiar ficheiros de dependências
COPY requirements.txt .

# Criar ambiente virtual e instalar dependências
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Instalar dependências Python
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt

# Estágio 2: Runtime otimizado
FROM python:3.11-slim as runtime

# Definir variáveis de ambiente
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    DEBIAN_FRONTEND=noninteractive

# Criar utilizador não-root para segurança
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Instalar dependências de runtime
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copiar ambiente virtual do estágio de build
COPY --from=builder /opt/venv /opt/venv

# Criar diretórios necessários
RUN mkdir -p /app/cache/whisper \
             /app/cache/huggingface \
             /app/cache/transformers \
             /app/generated_images \
             /app/logs \
             /app/static \
             /app/templates \
    && chown -R appuser:appuser /app

# Definir diretório de trabalho
WORKDIR /app

# Copiar código da aplicação
COPY --chown=appuser:appuser . .

# Mudar para utilizador não-root
USER appuser

# Expor porta
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# Comando de inicialização
CMD ["python", "app.py"]
```

**Dockerfile para Desenvolvimento:**

Crie um `Dockerfile.dev` para desenvolvimento com hot-reload e ferramentas de debug:

```dockerfile
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    build-essential \
    git \
    curl \
    vim \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Instalar dependências Python
COPY requirements.txt requirements-dev.txt ./
RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
    pip install -r requirements-dev.txt

# Copiar código
COPY . .

# Criar diretórios
RUN mkdir -p cache/whisper cache/huggingface cache/transformers generated_images logs

EXPOSE 8001

CMD ["python", "app.py", "--reload", "--debug"]
```

### 4.2. Docker Compose Melhorado

O ficheiro `docker-compose.yml` será reestruturado para suportar múltiplos ambientes, gestão adequada de recursos e monitorização avançada.

**docker-compose.yml Principal:**

```yaml
version: '3.8'

services:
  llm-app:
    build:
      context: .
      dockerfile: Dockerfile
      args:
        - BUILDKIT_INLINE_CACHE=1
    image: llm-pessoal:latest
    container_name: llm-app
    restart: unless-stopped
    
    # Gestão de recursos
    deploy:
      resources:
        limits:
          cpus: '4.0'
          memory: 8G
        reservations:
          cpus: '1.0'
          memory: 2G
    
    # Variáveis de ambiente
    environment:
      - HOST=0.0.0.0
      - PORT=8001
      - DEBUG=false
      - OLLAMA_HOST=http://ollama:11434
      - WHISPER_CACHE_DIR=/app/cache/whisper
      - HF_CACHE_DIR=/app/cache/huggingface
      - TRANSFORMERS_CACHE=/app/cache/transformers
    
    # Volumes persistentes
    volumes:
      - whisper_cache:/app/cache/whisper
      - huggingface_cache:/app/cache/huggingface
      - transformers_cache:/app/cache/transformers
      - generated_images:/app/generated_images
      - app_logs:/app/logs
    
    # Portas
    ports:
      - "8001:8001"
    
    # Dependências
    depends_on:
      ollama:
        condition: service_healthy
    
    # Redes
    networks:
      - llm-network
    
    # Health check
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8001/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
    
    # Logs
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  ollama:
    image: ollama/ollama:latest
    container_name: ollama
    restart: unless-stopped
    
    # GPU support (descomente se tiver GPU NVIDIA)
    # runtime: nvidia
    # environment:
    #   - NVIDIA_VISIBLE_DEVICES=all
    
    # Gestão de recursos
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '0.5'
          memory: 1G
    
    # Volumes
    volumes:
      - ollama_data:/root/.ollama
    
    # Portas
    ports:
      - "11434:11434"
    
    # Redes
    networks:
      - llm-network
    
    # Health check
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:11434/api/tags"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 30s
    
    # Logs
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  # Serviço de monitorização (opcional)
  watchtower:
    image: containrrr/watchtower:latest
    container_name: watchtower
    restart: unless-stopped
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
    environment:
      - WATCHTOWER_CLEANUP=true
      - WATCHTOWER_POLL_INTERVAL=3600
      - WATCHTOWER_INCLUDE_STOPPED=true
    networks:
      - llm-network

# Volumes nomeados para persistência
volumes:
  whisper_cache:
    driver: local
  huggingface_cache:
    driver: local
  transformers_cache:
    driver: local
  generated_images:
    driver: local
  app_logs:
    driver: local
  ollama_data:
    driver: local

# Rede personalizada
networks:
  llm-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
```

**docker-compose.dev.yml para Desenvolvimento:**

```yaml
version: '3.8'

services:
  llm-app-dev:
    build:
      context: .
      dockerfile: Dockerfile.dev
    container_name: llm-app-dev
    restart: "no"
    
    environment:
      - HOST=0.0.0.0
      - PORT=8001
      - DEBUG=true
      - RELOAD=true
      - OLLAMA_HOST=http://ollama:11434
    
    volumes:
      - .:/app
      - whisper_cache_dev:/app/cache/whisper
      - huggingface_cache_dev:/app/cache/huggingface
      - transformers_cache_dev:/app/cache/transformers
      - ./generated_images:/app/generated_images
      - ./logs:/app/logs
    
    ports:
      - "8001:8001"
    
    depends_on:
      - ollama
    
    networks:
      - llm-network-dev

  ollama:
    image: ollama/ollama:latest
    container_name: ollama-dev
    restart: "no"
    
    volumes:
      - ollama_data_dev:/root/.ollama
    
    ports:
      - "11434:11434"
    
    networks:
      - llm-network-dev

volumes:
  whisper_cache_dev:
  huggingface_cache_dev:
  transformers_cache_dev:
  ollama_data_dev:

networks:
  llm-network-dev:
    driver: bridge
```

### 4.3. Scripts de Gestão Automatizada

Crie scripts para automatizar tarefas comuns de gestão e manutenção do ambiente Docker.

**scripts/docker-manager.sh:**

```bash
#!/bin/bash

# Script de gestão Docker para LLM Pessoal
# Uso: ./docker-manager.sh [comando] [opções]

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configurações
PROJECT_NAME="llm-pessoal"
COMPOSE_FILE="docker-compose.yml"
COMPOSE_DEV_FILE="docker-compose.dev.yml"

# Funções auxiliares
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Verificar se Docker está instalado
check_docker() {
    if ! command -v docker &> /dev/null; then
        log_error "Docker não está instalado"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose não está instalado"
        exit 1
    fi
}

# Verificar recursos do sistema
check_resources() {
    log_info "Verificando recursos do sistema..."
    
    # Verificar memória disponível
    AVAILABLE_MEM=$(free -g | awk 'NR==2{printf "%.0f", $7}')
    if [ "$AVAILABLE_MEM" -lt 4 ]; then
        log_warning "Memória disponível baixa: ${AVAILABLE_MEM}GB (recomendado: 8GB+)"
    fi
    
    # Verificar espaço em disco
    AVAILABLE_DISK=$(df -BG . | awk 'NR==2{print $4}' | sed 's/G//')
    if [ "$AVAILABLE_DISK" -lt 10 ]; then
        log_warning "Espaço em disco baixo: ${AVAILABLE_DISK}GB (recomendado: 20GB+)"
    fi
    
    # Verificar GPU NVIDIA
    if command -v nvidia-smi &> /dev/null; then
        log_success "GPU NVIDIA detectada"
        nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
    else
        log_info "GPU NVIDIA não detectada, usando CPU"
    fi
}

# Construir imagens
build() {
    local env=${1:-prod}
    
    log_info "Construindo imagens para ambiente: $env"
    
    if [ "$env" = "dev" ]; then
        docker-compose -f $COMPOSE_DEV_FILE build --no-cache
    else
        docker-compose -f $COMPOSE_FILE build --no-cache
    fi
    
    log_success "Imagens construídas com sucesso"
}

# Iniciar serviços
start() {
    local env=${1:-prod}
    
    check_resources
    
    log_info "Iniciando serviços para ambiente: $env"
    
    if [ "$env" = "dev" ]; then
        docker-compose -f $COMPOSE_DEV_FILE up -d
    else
        docker-compose -f $COMPOSE_FILE up -d
    fi
    
    log_success "Serviços iniciados"
    
    # Aguardar serviços ficarem prontos
    wait_for_services $env
}

# Parar serviços
stop() {
    local env=${1:-prod}
    
    log_info "Parando serviços para ambiente: $env"
    
    if [ "$env" = "dev" ]; then
        docker-compose -f $COMPOSE_DEV_FILE down
    else
        docker-compose -f $COMPOSE_FILE down
    fi
    
    log_success "Serviços parados"
}

# Reiniciar serviços
restart() {
    local env=${1:-prod}
    
    log_info "Reiniciando serviços para ambiente: $env"
    
    stop $env
    start $env
}

# Aguardar serviços ficarem prontos
wait_for_services() {
    local env=${1:-prod}
    local max_attempts=30
    local attempt=1
    
    log_info "Aguardando serviços ficarem prontos..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f http://localhost:8001/health &> /dev/null; then
            log_success "Aplicação pronta em http://localhost:8001"
            return 0
        fi
        
        log_info "Tentativa $attempt/$max_attempts - aguardando..."
        sleep 10
        ((attempt++))
    done
    
    log_error "Serviços não ficaram prontos após $max_attempts tentativas"
    return 1
}

# Ver logs
logs() {
    local service=${1:-llm-app}
    local env=${2:-prod}
    
    if [ "$env" = "dev" ]; then
        docker-compose -f $COMPOSE_DEV_FILE logs -f $service
    else
        docker-compose -f $COMPOSE_FILE logs -f $service
    fi
}

# Status dos serviços
status() {
    local env=${1:-prod}
    
    log_info "Status dos serviços:"
    
    if [ "$env" = "dev" ]; then
        docker-compose -f $COMPOSE_DEV_FILE ps
    else
        docker-compose -f $COMPOSE_FILE ps
    fi
}

# Limpeza
cleanup() {
    log_info "Limpando recursos Docker..."
    
    # Parar todos os contêineres
    docker-compose -f $COMPOSE_FILE down 2>/dev/null || true
    docker-compose -f $COMPOSE_DEV_FILE down 2>/dev/null || true
    
    # Remover imagens não utilizadas
    docker image prune -f
    
    # Remover volumes órfãos
    docker volume prune -f
    
    # Remover redes não utilizadas
    docker network prune -f
    
    log_success "Limpeza concluída"
}

# Backup de dados
backup() {
    local backup_dir="backups/$(date +%Y%m%d_%H%M%S)"
    
    log_info "Criando backup em: $backup_dir"
    
    mkdir -p $backup_dir
    
    # Backup de volumes
    docker run --rm -v llm-pessoal_whisper_cache:/data -v $(pwd)/$backup_dir:/backup alpine tar czf /backup/whisper_cache.tar.gz -C /data .
    docker run --rm -v llm-pessoal_huggingface_cache:/data -v $(pwd)/$backup_dir:/backup alpine tar czf /backup/huggingface_cache.tar.gz -C /data .
    docker run --rm -v llm-pessoal_generated_images:/data -v $(pwd)/$backup_dir:/backup alpine tar czf /backup/generated_images.tar.gz -C /data .
    docker run --rm -v llm-pessoal_ollama_data:/data -v $(pwd)/$backup_dir:/backup alpine tar czf /backup/ollama_data.tar.gz -C /data .
    
    # Backup de configurações
    cp docker-compose.yml $backup_dir/
    cp -r static $backup_dir/ 2>/dev/null || true
    cp -r templates $backup_dir/ 2>/dev/null || true
    
    log_success "Backup criado em: $backup_dir"
}

# Restaurar backup
restore() {
    local backup_dir=$1
    
    if [ -z "$backup_dir" ]; then
        log_error "Especifique o diretório de backup"
        exit 1
    fi
    
    if [ ! -d "$backup_dir" ]; then
        log_error "Diretório de backup não encontrado: $backup_dir"
        exit 1
    fi
    
    log_info "Restaurando backup de: $backup_dir"
    
    # Parar serviços
    stop
    
    # Restaurar volumes
    if [ -f "$backup_dir/whisper_cache.tar.gz" ]; then
        docker run --rm -v llm-pessoal_whisper_cache:/data -v $(pwd)/$backup_dir:/backup alpine tar xzf /backup/whisper_cache.tar.gz -C /data
    fi
    
    if [ -f "$backup_dir/huggingface_cache.tar.gz" ]; then
        docker run --rm -v llm-pessoal_huggingface_cache:/data -v $(pwd)/$backup_dir:/backup alpine tar xzf /backup/huggingface_cache.tar.gz -C /data
    fi
    
    if [ -f "$backup_dir/generated_images.tar.gz" ]; then
        docker run --rm -v llm-pessoal_generated_images:/data -v $(pwd)/$backup_dir:/backup alpine tar xzf /backup/generated_images.tar.gz -C /data
    fi
    
    if [ -f "$backup_dir/ollama_data.tar.gz" ]; then
        docker run --rm -v llm-pessoal_ollama_data:/data -v $(pwd)/$backup_dir:/backup alpine tar xzf /backup/ollama_data.tar.gz -C /data
    fi
    
    log_success "Backup restaurado"
}

# Atualizar sistema
update() {
    log_info "Atualizando sistema..."
    
    # Fazer backup antes da atualização
    backup
    
    # Parar serviços
    stop
    
    # Atualizar código (assumindo git)
    if [ -d ".git" ]; then
        git pull origin main
    fi
    
    # Reconstruir imagens
    build
    
    # Iniciar serviços
    start
    
    log_success "Sistema atualizado"
}

# Monitorização
monitor() {
    log_info "Iniciando monitorização..."
    
    while true; do
        clear
        echo "=== LLM Pessoal - Monitorização ==="
        echo "Timestamp: $(date)"
        echo
        
        # Status dos contêineres
        echo "=== Status dos Contêineres ==="
        docker-compose -f $COMPOSE_FILE ps
        echo
        
        # Uso de recursos
        echo "=== Uso de Recursos ==="
        docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"
        echo
        
        # Health checks
        echo "=== Health Checks ==="
        curl -s http://localhost:8001/health | jq . 2>/dev/null || echo "Aplicação não responde"
        curl -s http://localhost:11434/api/tags | jq '.models | length' 2>/dev/null | xargs -I {} echo "Ollama: {} modelos carregados"
        echo
        
        sleep 30
    done
}

# Menu de ajuda
help() {
    echo "LLM Pessoal - Script de Gestão Docker"
    echo
    echo "Uso: $0 [comando] [opções]"
    echo
    echo "Comandos:"
    echo "  build [prod|dev]     - Construir imagens"
    echo "  start [prod|dev]     - Iniciar serviços"
    echo "  stop [prod|dev]      - Parar serviços"
    echo "  restart [prod|dev]   - Reiniciar serviços"
    echo "  logs [serviço] [env] - Ver logs"
    echo "  status [prod|dev]    - Status dos serviços"
    echo "  cleanup              - Limpeza de recursos"
    echo "  backup               - Criar backup"
    echo "  restore [dir]        - Restaurar backup"
    echo "  update               - Atualizar sistema"
    echo "  monitor              - Monitorização em tempo real"
    echo "  help                 - Mostrar esta ajuda"
    echo
    echo "Exemplos:"
    echo "  $0 start prod        - Iniciar em produção"
    echo "  $0 start dev         - Iniciar em desenvolvimento"
    echo "  $0 logs llm-app      - Ver logs da aplicação"
    echo "  $0 backup            - Criar backup"
}

# Função principal
main() {
    check_docker
    
    case "${1:-help}" in
        build)
            build $2
            ;;
        start)
            start $2
            ;;
        stop)
            stop $2
            ;;
        restart)
            restart $2
            ;;
        logs)
            logs $2 $3
            ;;
        status)
            status $2
            ;;
        cleanup)
            cleanup
            ;;
        backup)
            backup
            ;;
        restore)
            restore $2
            ;;
        update)
            update
            ;;
        monitor)
            monitor
            ;;
        help|*)
            help
            ;;
    esac
}

# Executar função principal
main "$@"
```

### 4.4. Configuração de Monitorização e Logs

Implemente um sistema robusto de monitorização e gestão de logs para facilitar a depuração e manutenção.

**config/logging.conf:**

```ini
[loggers]
keys=root,app,whisper,ollama

[handlers]
keys=consoleHandler,fileHandler,rotatingFileHandler

[formatters]
keys=simpleFormatter,detailedFormatter

[logger_root]
level=INFO
handlers=consoleHandler,rotatingFileHandler

[logger_app]
level=INFO
handlers=consoleHandler,rotatingFileHandler
qualname=app
propagate=0

[logger_whisper]
level=INFO
handlers=fileHandler
qualname=whisper
propagate=0

[logger_ollama]
level=INFO
handlers=fileHandler
qualname=ollama
propagate=0

[handler_consoleHandler]
class=StreamHandler
level=INFO
formatter=simpleFormatter
args=(sys.stdout,)

[handler_fileHandler]
class=FileHandler
level=INFO
formatter=detailedFormatter
args=('logs/app.log',)

[handler_rotatingFileHandler]
class=handlers.RotatingFileHandler
level=INFO
formatter=detailedFormatter
args=('logs/app.log', 'a', 10485760, 5)

[formatter_simpleFormatter]
format=%(asctime)s - %(name)s - %(levelname)s - %(message)s

[formatter_detailedFormatter]
format=%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(funcName)s - %(lineno)d - %(message)s
```

**health_check.py:**

```python
"""
Sistema de health check para monitorização da aplicação.
"""

import asyncio
import aiohttp
import psutil
import torch
import logging
from datetime import datetime
from typing import Dict, Any

logger = logging.getLogger(__name__)

class HealthChecker:
    """Sistema de verificação de saúde da aplicação."""
    
    def __init__(self):
        self.checks = {
            'system': self.check_system_resources,
            'whisper': self.check_whisper_service,
            'ollama': self.check_ollama_service,
            'disk_space': self.check_disk_space,
            'memory': self.check_memory_usage,
            'gpu': self.check_gpu_status
        }
    
    async def run_all_checks(self) -> Dict[str, Any]:
        """Executa todas as verificações de saúde."""
        results = {
            'timestamp': datetime.utcnow().isoformat(),
            'status': 'healthy',
            'checks': {}
        }
        
        for check_name, check_func in self.checks.items():
            try:
                check_result = await check_func()
                results['checks'][check_name] = check_result
                
                if not check_result.get('healthy', True):
                    results['status'] = 'unhealthy'
                    
            except Exception as e:
                logger.error(f"Erro na verificação {check_name}: {e}")
                results['checks'][check_name] = {
                    'healthy': False,
                    'error': str(e)
                }
                results['status'] = 'unhealthy'
        
        return results
    
    async def check_system_resources(self) -> Dict[str, Any]:
        """Verifica recursos do sistema."""
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        
        return {
            'healthy': cpu_percent < 90 and memory.percent < 90,
            'cpu_percent': cpu_percent,
            'memory_percent': memory.percent,
            'memory_available_gb': memory.available / (1024**3)
        }
    
    async def check_whisper_service(self) -> Dict[str, Any]:
        """Verifica o serviço Whisper."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get('http://localhost:8001/api/whisper/status') as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            'healthy': data.get('loaded', False),
                            'model': data.get('model'),
                            'device': data.get('device')
                        }
                    else:
                        return {'healthy': False, 'error': f'HTTP {response.status}'}
        except Exception as e:
            return {'healthy': False, 'error': str(e)}
    
    async def check_ollama_service(self) -> Dict[str, Any]:
        """Verifica o serviço Ollama."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get('http://localhost:11434/api/tags') as response:
                    if response.status == 200:
                        data = await response.json()
                        models = data.get('models', [])
                        return {
                            'healthy': len(models) > 0,
                            'models_count': len(models),
                            'models': [m.get('name') for m in models]
                        }
                    else:
                        return {'healthy': False, 'error': f'HTTP {response.status}'}
        except Exception as e:
            return {'healthy': False, 'error': str(e)}
    
    async def check_disk_space(self) -> Dict[str, Any]:
        """Verifica espaço em disco."""
        disk_usage = psutil.disk_usage('/')
        free_gb = disk_usage.free / (1024**3)
        
        return {
            'healthy': free_gb > 5,  # Pelo menos 5GB livres
            'free_gb': free_gb,
            'total_gb': disk_usage.total / (1024**3),
            'used_percent': (disk_usage.used / disk_usage.total) * 100
        }
    
    async def check_memory_usage(self) -> Dict[str, Any]:
        """Verifica uso de memória detalhado."""
        memory = psutil.virtual_memory()
        
        return {
            'healthy': memory.percent < 85,
            'total_gb': memory.total / (1024**3),
            'available_gb': memory.available / (1024**3),
            'used_gb': memory.used / (1024**3),
            'percent': memory.percent
        }
    
    async def check_gpu_status(self) -> Dict[str, Any]:
        """Verifica status da GPU."""
        if not torch.cuda.is_available():
            return {
                'healthy': True,
                'available': False,
                'message': 'GPU não disponível, usando CPU'
            }
        
        try:
            gpu_memory = torch.cuda.memory_stats()
            allocated_gb = gpu_memory['allocated_bytes.all.current'] / (1024**3)
            reserved_gb = gpu_memory['reserved_bytes.all.current'] / (1024**3)
            
            return {
                'healthy': True,
                'available': True,
                'allocated_gb': allocated_gb,
                'reserved_gb': reserved_gb,
                'device_count': torch.cuda.device_count(),
                'device_name': torch.cuda.get_device_name(0)
            }
        except Exception as e:
            return {
                'healthy': False,
                'available': True,
                'error': str(e)
            }

# Instância global
health_checker = HealthChecker()
```

Esta implementação robusta do Docker fornece uma base sólida para a gestão, monitorização e manutenção da aplicação. O sistema é resiliente, eficiente e facilita significativamente as operações de desenvolvimento e produção.


## 5. Implementação Passo a Passo

Esta secção fornece um roteiro detalhado para implementar todas as melhorias descritas neste guia, organizadas numa sequência lógica que minimiza riscos e maximiza a eficiência do processo.

### 5.1. Preparação do Ambiente

Antes de iniciar a implementação, é crucial preparar adequadamente o ambiente de desenvolvimento e fazer backup dos dados existentes.

**Passo 1: Backup Completo**

Execute um backup completo do sistema atual antes de fazer qualquer alteração:

```bash
# Criar diretório de backup
mkdir -p backups/pre-whisper-$(date +%Y%m%d)

# Backup do código
cp -r . backups/pre-whisper-$(date +%Y%m%d)/code/

# Backup de volumes Docker (se existirem)
docker-compose down
docker run --rm -v llm-pessoal_ollama_data:/data -v $(pwd)/backups/pre-whisper-$(date +%Y%m%d):/backup alpine tar czf /backup/ollama_data.tar.gz -C /data .
```

**Passo 2: Atualização das Dependências**

Atualize o ficheiro `requirements.txt` com as novas dependências:

```
# Dependências existentes (manter)
fastapi>=0.104.0
uvicorn>=0.24.0
jinja2>=3.1.0
python-multipart>=0.0.6
requests>=2.31.0
torch>=2.0.0
torchvision>=0.15.0
diffusers>=0.21.0
transformers>=4.30.0
accelerate>=0.24.0

# Novas dependências para Whisper
torchaudio>=2.0.0
librosa>=0.10.0
soundfile>=0.12.0
pydub>=0.25.0
ffmpeg-python>=0.2.0

# Dependências para monitorização
psutil>=5.9.0
aiohttp>=3.8.0
```

### 5.2. Implementação do Backend

**Passo 3: Criar o Módulo Whisper**

Crie o ficheiro `whisper_service.py` com o código fornecido na secção 2.2. Este módulo encapsula toda a lógica do Whisper.

**Passo 4: Atualizar o FastAPI**

Modifique o ficheiro `app.py` para incluir os novos endpoints:

```python
# Adicionar imports
from whisper_service import whisper_service
from health_check import health_checker

# Adicionar endpoints (código da secção 2.3)

# Adicionar endpoint de health check
@app.get("/health")
async def health_check():
    """Endpoint de verificação de saúde."""
    return await health_checker.run_all_checks()
```

**Passo 5: Configuração de Logs**

Crie o diretório `config/` e adicione o ficheiro `logging.conf` com a configuração fornecida na secção 4.4.

### 5.3. Implementação do Frontend

**Passo 6: Atualizar HTML**

Modifique o ficheiro `templates/index.html` para incluir a nova aba de reconhecimento de voz com o código HTML fornecido na secção 3.2.

**Passo 7: Adicionar Estilos CSS**

Adicione os estilos CSS fornecidos na secção 3.3 ao ficheiro `static/css/style.css`.

**Passo 8: Implementar JavaScript**

Crie o ficheiro `static/js/voice.js` com o código JavaScript fornecido na secção 3.4.

**Passo 9: Integrar com Interface Existente**

Modifique o ficheiro `static/js/app.js` para incluir a integração com a nova aba, conforme descrito na secção 3.5.

### 5.4. Otimização do Docker

**Passo 10: Atualizar Dockerfile**

Substitua o `Dockerfile` existente pelo Dockerfile otimizado fornecido na secção 4.1.

**Passo 11: Atualizar Docker Compose**

Substitua o `docker-compose.yml` existente pela versão melhorada fornecida na secção 4.2.

**Passo 12: Criar Scripts de Gestão**

Crie o diretório `scripts/` e adicione o ficheiro `docker-manager.sh` com o código fornecido na secção 4.3. Torne o script executável:

```bash
chmod +x scripts/docker-manager.sh
```

### 5.5. Testes e Validação

**Passo 13: Teste Local**

Execute testes locais para verificar se todas as funcionalidades estão a funcionar:

```bash
# Construir e iniciar em modo desenvolvimento
./scripts/docker-manager.sh build dev
./scripts/docker-manager.sh start dev

# Verificar logs
./scripts/docker-manager.sh logs llm-app-dev dev

# Testar endpoints
curl http://localhost:8001/health
curl http://localhost:8001/api/whisper/status
```

**Passo 14: Teste de Produção**

Após validar em desenvolvimento, teste em modo de produção:

```bash
# Parar desenvolvimento
./scripts/docker-manager.sh stop dev

# Iniciar produção
./scripts/docker-manager.sh start prod

# Monitorizar
./scripts/docker-manager.sh monitor
```

### 5.6. Configuração Final

**Passo 15: Configurar Variáveis de Ambiente**

Crie um ficheiro `.env` para personalizar configurações:

```env
# Servidor
HOST=0.0.0.0
PORT=8001
DEBUG=false

# Whisper
WHISPER_MODEL=small
WHISPER_DEVICE=auto
WHISPER_CACHE_DIR=/app/cache/whisper

# Ollama
OLLAMA_HOST=http://ollama:11434

# Logs
LOG_LEVEL=INFO
```

**Passo 16: Documentação**

Atualize o README.md do projeto para incluir informações sobre as novas funcionalidades.

## 6. Resolução de Problemas Comuns

### 6.1. Problemas de Instalação

**Erro: FFmpeg não encontrado**
```bash
# Solução: Instalar FFmpeg no sistema
sudo apt-get update && sudo apt-get install ffmpeg
```

**Erro: Dependências de áudio**
```bash
# Solução: Instalar bibliotecas de áudio
sudo apt-get install libsndfile1-dev libportaudio2-dev
```

### 6.2. Problemas de Performance

**Whisper muito lento**
- Use modelos menores (tiny, base) para testes
- Verifique se a GPU está a ser utilizada
- Reduza a qualidade do áudio de entrada

**Falta de memória**
- Ajuste os limites de recursos no docker-compose.yml
- Use modelos Whisper menores
- Feche outras aplicações

### 6.3. Problemas de Conectividade

**Erro de conexão entre serviços**
- Verifique se todos os contêineres estão na mesma rede
- Confirme que as portas estão expostas corretamente
- Use nomes de serviço em vez de localhost

## 7. Próximos Passos e Melhorias Futuras

### 7.1. Funcionalidades Avançadas

**Reconhecimento de Voz em Tempo Real**
Implementar streaming de áudio para transcrição em tempo real, permitindo conversas mais naturais com a IA.

**Síntese de Voz (TTS)**
Adicionar capacidade de síntese de voz para que a IA possa responder em áudio, criando uma experiência completamente por voz.

**Múltiplos Idiomas Simultâneos**
Implementar deteção automática de idioma e suporte para conversas multilingues.

### 7.2. Otimizações de Performance

**Cache Inteligente**
Implementar sistema de cache para transcrições frequentes e otimizar o uso de recursos.

**Processamento Distribuído**
Configurar processamento distribuído para lidar com múltiplos utilizadores simultaneamente.

**Otimizações de GPU**
Implementar partilha eficiente de GPU entre Whisper e Stable Diffusion.

### 7.3. Melhorias de Interface

**Interface Mobile**
Desenvolver aplicação mobile nativa para acesso mais conveniente às funcionalidades de voz.

**Comandos de Voz**
Implementar comandos de voz para controlar a aplicação (e.g., "gerar imagem", "mudar modelo").

**Visualizações Avançadas**
Adicionar visualizações de forma de onda, espectrogramas e outras ferramentas de análise de áudio.

## 8. Conclusão

Este guia fornece uma implementação completa e robusta para adicionar funcionalidades de reconhecimento de voz (Whisper) e uma interface web moderna à sua aplicação de LLM pessoal. A abordagem apresentada prioriza a estabilidade, performance e facilidade de manutenção, garantindo que as novas funcionalidades se integrem harmoniosamente com o sistema existente.

As melhorias na infraestrutura Docker tornam o sistema mais resiliente e fácil de gerir, enquanto a interface de utilizador moderna proporciona uma experiência intuitiva e profissional. O sistema de monitorização e logs facilita a depuração e manutenção contínua.

A implementação modular permite adicionar as funcionalidades gradualmente, testando cada componente antes de avançar para o próximo. Os scripts de gestão automatizam tarefas comuns e reduzem a possibilidade de erros humanos.

Com estas melhorias, a sua aplicação de LLM pessoal estará preparada para oferecer uma experiência multimodal completa, mantendo os princípios de privacidade e controlo local que caracterizam o projeto original.

---

**Autor:** Manus AI  
**Data:** Janeiro 2025  
**Versão:** 1.0

