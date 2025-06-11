from flask import Flask, request, jsonify, render_template, Response, redirect, url_for
from flask_cors import CORS
import requests
import json
from flask_login import LoginManager, current_user
from app.models.user import db, User
from app.controllers.auth import auth
import os

OLLAMA_API_URL = "http://localhost:11434/api/generate"

def create_app():
    app = Flask(__name__, 
                template_folder='app/templates', 
                static_folder='app/static')
    CORS(app)
    
    # Configuration
    app.config['SECRET_KEY'] = os.urandom(24)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize extensions
    db.init_app(app)
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register blueprints
    app.register_blueprint(auth)

    # Routes
    @app.route('/')
    def index():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        return render_template('index.html')

    @app.route('/chat')
    def chat_page():
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        return render_template('chat.html', username=current_user.username)

    @app.route('/dashboard')
    def dashboard():
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        return render_template('dashboard.html', username=current_user.username)

    @app.route('/api/chat', methods=['POST'])
    def chat():
        try:
            data = request.json
            user_message = data.get('message', '')

            if not user_message:
                return jsonify({'error': 'No message provided'}), 400

            ollama_request = {
                "model": "llama3",
                "prompt": user_message,
                "stream": True
            }

            def generate():
                with requests.post(OLLAMA_API_URL, json=ollama_request, stream=True) as r:
                    for line in r.iter_lines():
                        if line:
                            try:
                                chunk = json.loads(line.decode('utf-8'))
                                text = chunk.get('response', '')
                                yield f"data: {text}\n\n"
                            except Exception:
                                continue
            return Response(generate(), mimetype='text/event-stream')

        except Exception as e:
            return jsonify({'error': str(e)}), 500

    # Create database tables
    with app.app_context():
        db.create_all()

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True) 