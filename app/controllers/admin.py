from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from sqlalchemy import func, desc
from datetime import datetime, timezone, timedelta
import json

from app.models.user import User, ChatSession, UsageLog, db
from app.services.ai_service import AIService
from app.config import Config

admin = Blueprint('admin', __name__, url_prefix='/admin')
ai_service = AIService()
config = Config()

def admin_required(f):
    """Decorator to require admin role"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Access denied. Admin privileges required.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

@admin.route('/')
@login_required
@admin_required
def admin_dashboard():
    """Admin dashboard with system overview"""
    # Get system statistics
    total_users = User.query.count()
    active_users = User.query.filter_by(is_active=True).count()
    total_sessions = ChatSession.query.count()
    
    # Usage statistics for last 30 days
    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
    recent_usage = UsageLog.query.filter(UsageLog.request_time >= thirty_days_ago).all()
    
    total_requests = len(recent_usage)
    total_tokens = sum(log.total_tokens for log in recent_usage)
    total_cost = sum(log.cost for log in recent_usage)
    
    # Top users by usage
    top_users_query = db.session.query(
        User.username,
        User.current_usage,
        User.monthly_budget,
        func.count(UsageLog.id).label('request_count')
    ).join(UsageLog).filter(
        UsageLog.request_time >= thirty_days_ago
    ).group_by(User.id).order_by(desc('request_count')).limit(10).all()
    
    # Model usage statistics
    model_stats = {}
    provider_stats = {}
    
    for log in recent_usage:
        # Models
        if log.model_name not in model_stats:
            model_stats[log.model_name] = {'requests': 0, 'tokens': 0, 'cost': 0.0}
        model_stats[log.model_name]['requests'] += 1
        model_stats[log.model_name]['tokens'] += log.total_tokens
        model_stats[log.model_name]['cost'] += log.cost
        
        # Providers
        if log.provider not in provider_stats:
            provider_stats[log.provider] = {'requests': 0, 'tokens': 0, 'cost': 0.0}
        provider_stats[log.provider]['requests'] += 1
        provider_stats[log.provider]['tokens'] += log.total_tokens
        provider_stats[log.provider]['cost'] += log.cost
    
    # Daily usage for chart
    daily_usage = {}
    for i in range(30):
        date = (datetime.now(timezone.utc) - timedelta(days=i)).strftime('%Y-%m-%d')
        daily_usage[date] = {'requests': 0, 'tokens': 0, 'cost': 0.0}
    
    for log in recent_usage:
        date_key = log.request_time.strftime('%Y-%m-%d')
        if date_key in daily_usage:
            daily_usage[date_key]['requests'] += 1
            daily_usage[date_key]['tokens'] += log.total_tokens
            daily_usage[date_key]['cost'] += log.cost
    
    return render_template('admin/dashboard.html',
                         total_users=total_users,
                         active_users=active_users,
                         total_sessions=total_sessions,
                         total_requests=total_requests,
                         total_tokens=total_tokens,
                         total_cost=total_cost,
                         top_users=top_users_query,
                         model_stats=model_stats,
                         provider_stats=provider_stats,
                         daily_usage=daily_usage)

@admin.route('/users')
@login_required
@admin_required
def manage_users():
    """User management page"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    users = User.query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('admin/users.html', users=users)

