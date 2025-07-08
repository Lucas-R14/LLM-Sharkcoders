# -*- coding: utf-8 -*-
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