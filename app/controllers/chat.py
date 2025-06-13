from flask import Blueprint, request, jsonify, Response, render_template, redirect, url_for
from flask_login import login_required, current_user
import json
import asyncio
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
    """Enhanced chat page with model selection and features"""
    available_models = ai_service.get_available_models(current_user)
    user_stats = ai_service.get_user_usage_stats(current_user, days=30)
    
    # Get recent chat sessions
    recent_sessions = ChatSession.query.filter_by(
        user_id=current_user.id,
        is_active=True
    ).order_by(ChatSession.updated_at.desc()).limit(10).all()
    
    return render_template('chat/advanced_chat.html',
                         username=current_user.username,
                         available_models=available_models,
                         user_stats=user_stats,
                         recent_sessions=recent_sessions)

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