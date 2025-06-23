from flask import Flask, request, jsonify, render_template, Response, redirect, url_for
from flask_cors import CORS
from flask_login import LoginManager, current_user
from flask_migrate import Migrate
import os

from app.models.user import db, User
from app.controllers.auth import auth
from app.controllers.chat import chat
from app.controllers.admin import admin
from app.config import config
from app.services.ai_service import AIService

def create_app(config_name='development'):
    app = Flask(__name__, 
                template_folder='app/templates', 
                static_folder='app/static')
    
    # Load configuration
    app.config.from_object(config[config_name])
    CORS(app)
    
    # Initialize extensions
    db.init_app(app)
    migrate = Migrate(app, db)
    
    # Initialize Login Manager
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register blueprints
    app.register_blueprint(auth)
    app.register_blueprint(chat)
    app.register_blueprint(admin)
    
    # Initialize AI Service
    ai_service = AIService()

    # Main routes
    @app.route('/')
    def index():
        if current_user.is_authenticated:
            return redirect(url_for('chat.chat_page'))
        return render_template('index.html')

    @app.route('/dashboard')
    def dashboard():
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        
        # Redirect authenticated users to chat page
        return redirect(url_for('chat.chat_page'))

    @app.route('/profile')
    def profile():
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        
        user_stats = ai_service.get_user_usage_stats(current_user, days=30)
        return render_template('profile.html', 
                             username=current_user.username,
                             user=current_user,
                             user_stats=user_stats)

    # Legacy chat route (redirect to new chat)
    @app.route('/chat')
    def legacy_chat():
        return redirect(url_for('chat.chat_page'))

    # Legacy API route (for backward compatibility)
    @app.route('/api/chat', methods=['POST'])
    def legacy_api_chat():
        return redirect(url_for('chat.chat_single_model'), 308)

    # Health check endpoint
    @app.route('/health')
    def health_check():
        return jsonify({
            'status': 'healthy',
            'timestamp': os.environ.get('TIMESTAMP', 'unknown'),
            'version': '2.0.0-enhanced'
        })

    # Favicon route to prevent 404 errors
    @app.route('/favicon.ico')
    def favicon():
        return '', 204

    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500

    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template('errors/403.html'), 403

    # Context processors for templates
    @app.context_processor
    def inject_user_data():
        if current_user.is_authenticated:
            return {
                'current_user': current_user,
                'user_budget_percentage': (current_user.current_usage / current_user.monthly_budget * 100) if current_user.monthly_budget > 0 else 0,
                'available_providers': current_user.get_allowed_models()
            }
        return {}

    # Create database tables and initial admin user
    with app.app_context():
        db.create_all()
        
        # Create initial admin user if doesn't exist
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            admin_user = User(
                username='admin',
                email='admin@localhost',
                role='admin',
                monthly_budget=1000.0,
                is_active=True
            )
            admin_user.set_password('admin123')  # Change this in production!
            admin_user.set_allowed_models(['openai', 'anthropic', 'google', 'groq', 'ollama'])
            db.session.add(admin_user)
            db.session.commit()
            print("✅ Created initial admin user (username: admin, password: admin123)")

    # CLI commands for administration
    @app.cli.command('create-admin')
    def create_admin():
        """Create an admin user via CLI"""
        username = input('Enter admin username: ')
        email = input('Enter admin email: ')
        password = input('Enter admin password: ')
        
        if User.query.filter_by(username=username).first():
            print(f'User {username} already exists!')
            return
        
        admin_user = User(
            username=username,
            email=email,
            role='admin',
            monthly_budget=1000.0,
            is_active=True
        )
        admin_user.set_password(password)
        admin_user.set_allowed_models(['openai', 'anthropic', 'google', 'groq', 'ollama'])
        db.session.add(admin_user)
        db.session.commit()
        print(f'✅ Created admin user: {username}')

    @app.cli.command('reset-usage')
    def reset_monthly_usage():
        """Reset monthly usage for all users"""
        users = User.query.all()
        count = 0
        for user in users:
            user.reset_monthly_usage()
            count += 1
        print(f'✅ Reset usage for {count} users')

    @app.cli.command('list-users')
    def list_users():
        """List all users"""
        users = User.query.all()
        print(f"{'ID':<5} {'Username':<20} {'Email':<30} {'Role':<10} {'Budget':<10} {'Usage':<10} {'Active':<8}")
        print("-" * 95)
        for user in users:
            print(f"{user.id:<5} {user.username:<20} {user.email:<30} {user.role:<10} ${user.monthly_budget:<9.2f} ${user.current_usage:<9.2f} {'Yes' if user.is_active else 'No':<8}")

    return app

if __name__ == '__main__':
    app = create_app('development')
    app.run(debug=True, host='0.0.0.0', port=5000) 