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

app = Flask(__name__, 
            static_folder='../frontend', 
            static_url_path='')

# Configuración de CORS: Permite peticiones desde cualquier origen (Vercel, Localhost, etc.)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Variables de entorno
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY', '')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')

# Inicialización de servicios
# Asegúrate de que las API Keys estén configuradas en las variables de Railway
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
            "info": "Backend operativo para el proyecto de maestría."
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
        # Usamos buscar_videos que es el nombre confirmado en tu lógica
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
    # Retorna la lista que el frontend necesita para el selector
    lenguajes = ["python", "javascript", "java", "php", "c++", "ruby"]
    return jsonify({"lenguajes": lenguajes})

# --- ENDPOINT: ESTADÍSTICAS (Para evitar 404 en el Frontend) ---
@app.route('/api/estadisticas', methods=['GET'])
def obtener_estadisticas():
    stats = {
        "cursos_totales": 150,
        "busquedas_exitosas": 1240,
        "usuarios_activos": 85,
        "popularidad": [
            {"name": "Python", "value": 45},
            {"name": "JS", "value": 35},
            {"name": "Otros", "value": 20}
        ]
    }
    return jsonify(stats)

if __name__ == '__main__':
    # Railway inyecta el puerto automáticamente mediante la variable PORT
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
