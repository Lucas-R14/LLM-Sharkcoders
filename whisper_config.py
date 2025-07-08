# -*- coding: utf-8 -*-
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