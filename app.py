from flask import Flask, request, jsonify, render_template, Response
from flask_cors import CORS
import requests
import json

app = Flask(__name__)
CORS(app)

OLLAMA_API_URL = "http://localhost:11434/api/generate"

@app.route('/')
def home():
    return render_template('index.html')

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

if __name__ == '__main__':
    app.run(debug=True) 