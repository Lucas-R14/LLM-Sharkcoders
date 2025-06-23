from flask import Blueprint, request, jsonify, Response, render_template, redirect, url_for
from flask_login import login_required, current_user
import json
import asyncio
import requests
import os
from datetime import datetime, timezone

from app.models.user import User, ChatSession, UsageLog, db
from app.services.ai_service import AIService
from app.config import Config

chat = Blueprint('chat', __name__)
ai_service = AIService()
config = Config()

@chat.route('/chat')
@login_required
def chat_page():
    """Simple chat page"""
    return render_template('chat.html', username=current_user.username)

@chat.route('/chat/multi-model')
@login_required
def multi_model_chat():
    """Multi-model comparison chat page"""
    available_models = ai_service.get_available_models(current_user)
    return render_template('chat/multi_model.html',
                         username=current_user.username,
                         available_models=available_models)

@chat.route('/api/chat/single', methods=['POST'])
@login_required
def chat_single_model():
    """Chat with a single AI model with streaming"""
    try:
        data = request.json
        user_message = data.get('message', '').strip()
        model_name = data.get('model', current_user.default_model)
        provider = data.get('provider', 'ollama')
        session_id = data.get('session_id')
        
        if not user_message:
            return jsonify({'error': 'No message provided'}), 400
        
        # Check if user can use this model
        if not current_user.can_use_model(provider):
            return jsonify({'error': f'Access denied to {provider} models'}), 403
        
        # Get or create chat session
        chat_session = None
        if session_id:
            chat_session = ChatSession.query.filter_by(
                id=session_id,
                user_id=current_user.id
            ).first()
        
        if not chat_session:
            chat_session = ChatSession(
                user_id=current_user.id,
                title=user_message[:50] + '...' if len(user_message) > 50 else user_message
            )
            db.session.add(chat_session)
            db.session.commit()
        
        # Add user message to session
        chat_session.add_message('user', user_message)
        
        # Prepare messages for AI
        system_prompt = current_user.system_prompt if current_user.guardrails_enabled else None
        messages = ai_service.prepare_messages(
            user_message, 
            chat_session, 
            system_prompt
        )
        
        # Create async generator for streaming
        async def generate():
            try:
                yield f"data: {json.dumps({'session_id': chat_session.id, 'type': 'session_info'})}\n\n"
                
                response_buffer = ""
                async for chunk in ai_service.chat_completion(
                    user=current_user,
                    model_name=model_name,
                    provider=provider,
                    messages=messages,
                    stream=True,
                    chat_session=chat_session
                ):
                    response_buffer += chunk
                    yield f"data: {json.dumps({'content': chunk, 'type': 'content'})}\n\n"
                
                # Send completion signal
                yield f"data: {json.dumps({'type': 'complete', 'full_response': response_buffer})}\n\n"
                
            except Exception as e:
                yield f"data: {json.dumps({'error': str(e), 'type': 'error'})}\n\n"
        
        # Run async generator in sync context
        def sync_generate():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                async_gen = generate()
                while True:
                    try:
                        result = loop.run_until_complete(async_gen.__anext__())
                        yield result
                    except StopAsyncIteration:
                        break
            finally:
                loop.close()
        
        return Response(sync_generate(), mimetype='text/event-stream',
                       headers={'Cache-Control': 'no-cache',
                               'Connection': 'keep-alive'})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@chat.route('/api/chat/multi-model', methods=['POST'])
