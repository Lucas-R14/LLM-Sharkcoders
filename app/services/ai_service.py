import os
import json
import time
import asyncio
from typing import Dict, List, Optional, AsyncGenerator
import requests
from litellm import completion, acompletion
import openai
import anthropic
import google.generativeai as genai
from datetime import datetime, timezone

from app.config import Config
from app.models.user import User, ChatSession, UsageLog

class AIService:
    def __init__(self):
        self.config = Config()
        self.setup_providers()
    
    def setup_providers(self):
        """Setup all AI providers with their API keys"""
        # OpenAI
        if self.config.OPENAI_API_KEY:
            os.environ["OPENAI_API_KEY"] = self.config.OPENAI_API_KEY
        
        # Anthropic (Claude)
        if self.config.ANTHROPIC_API_KEY:
            os.environ["ANTHROPIC_API_KEY"] = self.config.ANTHROPIC_API_KEY
        
        # Google (Gemini)
        if self.config.GOOGLE_API_KEY:
            os.environ["GOOGLE_API_KEY"] = self.config.GOOGLE_API_KEY
            genai.configure(api_key=self.config.GOOGLE_API_KEY)
        
        # Groq
        if self.config.GROQ_API_KEY:
            os.environ["GROQ_API_KEY"] = self.config.GROQ_API_KEY
    
    def get_available_models(self, user: User) -> Dict[str, List]:
        """Get available models for a specific user based on their permissions"""
        allowed_providers = user.get_allowed_models()
        available_models = {}
        
        for provider in allowed_providers:
            if provider in self.config.AI_MODELS:
                available_models[provider] = []
                for model_id, model_info in self.config.AI_MODELS[provider].items():
                    available_models[provider].append({
                        'id': model_id,
                        'name': model_info['display_name'],
                        'cost_per_1k_tokens': model_info['cost_per_1k_tokens'],
                        'provider': provider
                    })
        
        return available_models
    
    def calculate_cost(self, model_name: str, provider: str, tokens: int) -> float:
        """Calculate cost for a specific model and token count"""
        if provider in self.config.AI_MODELS and model_name in self.config.AI_MODELS[provider]:
            cost_per_1k = self.config.AI_MODELS[provider][model_name]['cost_per_1k_tokens']
            return (tokens / 1000) * cost_per_1k
        return 0.0
    
    def prepare_messages(self, user_message: str, chat_session: ChatSession = None, 
                        system_prompt: str = None) -> List[Dict]:
        """Prepare messages for AI completion"""
        messages = []
        
        # Add system prompt if provided
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        # Add chat history if available
        if chat_session:
            context_messages = chat_session.get_context_messages(max_messages=20)
            for msg in context_messages[:-1]:  # Exclude the last message (current one)
                messages.append({
                    "role": msg['role'],
                    "content": msg['content']
                })
        
        # Add current user message
        messages.append({"role": "user", "content": user_message})
        
        return messages
    
    async def chat_completion(self, user: User, model_name: str, provider: str, 
                            messages: List[Dict], stream: bool = True, 
                            chat_session: ChatSession = None) -> AsyncGenerator[str, None]:
        """
        Generate chat completion with streaming support
        """
        start_time = time.time()
        full_response = ""
        input_tokens = 0
        output_tokens = 0
        
        try:
            # Check user budget
            estimated_cost = self.calculate_cost(model_name, provider, 1000)  # Rough estimate
            if not user.has_budget_available(estimated_cost):
                yield f"❌ Budget exceeded! Current usage: ${user.current_usage:.2f} / ${user.monthly_budget:.2f}"
                return
            
            # Handle different providers
            if provider == 'ollama':
                async for chunk in self._ollama_completion(model_name, messages, stream):
                    full_response += chunk
                    yield chunk
                output_tokens = len(full_response.split())  # Rough token count
                input_tokens = sum(len(msg['content'].split()) for msg in messages)
            
            else:
                # Use LiteLLM for cloud providers
                model_identifier = f"{provider}/{model_name}" if provider != 'openai' else model_name
                
                if stream:
                    response = await acompletion(
                        model=model_identifier,
                        messages=messages,
                        stream=True,
                        max_tokens=user.max_tokens_per_request
                    )
                    
                    async for chunk in response:
                        if chunk.choices[0].delta.content:
                            content = chunk.choices[0].delta.content
                            full_response += content
                            yield content
                        
                        # Extract token usage if available
                        if hasattr(chunk, 'usage') and chunk.usage:
                            input_tokens = chunk.usage.prompt_tokens or 0
                            output_tokens = chunk.usage.completion_tokens or 0
                
                else:
                    response = await acompletion(
                        model=model_identifier,
                        messages=messages,
                        max_tokens=user.max_tokens_per_request
                    )
                    
                    full_response = response.choices[0].message.content
                    input_tokens = response.usage.prompt_tokens or 0
                    output_tokens = response.usage.completion_tokens or 0
                    yield full_response
            
            # Calculate actual cost
            total_tokens = input_tokens + output_tokens
            actual_cost = self.calculate_cost(model_name, provider, total_tokens)
            
            # Log usage
            response_time = time.time() - start_time
            UsageLog.log_usage(
                user_id=user.id,
                model_name=model_name,
                provider=provider,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost=actual_cost,
                response_time=response_time,
                status='success',
                chat_session_id=chat_session.id if chat_session else None
            )
            
            # Update user usage
            user.add_usage(actual_cost)
            
            # Add to chat session if provided
            if chat_session:
                chat_session.add_message(
                    role='assistant',
                    content=full_response,
                    model=f"{provider}/{model_name}",
                    tokens=total_tokens,
                    cost=actual_cost
                )
        
        except Exception as e:
            error_msg = f"Error with {provider}/{model_name}: {str(e)}"
            
            # Log error
            UsageLog.log_usage(
                user_id=user.id,
                model_name=model_name,
                provider=provider,
                status='error',
                error_message=error_msg,
                response_time=time.time() - start_time,
                chat_session_id=chat_session.id if chat_session else None
            )
            
            yield f"❌ {error_msg}"
    
    async def _ollama_completion(self, model_name: str, messages: List[Dict], 
                               stream: bool = True) -> AsyncGenerator[str, None]:
        """Handle Ollama local model completion"""
        try:
            # Convert messages to Ollama format
            prompt = self._messages_to_prompt(messages)
            
            payload = {
                "model": model_name,
                "prompt": prompt,
                "stream": stream
            }
            
            response = requests.post(
                f"{self.config.OLLAMA_BASE_URL}/api/generate",
                json=payload,
                stream=stream
            )
            
            if stream:
                for line in response.iter_lines():
                    if line:
                        try:
                            chunk = json.loads(line.decode('utf-8'))
                            if 'response' in chunk:
                                yield chunk['response']
                        except json.JSONDecodeError:
                            continue
            else:
                result = response.json()
                yield result.get('response', '')
                
        except Exception as e:
            yield f"Ollama error: {str(e)}"
    
    def _messages_to_prompt(self, messages: List[Dict]) -> str:
        """Convert messages to a simple prompt for Ollama"""
        prompt_parts = []
        
        for message in messages:
            role = message['role']
            content = message['content']
            
            if role == 'system':
                prompt_parts.append(f"System: {content}")
            elif role == 'user':
                prompt_parts.append(f"Human: {content}")
            elif role == 'assistant':
                prompt_parts.append(f"Assistant: {content}")
        
        prompt_parts.append("Assistant:")
        return "\n\n".join(prompt_parts)
    
    def compare_models(self, user: User, prompt: str, models: List[Dict]) -> Dict:
        """
        Compare multiple models side by side
        Returns a dictionary with model responses
        """
        results = {}
        
        for model_info in models:
            model_name = model_info['model']
            provider = model_info['provider']
            
            if not user.can_use_model(provider):
                results[f"{provider}/{model_name}"] = {
                    'error': 'Access denied to this model'
                }
                continue
            
            try:
                # Prepare messages
                messages = [{"role": "user", "content": prompt}]
                
                # Get response (non-streaming for comparison)
                start_time = time.time()
                
                if provider == 'ollama':
                    # Handle Ollama differently
                    response_text = asyncio.run(self._get_ollama_response(model_name, messages))
                else:
                    model_identifier = f"{provider}/{model_name}" if provider != 'openai' else model_name
                    response = completion(
                        model=model_identifier,
                        messages=messages,
                        max_tokens=user.max_tokens_per_request
                    )
                    response_text = response.choices[0].message.content
                
                response_time = time.time() - start_time
                
                results[f"{provider}/{model_name}"] = {
                    'response': response_text,
                    'response_time': round(response_time, 2),
                    'model_display_name': self.config.AI_MODELS.get(provider, {}).get(model_name, {}).get('display_name', model_name)
                }
                
            except Exception as e:
                results[f"{provider}/{model_name}"] = {
                    'error': str(e)
                }
        
        return results
    
    async def _get_ollama_response(self, model_name: str, messages: List[Dict]) -> str:
        """Get non-streaming response from Ollama"""
        prompt = self._messages_to_prompt(messages)
        
        payload = {
            "model": model_name,
            "prompt": prompt,
            "stream": False
        }
        
        response = requests.post(
            f"{self.config.OLLAMA_BASE_URL}/api/generate",
            json=payload
        )
        
        return response.json().get('response', 'No response from Ollama')
    
    def get_user_usage_stats(self, user: User, days: int = 30) -> Dict:
        """Get usage statistics for a user"""
        from sqlalchemy import func
        from datetime import timedelta
        
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        # Get usage logs for the period
        usage_logs = UsageLog.query.filter(
            UsageLog.user_id == user.id,
            UsageLog.request_time >= cutoff_date
        ).all()
        
        stats = {
            'total_requests': len(usage_logs),
            'total_tokens': sum(log.total_tokens for log in usage_logs),
            'total_cost': sum(log.cost for log in usage_logs),
            'current_month_usage': user.current_usage,
            'monthly_budget': user.monthly_budget,
            'budget_remaining': user.monthly_budget - user.current_usage,
            'models_used': {},
            'providers_used': {},
            'daily_usage': {}
        }
        
        # Aggregate by models and providers
        for log in usage_logs:
            # Models
            if log.model_name not in stats['models_used']:
                stats['models_used'][log.model_name] = {
                    'requests': 0,
                    'tokens': 0,
                    'cost': 0.0
                }
            stats['models_used'][log.model_name]['requests'] += 1
            stats['models_used'][log.model_name]['tokens'] += log.total_tokens
            stats['models_used'][log.model_name]['cost'] += log.cost
            
            # Providers
            if log.provider not in stats['providers_used']:
                stats['providers_used'][log.provider] = {
                    'requests': 0,
                    'tokens': 0,
                    'cost': 0.0
                }
            stats['providers_used'][log.provider]['requests'] += 1
            stats['providers_used'][log.provider]['tokens'] += log.total_tokens
            stats['providers_used'][log.provider]['cost'] += log.cost
            
            # Daily usage
            day_key = log.request_time.strftime('%Y-%m-%d')
            if day_key not in stats['daily_usage']:
                stats['daily_usage'][day_key] = {
                    'requests': 0,
                    'tokens': 0,
                    'cost': 0.0
                }
            stats['daily_usage'][day_key]['requests'] += 1
            stats['daily_usage'][day_key]['tokens'] += log.total_tokens
            stats['daily_usage'][day_key]['cost'] += log.cost
        
        return stats 