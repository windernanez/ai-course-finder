from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from buscador_ia import BuscadorCursosIA
from chatbot_gemini import ChatbotGemini
import os
from dotenv import load_dotenv
import sys

# 1. Ajuste de Path para Railway
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

# Configuración de carpetas estáticas
app = Flask(__name__, 
            static_folder='../frontend', 
            static_url_path='')

# Configuración de CORS para permitir peticiones desde tu terminal y el frontend
CORS(app, resources={r"/api/*": {"origins": "*"}})

YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY', '')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')

# Inicialización de servicios
buscador = BuscadorCursosIA(YOUTUBE_API_KEY)
chatbot = ChatbotGemini(GEMINI_API_KEY)

@app.route('/')
def servir_frontend():
    try:
        return send_from_directory(app.static_folder, 'index.html')
    except:
        return jsonify({
            "mensaje": "API de AI Course Finder Activa", 
            "status": "online",
            "info": "Para usar la API usa los endpoints /api/buscar o /api/chat"
        }), 200

# --- ENDPOINT: BUSCADOR DE CURSOS ---
@app.route('/api/buscar', methods=['POST', 'OPTIONS'])
def buscar_cursos():
    if request.method == 'OPTIONS':
        return jsonify({"status": "ok"}), 200
        
    data = request.json
    if not data:
        return jsonify({"error": "No se recibieron datos"}), 400
        
    lenguaje = data.get('lenguaje', '')
    nivel = data.get('nivel', 'principiante')
    
    try:
        resultado = buscador.buscar_videos(lenguaje, nivel)
        return jsonify(resultado)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- ENDPOINT: CHATBOT DIRECTO ---
@app.route('/api/chat', methods=['POST', 'OPTIONS'])
def chat():
    if request.method == 'OPTIONS':
        return jsonify({"status": "ok"}), 200

    data = request.json
    mensaje = data.get('mensaje', '')
    
    if not mensaje:
        return jsonify({"error": "Mensaje vacío"}), 400

    try:
        respuesta = chatbot.generar_respuesta(mensaje)
        return jsonify({"respuesta": respuesta})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- ENDPOINT: LISTADO DE LENGUAJES ---
@app.route('/api/lenguajes', methods=['GET'])
def listar_lenguajes():
    # Esto es útil para llenar los selects en tu frontend
    lenguajes = ["python", "javascript", "java", "php", "c++", "ruby"]
    return jsonify({"lenguajes": lenguajes})

if __name__ == '__main__':
    # Railway inyecta el puerto automáticamente
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
