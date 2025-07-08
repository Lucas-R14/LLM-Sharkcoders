# -*- coding: utf-8 -*-
"""
Gestor de recursos para otimizar o uso de CPU/GPU entre serviços.
"""

import psutil
import threading
import time
from typing import Optional
import logging

logger = logging.getLogger(__name__)

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
                logger.warning(f"Memória muito alta: {memory_percent}%")
                return False
            
            # Verificar se Stable Diffusion está ativo
            if self.stable_diffusion_active:
                logger.info("Stable Diffusion ativo, aguardando...")
                return False
                
            return True
    
    def reserve_whisper(self) -> bool:
        """Reserva recursos para o Whisper."""
        with self.lock:
            if self.can_use_whisper():
                self.whisper_active = True
                logger.info("Recursos reservados para Whisper")
                return True
            return False
    
    def release_whisper(self):
        """Liberta recursos do Whisper."""
        with self.lock:
            self.whisper_active = False
            logger.info("Recursos do Whisper libertados")
    
    def reserve_stable_diffusion(self) -> bool:
        """Reserva recursos para Stable Diffusion."""
        with self.lock:
            if not self.whisper_active:
                self.stable_diffusion_active = True
                logger.info("Recursos reservados para Stable Diffusion")
                return True
            return False
    
    def release_stable_diffusion(self):
        """Liberta recursos do Stable Diffusion."""
        with self.lock:
            self.stable_diffusion_active = False
            logger.info("Recursos do Stable Diffusion libertados")
    
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
    
    def get_system_info(self) -> dict:
        """Retorna informações detalhadas do sistema."""
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_total_gb": memory.total / (1024**3),
            "memory_available_gb": memory.available / (1024**3),
            "memory_percent": memory.percent,
            "disk_total_gb": disk.total / (1024**3),
            "disk_free_gb": disk.free / (1024**3),
            "disk_percent": (disk.used / disk.total) * 100,
            "whisper_active": self.whisper_active,
            "stable_diffusion_active": self.stable_diffusion_active
        }
    
    def wait_for_resources(self, service: str, timeout: int = 60) -> bool:
        """
        Aguarda até que recursos estejam disponíveis.
        
        Args:
            service: 'whisper' ou 'stable_diffusion'
            timeout: Tempo máximo de espera em segundos
            
        Returns:
            True se recursos foram obtidos, False se timeout
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if service == 'whisper' and self.can_use_whisper():
                return True
            elif service == 'stable_diffusion' and not self.whisper_active:
                return True
            
            time.sleep(2)
        
        logger.warning(f"Timeout aguardando recursos para {service}")
        return False

# Instância global
resource_manager = ResourceManager() 