from flask import Flask, request, jsonify
import subprocess
import os

app = Flask(__name__)

# Caminho para o executável whisper.cpp e o modelo
WHISPER_CPP_PATH = "/app/whisper.cpp"
MODEL_PATH = os.path.join(WHISPER_CPP_PATH, "models", "ggml-base.en.bin") # Pode ser alterado para outro modelo

@app.route("/transcribe", methods=["POST"])
def transcribe_audio():
    if "audio" not in request.files:
        return jsonify({"error": "No audio file provided"}), 400

    audio_file = request.files["audio"]
    # Salvar o ficheiro de áudio temporariamente
    temp_file_path = os.path.join("/tmp", audio_file.filename)
    audio_file.save(temp_file_path)

    try:
        # Comando para executar o whisper.cpp
        # -l pt para português, ajuste conforme necessário
        command = [os.path.join(WHISPER_CPP_PATH, "main"), "-m", MODEL_PATH, "-f", temp_file_path, "-l", "pt"]
        process = subprocess.run(command, capture_output=True, text=True, check=True)
        transcription = process.stdout.strip()
        return jsonify({"transcription": transcription}), 200
    except subprocess.CalledProcessError as e:
        return jsonify({"error": f"Transcription failed: {e.stderr}"}), 500
    finally:
        # Remover o ficheiro temporário
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "healthy", "service": "whisper-api"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001) 