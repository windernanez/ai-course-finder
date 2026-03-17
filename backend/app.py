from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from buscador_ia import BuscadorCursosIA
from chatbot_gemini import ChatbotGemini
import os
from dotenv import load_dotenv
from datetime import datetime

# 1. Configuración de Rutas Absolutas (Corrige el 404 en Railway)
load_dotenv()
base_dir = os.path.abspath(os.path.dirname(__file__))
# Subimos un nivel desde 'backend' para encontrar 'frontend'
frontend_dir = os.path.abspath(os.path.join(base_dir, '..', 'frontend'))

app = Flask(__name__, 
            static_folder=frontend_dir, 
            static_url_path='')

CORS(app, resources={r"/api/*": {"origins": "*"}})

# Inicializar componentes
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY', '')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')

buscador = BuscadorCursosIA(YOUTUBE_API_KEY)
chatbot = ChatbotGemini(GEMINI_API_KEY)

# --- RUTAS DE NAVEGACIÓN ---

@app.route('/')
def servir_index():
    """Sirve el index.html desde la carpeta frontend"""
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def servir_estaticos(path):
    """Sirve CSS, JS y otros archivos estáticos"""
    return send_from_directory(app.static_folder, path)

# --- API ENDPOINTS ---

@app.route('/api/buscar', methods=['POST'])
def buscar_cursos():
    try:
        datos = request.get_json()
        if not datos:
            return jsonify({'error': 'No data provided'}), 400
        
        lenguaje = datos.get('lenguaje', '').strip().lower()
        nivel = datos.get('nivel', 'principiante').strip().lower()

        # Sincronizado con los métodos de tu buscador_ia.py
        videos = buscador.buscar_videos(lenguaje, nivel)
        canales = buscador.recomendar_canales(lenguaje)
        
        # Recomendación de IA
        recomendacion_chat = chatbot.obtener_recomendacion_rapida(lenguaje, nivel)

        # Retornamos un objeto estructurado para el frontend
        return jsonify({
            'exito': True,
            'videos': videos,
            'canales_recomendados': canales,
            'recomendacion_chat': recomendacion_chat
        })
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'exito': False, 'error': str(e)}), 500

@app.route('/api/lenguajes', methods=['GET'])
def obtener_lenguajes():
    """Retorna LISTA PURA [] para que .forEach() funcione en script.js"""
    lenguajes_lista = [
        {'id': 'python', 'nombre': 'Python', 'icono': '🐍'},
        {'id': 'javascript', 'nombre': 'JavaScript', 'icono': '📜'},
        {'id': 'java', 'nombre': 'Java', 'icono': '☕'},
        {'id': 'csharp', 'nombre': 'C#', 'icono': '🎯'},
        {'id': 'cpp', 'nombre': 'C++', 'icono': '⚡'},
        {'id': 'php', 'nombre': 'PHP', 'icono': '🐘'},
        {'id': 'ruby', 'nombre': 'Ruby', 'icono': '💎'},
        {'id': 'swift', 'nombre': 'Swift', 'icono': '📱'},
        {'id': 'kotlin', 'nombre': 'Kotlin', 'icono': '📲'},
        {'id': 'go', 'nombre': 'Go', 'icono': '🔵'},
        {'id': 'rust', 'nombre': 'Rust', 'icono': '⚙️'},
        {'id': 'typescript', 'nombre': 'TypeScript', 'icono': '📘'}
    ]
    return jsonify(lenguajes_lista)

@app.route('/api/estadisticas', methods=['GET'])
def obtener_estadisticas():
    return jsonify({
        'cursos_totales': 165,
        'busquedas_exitosas': 1284
    })

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        datos = request.get_json()
        mensaje = datos.get('mensaje', '')
        respuesta = chatbot.generar_respuesta(mensaje)
        return jsonify({'respuesta': respuesta})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
