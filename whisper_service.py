#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Serviço Whisper para Reconhecimento de Voz
Integra modelos Whisper para transcrição de áudio
"""

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