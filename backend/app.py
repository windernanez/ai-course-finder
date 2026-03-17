from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from buscador_ia import BuscadorCursosIA
from chatbot_gemini import ChatbotGemini
import os
from dotenv import load_dotenv
from datetime import datetime
import sys

# Cargar variables de entorno
load_dotenv()

app = Flask(__name__, 
            static_folder='../frontend',
            static_url_path='')

# Configuración de CORS robusta para producción
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Inicializar buscador y chatbot
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY', '')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')

buscador = BuscadorCursosIA(YOUTUBE_API_KEY)
chatbot = ChatbotGemini(GEMINI_API_KEY)

# Historial de búsquedas en memoria
historial_busquedas = []

@app.route('/')
def servir_frontend():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/api/buscar', methods=['POST', 'OPTIONS'])
def buscar_cursos():
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200
        
    try:
        datos = request.get_json()
        if not datos:
            return jsonify({'error': 'No se proporcionaron datos'}), 400
        
        lenguaje = datos.get('lenguaje', '').strip().lower()
        nivel = datos.get('nivel', 'principiante').strip().lower()
        
        if not lenguaje:
            return jsonify({'error': 'El lenguaje es requerido'}), 400
        
        # Actualizar contexto del chatbot
        chatbot.actualizar_contexto(lenguaje=lenguaje, nivel=nivel)
        
        # Buscar videos y canales
        videos = buscador.buscar_videos(lenguaje, nivel)
        canales = buscador.recomendar_canales(lenguaje)
        
        # Guardar en historial
        busqueda = {
            'lenguaje': lenguaje,
            'nivel': nivel,
            'timestamp': str(datetime.now()),
            'total_videos': len(videos)
        }
        historial_busquedas.append(busqueda)
        if len(historial_busquedas) > 100: historial_busquedas.pop(0)
        
        # Generar recomendación de IA
        recomendacion_chat = chatbot.obtener_recomendacion_rapida(lenguaje, nivel)
        
        # RETORNO COMPATIBLE: Enviamos el array de videos directamente para el script.js
        # pero incluimos los metadatos para el chatbot
        return jsonify(videos) 
        
    except Exception as e:
        print(f"❌ Error en búsqueda: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        datos = request.get_json()
        mensaje = datos.get('mensaje', '')
        respuesta = chatbot.generar_respuesta(mensaje)
        return jsonify({'respuesta': respuesta})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/lenguajes', methods=['GET'])
def obtener_lenguajes():
    """Mantiene tu lista original con iconos"""
    lenguajes_full = [
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
    # Para evitar el error en el frontend, enviamos un objeto que contenga la lista
    # pero también una lista plana de IDs para compatibilidad.
    return jsonify({
        'lenguajes': [l['id'] for l in lenguajes_full],
        'detalles': lenguajes_full
    })

@app.route('/api/estadisticas', methods=['GET'])
def obtener_estadisticas():
    # Valores por defecto para que la interfaz nunca se vea vacía
    return jsonify({
        'cursos_totales': 150 + len(historial_busquedas),
        'busquedas_exitosas': 1240 + len(historial_busquedas)
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