@admin.route('/api/users')
@login_required
@admin_required
def api_get_users():
    """API endpoint to get users with filters"""
    try:
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        search = request.args.get('search', '').strip()
        role_filter = request.args.get('role', '').strip()
        status_filter = request.args.get('status', '').strip()
        
        # Build query
        query = User.query
        
        if search:
            query = query.filter(
                (User.username.contains(search)) |
                (User.email.contains(search))
            )
        
        if role_filter:
            query = query.filter(User.role == role_filter)
        
        if status_filter == 'active':
            query = query.filter(User.is_active == True)
        elif status_filter == 'inactive':
            query = query.filter(User.is_active == False)
        
        # Paginate
        users = query.order_by(User.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        # Convert to dict
        user_list = []
        for user in users.items:
            user_data = user.to_dict()
            # Add usage stats
            user_data['usage_percentage'] = (user.current_usage / user.monthly_budget * 100) if user.monthly_budget > 0 else 0
            user_list.append(user_data)
        
        return jsonify({
            'users': user_list,
            'pagination': {
                'page': users.page,
                'pages': users.pages,
                'per_page': users.per_page,
                'total': users.total,
                'has_next': users.has_next,
                'has_prev': users.has_prev
            }
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin.route('/api/users/<int:user_id>', methods=['PUT'])
@login_required
@admin_required
def api_update_user(user_id):
    """Update user settings"""
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.json
        
        # Update allowed fields
        if 'role' in data and data['role'] in config.USER_ROLES:
            user.role = data['role']
        
        if 'monthly_budget' in data:
            budget = float(data['monthly_budget'])
            max_budget = config.USER_ROLES.get(user.role, {}).get('max_budget', 1000.0)
            if 0 <= budget <= max_budget:
                user.monthly_budget = budget
        
        if 'is_active' in data:
            user.is_active = bool(data['is_active'])
        
        if 'allowed_models' in data:
            if isinstance(data['allowed_models'], list):
                user.set_allowed_models(data['allowed_models'])
        
        if 'max_tokens_per_request' in data:
            tokens = int(data['max_tokens_per_request'])
            if 100 <= tokens <= 8000:
                user.max_tokens_per_request = tokens
        
        if 'system_prompt' in data:
            user.system_prompt = data['system_prompt'][:2000]  # Limit length
        
        if 'guardrails_enabled' in data:
            user.guardrails_enabled = bool(data['guardrails_enabled'])
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'User updated successfully',
            'user': user.to_dict()
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin.route('/api/users/<int:user_id>/reset-usage', methods=['POST'])
@login_required
@admin_required
def api_reset_user_usage(user_id):
    """Reset user's monthly usage"""
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        user.reset_monthly_usage()
        
        return jsonify({
            'success': True,
            'message': f'Usage reset for {user.username}',
            'user': user.to_dict()
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin.route('/api/users/<int:user_id>/chat-history')
@login_required
@admin_required
def api_get_user_chats(user_id):
    """Get user's chat history (admin monitoring)"""
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get recent chat sessions
        sessions = ChatSession.query.filter_by(
            user_id=user_id,
            is_active=True
        ).order_by(ChatSession.updated_at.desc()).limit(50).all()
        
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
                'message_count': len(session.get_messages()),
                'messages': session.get_messages()  # Include full messages for admin
            }
            session_list.append(session_data)
        
        return jsonify({
            'user': user.to_dict(),
            'chat_sessions': session_list
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin.route('/api/usage-analytics')
@login_required
@admin_required
def api_usage_analytics():
    """Get detailed usage analytics"""
    try:
        days = request.args.get('days', 30, type=int)
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        # Get usage logs
        usage_logs = UsageLog.query.filter(
            UsageLog.request_time >= cutoff_date
        ).all()
        
        # Aggregate data
        analytics = {
            'total_requests': len(usage_logs),
            'total_tokens': sum(log.total_tokens for log in usage_logs),
            'total_cost': sum(log.cost for log in usage_logs),
            'average_response_time': sum(log.response_time for log in usage_logs if log.response_time) / len(usage_logs) if usage_logs else 0,
            'success_rate': len([log for log in usage_logs if log.status == 'success']) / len(usage_logs) * 100 if usage_logs else 0,
            'models': {},
            'providers': {},
            'users': {},
            'daily_breakdown': {},
            'hourly_pattern': {},
            'error_analysis': {}
        }
        
        # Aggregate by different dimensions
        for log in usage_logs:
            # Models
            if log.model_name not in analytics['models']:
                analytics['models'][log.model_name] = {
                    'requests': 0, 'tokens': 0, 'cost': 0.0, 'avg_response_time': 0
                }
            analytics['models'][log.model_name]['requests'] += 1
            analytics['models'][log.model_name]['tokens'] += log.total_tokens
            analytics['models'][log.model_name]['cost'] += log.cost
            if log.response_time:
                analytics['models'][log.model_name]['avg_response_time'] += log.response_time
            
            # Providers
            if log.provider not in analytics['providers']:
                analytics['providers'][log.provider] = {
                    'requests': 0, 'tokens': 0, 'cost': 0.0
                }
            analytics['providers'][log.provider]['requests'] += 1
            analytics['providers'][log.provider]['tokens'] += log.total_tokens
            analytics['providers'][log.provider]['cost'] += log.cost
            
            # Users (anonymized for privacy)
            user_key = f"user_{log.user_id}"
            if user_key not in analytics['users']:
                analytics['users'][user_key] = {
                    'requests': 0, 'tokens': 0, 'cost': 0.0
                }
            analytics['users'][user_key]['requests'] += 1
            analytics['users'][user_key]['tokens'] += log.total_tokens
            analytics['users'][user_key]['cost'] += log.cost
            
            # Daily breakdown
            day_key = log.request_time.strftime('%Y-%m-%d')
            if day_key not in analytics['daily_breakdown']:
                analytics['daily_breakdown'][day_key] = {
                    'requests': 0, 'tokens': 0, 'cost': 0.0
                }
            analytics['daily_breakdown'][day_key]['requests'] += 1
            analytics['daily_breakdown'][day_key]['tokens'] += log.total_tokens
            analytics['daily_breakdown'][day_key]['cost'] += log.cost
            
            # Hourly pattern
            hour_key = log.request_time.strftime('%H')
            if hour_key not in analytics['hourly_pattern']:
                analytics['hourly_pattern'][hour_key] = 0
            analytics['hourly_pattern'][hour_key] += 1
            
            # Error analysis
            if log.status != 'success':
                error_key = log.error_message or log.status
                if error_key not in analytics['error_analysis']:
                    analytics['error_analysis'][error_key] = 0
                analytics['error_analysis'][error_key] += 1
        
        # Calculate averages for models
        for model_data in analytics['models'].values():
            if model_data['requests'] > 0:
                model_data['avg_response_time'] /= model_data['requests']
        
        return jsonify(analytics)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin.route('/api/system/health')
@login_required
@admin_required
def api_system_health():
    """Check system health and status"""
    try:
        health_status = {
            'database': 'healthy',
            'ai_providers': {},
            'system_resources': {},
            'active_users': User.query.filter_by(is_active=True).count(),
            'recent_errors': []
        }
        
        # Check AI providers
        try:
            # Test Ollama
            import requests
            response = requests.get(f"{config.OLLAMA_BASE_URL}/api/tags", timeout=5)
            health_status['ai_providers']['ollama'] = 'healthy' if response.status_code == 200 else 'unhealthy'
        except:
            health_status['ai_providers']['ollama'] = 'unreachable'
        
        # Check for recent errors
        recent_errors = UsageLog.query.filter(
            UsageLog.status != 'success',
            UsageLog.request_time >= datetime.now(timezone.utc) - timedelta(hours=1)
        ).limit(10).all()
        
        for error in recent_errors:
            health_status['recent_errors'].append({
                'timestamp': error.request_time.isoformat(),
                'model': error.model_name,
                'provider': error.provider,
                'error': error.error_message
            })
        
        # System resources (if psutil is available)
        try:
            import psutil
            health_status['system_resources'] = {
                'cpu_percent': psutil.cpu_percent(),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_percent': psutil.disk_usage('/').percent
            }
        except ImportError:
            health_status['system_resources'] = {'note': 'psutil not available'}
        
        return jsonify(health_status)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin.route('/api/system/reset-all-usage', methods=['POST'])
@login_required
@admin_required
def api_reset_all_usage():
    """Reset monthly usage for all users (typically run monthly)"""
    try:
        users = User.query.all()
        count = 0
        
        for user in users:
            user.reset_monthly_usage()
            count += 1
        
        return jsonify({
            'success': True,
            'message': f'Reset usage for {count} users'
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500 