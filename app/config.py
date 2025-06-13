import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    # Basic Flask Configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or os.urandom(24)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///enhanced_users.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # AI Provider Configuration
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY')
    GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')
    GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
    
    # Ollama Configuration
    OLLAMA_BASE_URL = os.environ.get('OLLAMA_BASE_URL', 'http://localhost:11434')
    OLLAMA_DEFAULT_MODEL = os.environ.get('OLLAMA_DEFAULT_MODEL', 'llama3')
    
    # LiteLLM Configuration
    LITELLM_MASTER_KEY = os.environ.get('LITELLM_MASTER_KEY', 'sk-' + os.urandom(16).hex())
    LITELLM_SALT_KEY = os.environ.get('LITELLM_SALT_KEY', 'sk-' + os.urandom(16).hex())
    LITELLM_PORT = int(os.environ.get('LITELLM_PORT', '4000'))
    LITELLM_BASE_URL = f"http://localhost:{LITELLM_PORT}"
    
    # Redis Configuration
    REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    
    # Application Settings
    MAX_CHAT_HISTORY = int(os.environ.get('MAX_CHAT_HISTORY', '100'))
    DEFAULT_USER_BUDGET = float(os.environ.get('DEFAULT_USER_BUDGET', '20.00'))
    ENABLE_USAGE_TRACKING = os.environ.get('ENABLE_USAGE_TRACKING', 'True').lower() == 'true'
    
    # Security Settings
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or os.urandom(32)
    BCRYPT_LOG_ROUNDS = int(os.environ.get('BCRYPT_LOG_ROUNDS', '12'))
    
    # Rate Limiting
    RATELIMIT_STORAGE_URL = os.environ.get('RATE_LIMIT_STORAGE_URL', 'redis://localhost:6379/1')
    RATELIMIT_DEFAULT = "100 per hour"
    
    # Available AI Models Configuration
    AI_MODELS = {
        'openai': {
            'gpt-4o': {'display_name': 'GPT-4o', 'cost_per_1k_tokens': 0.005, 'provider': 'openai'},
            'gpt-4o-mini': {'display_name': 'GPT-4o Mini', 'cost_per_1k_tokens': 0.0001, 'provider': 'openai'},
            'gpt-4-turbo': {'display_name': 'GPT-4 Turbo', 'cost_per_1k_tokens': 0.01, 'provider': 'openai'},
            'gpt-3.5-turbo': {'display_name': 'GPT-3.5 Turbo', 'cost_per_1k_tokens': 0.0005, 'provider': 'openai'},
        },
        'anthropic': {
            'claude-3-5-sonnet-20241022': {'display_name': 'Claude 3.5 Sonnet', 'cost_per_1k_tokens': 0.003, 'provider': 'anthropic'},
            'claude-3-haiku-20240307': {'display_name': 'Claude 3 Haiku', 'cost_per_1k_tokens': 0.00025, 'provider': 'anthropic'},
            'claude-3-opus-20240229': {'display_name': 'Claude 3 Opus', 'cost_per_1k_tokens': 0.015, 'provider': 'anthropic'},
        },
        'google': {
            'gemini-1.5-pro': {'display_name': 'Gemini 1.5 Pro', 'cost_per_1k_tokens': 0.0035, 'provider': 'google'},
            'gemini-1.5-flash': {'display_name': 'Gemini 1.5 Flash', 'cost_per_1k_tokens': 0.0001, 'provider': 'google'},
        },
        'groq': {
            'llama-3.1-70b-versatile': {'display_name': 'Llama 3.1 70B', 'cost_per_1k_tokens': 0.0008, 'provider': 'groq'},
            'llama-3.1-8b-instant': {'display_name': 'Llama 3.1 8B', 'cost_per_1k_tokens': 0.0001, 'provider': 'groq'},
            'mixtral-8x7b-32768': {'display_name': 'Mixtral 8x7B', 'cost_per_1k_tokens': 0.0006, 'provider': 'groq'},
        },
        'ollama': {
            'llama3': {'display_name': 'Llama 3 (Local)', 'cost_per_1k_tokens': 0.0, 'provider': 'ollama'},
            'llama3.1': {'display_name': 'Llama 3.1 (Local)', 'cost_per_1k_tokens': 0.0, 'provider': 'ollama'},
            'mistral': {'display_name': 'Mistral (Local)', 'cost_per_1k_tokens': 0.0, 'provider': 'ollama'},
            'codellama': {'display_name': 'Code Llama (Local)', 'cost_per_1k_tokens': 0.0, 'provider': 'ollama'},
        }
    }
    
    # User Roles and Permissions
    USER_ROLES = {
        'admin': {
            'can_manage_users': True,
            'can_view_all_chats': True,
            'can_set_budgets': True,
            'can_access_admin_panel': True,
            'default_models': list(AI_MODELS.keys()),
            'max_budget': 1000.0
        },
        'premium': {
            'can_manage_users': False,
            'can_view_all_chats': False,
            'can_set_budgets': False,
            'can_access_admin_panel': False,
            'default_models': ['openai', 'anthropic', 'google', 'ollama'],
            'max_budget': 100.0
        },
        'standard': {
            'can_manage_users': False,
            'can_view_all_chats': False,
            'can_set_budgets': False,
            'can_access_admin_panel': False,
            'default_models': ['openai', 'ollama'],
            'max_budget': 20.0
        },
        'basic': {
            'can_manage_users': False,
            'can_view_all_chats': False,
            'can_set_budgets': False,
            'can_access_admin_panel': False,
            'default_models': ['ollama'],
            'max_budget': 0.0
        }
    }

class DevelopmentConfig(Config):
    DEBUG = True
    FLASK_ENV = 'development'

class ProductionConfig(Config):
    DEBUG = False
    FLASK_ENV = 'production'
    
    # Stricter security settings for production
    BCRYPT_LOG_ROUNDS = 15
    RATELIMIT_DEFAULT = "50 per hour"

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
} 