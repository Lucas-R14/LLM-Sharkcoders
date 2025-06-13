from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone
import json

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    
    # Enhanced user properties
    role = db.Column(db.String(20), default='standard', nullable=False)
    monthly_budget = db.Column(db.Float, default=20.0, nullable=False)
    current_usage = db.Column(db.Float, default=0.0, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    last_login = db.Column(db.DateTime)
    
    # AI Model access permissions (JSON string)
    allowed_models = db.Column(db.Text, default='["ollama"]')
    
    # User preferences
    default_model = db.Column(db.String(50), default='llama3')
    max_tokens_per_request = db.Column(db.Integer, default=2000)
    enable_streaming = db.Column(db.Boolean, default=True)
    
    # System prompt and guardrails
    system_prompt = db.Column(db.Text, default='')
    guardrails_enabled = db.Column(db.Boolean, default=False)
    
    # Relationships
    chat_sessions = db.relationship('ChatSession', backref='user', lazy=True, cascade='all, delete-orphan')
    usage_logs = db.relationship('UsageLog', backref='user', lazy=True, cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_allowed_models(self):
        """Get list of allowed models for this user"""
        try:
            return json.loads(self.allowed_models)
        except:
            return ['ollama']
    
    def set_allowed_models(self, models_list):
        """Set allowed models for this user"""
        self.allowed_models = json.dumps(models_list)
    
    def can_use_model(self, model_name):
        """Check if user can use a specific model"""
        allowed = self.get_allowed_models()
        return model_name in allowed or 'all' in allowed
    
    def has_budget_available(self, cost=0.0):
        """Check if user has budget available for a request"""
        return (self.current_usage + cost) <= self.monthly_budget
    
    def add_usage(self, cost):
        """Add usage cost to user's current usage"""
        self.current_usage += cost
        db.session.commit()
    
    def reset_monthly_usage(self):
        """Reset monthly usage (typically called at month start)"""
        self.current_usage = 0.0
        db.session.commit()
    
    def update_last_login(self):
        """Update user's last login timestamp"""
        self.last_login = datetime.now(timezone.utc)
        db.session.commit()
    
    def to_dict(self):
        """Convert user to dictionary for API responses"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'monthly_budget': self.monthly_budget,
            'current_usage': self.current_usage,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'allowed_models': self.get_allowed_models(),
            'default_model': self.default_model
        }

    def __repr__(self):
        return f'<User {self.username}>'


class ChatSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), default='New Chat')
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    is_active = db.Column(db.Boolean, default=True)
    
    # Chat messages (JSON string)
    messages = db.Column(db.Text, default='[]')
    
    # Session metadata
    model_used = db.Column(db.String(50))
    total_tokens = db.Column(db.Integer, default=0)
    total_cost = db.Column(db.Float, default=0.0)
    
    def add_message(self, role, content, model=None, tokens=0, cost=0.0):
        """Add a message to the chat session"""
        try:
            messages = json.loads(self.messages)
        except:
            messages = []
        
        message = {
            'role': role,
            'content': content,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'model': model,
            'tokens': tokens,
            'cost': cost
        }
        
        messages.append(message)
        self.messages = json.dumps(messages)
        self.total_tokens += tokens
        self.total_cost += cost
        self.updated_at = datetime.now(timezone.utc)
        
        if model:
            self.model_used = model
        
        db.session.commit()
    
    def get_messages(self):
        """Get chat messages as list"""
        try:
            return json.loads(self.messages)
        except:
            return []
    
    def get_context_messages(self, max_messages=20):
        """Get recent messages for context"""
        messages = self.get_messages()
        return messages[-max_messages:] if len(messages) > max_messages else messages


class UsageLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Request details
    model_name = db.Column(db.String(50), nullable=False)
    provider = db.Column(db.String(30), nullable=False)
    
    # Usage metrics
    input_tokens = db.Column(db.Integer, default=0)
    output_tokens = db.Column(db.Integer, default=0)
    total_tokens = db.Column(db.Integer, default=0)
    cost = db.Column(db.Float, default=0.0)
    
    # Request metadata
    request_time = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    response_time = db.Column(db.Float)  # Response time in seconds
    status = db.Column(db.String(20), default='success')  # success, error, timeout
    error_message = db.Column(db.Text)
    
    # Context
    chat_session_id = db.Column(db.Integer, db.ForeignKey('chat_session.id'))
    
    @staticmethod
    def log_usage(user_id, model_name, provider, input_tokens=0, output_tokens=0, 
                  cost=0.0, response_time=0.0, status='success', error_message=None, 
                  chat_session_id=None):
        """Log usage for analytics and billing"""
        usage = UsageLog(
            user_id=user_id,
            model_name=model_name,
            provider=provider,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            cost=cost,
            response_time=response_time,
            status=status,
            error_message=error_message,
            chat_session_id=chat_session_id
        )
        
        db.session.add(usage)
        db.session.commit()
        
        return usage 