@login_required
def chat_multi_model():
    """Compare responses from multiple models"""
    try:
        data = request.json
        user_message = data.get('message', '').strip()
        selected_models = data.get('models', [])
        
        if not user_message:
            return jsonify({'error': 'No message provided'}), 400
        
        if not selected_models:
            return jsonify({'error': 'No models selected'}), 400
        
        # Validate user access to models
        valid_models = []
        for model_info in selected_models:
            provider = model_info.get('provider')
            if current_user.can_use_model(provider):
                valid_models.append(model_info)
        
        if not valid_models:
            return jsonify({'error': 'No accessible models selected'}), 403
        
        # Get responses from all models
        results = ai_service.compare_models(current_user, user_message, valid_models)
        
        return jsonify({
            'success': True,
            'prompt': user_message,
            'results': results,
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@chat.route('/api/chat/sessions')
@login_required
def get_chat_sessions():
    """Get user's chat sessions"""
    try:
        sessions = ChatSession.query.filter_by(
            user_id=current_user.id,
            is_active=True
        ).order_by(ChatSession.updated_at.desc()).all()
        
        session_list = []
        for session in sessions:
            session_data = {
                'id': session.id,
                'title': session.title,
                'created_at': session.created_at.isoformat(),
                'updated_at': session.updated_at.isoformat(),
                'total_tokens': session.total_tokens,
                'total_cost': session.total_cost,
                'model_used': session.model_used,
                'message_count': len(session.get_messages())
            }
            session_list.append(session_data)
        
        return jsonify({'sessions': session_list})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@chat.route('/api/chat/sessions/<int:session_id>')
@login_required
def get_chat_session(session_id):
    """Get specific chat session with messages"""
    try:
        session = ChatSession.query.filter_by(
            id=session_id,
            user_id=current_user.id
        ).first()
        
        if not session:
            return jsonify({'error': 'Session not found'}), 404
        
        return jsonify({
            'session': {
                'id': session.id,
                'title': session.title,
                'created_at': session.created_at.isoformat(),
                'updated_at': session.updated_at.isoformat(),
                'messages': session.get_messages(),
                'total_tokens': session.total_tokens,
                'total_cost': session.total_cost,
                'model_used': session.model_used
            }
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@chat.route('/api/chat/sessions/<int:session_id>', methods=['DELETE'])
@login_required
def delete_chat_session(session_id):
    """Delete a chat session"""
    try:
        session = ChatSession.query.filter_by(
            id=session_id,
            user_id=current_user.id
        ).first()
        
        if not session:
            return jsonify({'error': 'Session not found'}), 404
        
        session.is_active = False
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Session deleted'})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@chat.route('/api/user/stats')
@login_required
def get_user_stats():
    """Get user usage statistics"""
    try:
        stats = ai_service.get_user_usage_stats(current_user, days=30)
        return jsonify(stats)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@chat.route('/api/models/available')
@login_required
def get_available_models():
    """Get available models for current user"""
    try:
        models = ai_service.get_available_models(current_user)
        return jsonify({'models': models})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@chat.route('/api/user/preferences', methods=['POST'])
@login_required
def update_user_preferences():
    """Update user preferences"""
    try:
        data = request.json
        
        # Update allowed fields
        if 'default_model' in data:
            current_user.default_model = data['default_model']
        
        if 'max_tokens_per_request' in data:
            tokens = int(data['max_tokens_per_request'])
            if 100 <= tokens <= 4000:  # Reasonable limits
                current_user.max_tokens_per_request = tokens
        
        if 'enable_streaming' in data:
            current_user.enable_streaming = bool(data['enable_streaming'])
        
        if 'system_prompt' in data:
            current_user.system_prompt = data['system_prompt'][:1000]  # Limit length
        
        if 'guardrails_enabled' in data:
            current_user.guardrails_enabled = bool(data['guardrails_enabled'])
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Preferences updated',
            'user': current_user.to_dict()
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@chat.route('/api/chat/export/<int:session_id>')
@login_required
def export_chat_session(session_id):
    """Export chat session as JSON"""
    try:
        session = ChatSession.query.filter_by(
            id=session_id,
            user_id=current_user.id
        ).first()
        
        if not session:
            return jsonify({'error': 'Session not found'}), 404
        
        export_data = {
            'session_info': {
                'id': session.id,
                'title': session.title,
                'created_at': session.created_at.isoformat(),
                'model_used': session.model_used,
                'total_tokens': session.total_tokens,
                'total_cost': session.total_cost
            },
            'messages': session.get_messages(),
            'exported_at': datetime.now(timezone.utc).isoformat(),
            'exported_by': current_user.username
        }
        
        return Response(
            json.dumps(export_data, indent=2),
            mimetype='application/json',
            headers={
                'Content-Disposition': f'attachment; filename=chat_session_{session_id}.json'
            }
        )
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@chat.route('/api/audio/transcribe', methods=['POST'])
@login_required
def transcribe_audio():
    """Transcribe audio using Whisper API"""
    try:
        if 'audio' not in request.files:
            return jsonify({'error': 'No audio file provided'}), 400
        
        audio_file = request.files['audio']
        
        # Forward to Whisper API
        whisper_url = 'http://whisper-api:5001/transcribe'
        files = {'audio': (audio_file.filename, audio_file.stream, audio_file.content_type)}
        
        response = requests.post(whisper_url, files=files, timeout=30)
        
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({'error': 'Transcription failed'}), 500
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@chat.route('/api/image/generate', methods=['POST'])
@login_required
def generate_image():
    """Generate image using Stable Diffusion API"""
    try:
        data = request.json
        prompt = data.get('prompt', '').strip()
        
        if not prompt:
            return jsonify({'error': 'No prompt provided'}), 400
        
        # Check if user has budget for image generation (approximate cost)
        image_cost = 0.05  # Approximate cost per image
        if not current_user.has_budget_available(image_cost):
            return jsonify({'error': 'Insufficient budget for image generation'}), 403
        
        # Forward to Stable Diffusion API
        sd_url = 'http://stable-diffusion-webui:7860/sdapi/v1/txt2img'
        
        payload = {
            "prompt": prompt,
            "negative_prompt": "blur, low quality, distorted",
            "steps": 20,
            "sampler_index": "Euler a",
            "width": 512,
            "height": 512,
            "cfg_scale": 7,
            "batch_size": 1,
            "n_iter": 1,
        }
        
        response = requests.post(sd_url, json=payload, timeout=120)
        
        if response.status_code == 200:
            result = response.json()
            
            # Add usage cost
            current_user.add_usage(image_cost)
            
            # Log usage
            UsageLog.log_usage(
                user_id=current_user.id,
                model_name='stable-diffusion',
                provider='local',
                cost=image_cost,
                status='success'
            )
            
            return jsonify({
                'success': True,
                'images': result.get('images', []),
                'prompt': prompt,
                'cost': image_cost
            })
        else:
            return jsonify({'error': 'Image generation failed'}), 500
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@chat.route('/api/services/status')
@login_required
def get_services_status():
    """Check status of all AI services"""
    try:
        services = {
            'ollama': False,
            'whisper': False,
            'stable_diffusion': False,
            'open_webui': False
        }
        
        # Check Ollama
        try:
            response = requests.get('http://ollama:11434/api/tags', timeout=5)
            services['ollama'] = response.status_code == 200
        except:
            pass
        
        # Check Whisper API
        try:
            response = requests.get('http://whisper-api:5001/health', timeout=5)
            services['whisper'] = response.status_code == 200
        except:
            pass
        
        # Check Stable Diffusion
        try:
            response = requests.get('http://stable-diffusion-webui:7860/internal/ping', timeout=5)
            services['stable_diffusion'] = response.status_code == 200
        except:
            pass
        
        # Check Open WebUI
        try:
            response = requests.get('http://open-webui:8080/health', timeout=5)
            services['open_webui'] = response.status_code == 200
        except:
            pass
        
        return jsonify({'services': services})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500 