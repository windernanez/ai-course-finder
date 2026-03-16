from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from buscador_ia import BuscadorCursosIA
from chatbot_gemini import ChatbotGemini
import os
from dotenv import load_dotenv
from datetime import datetime
import sys

# 1. Ajuste de Path: Esto asegura que encuentre los módulos en Railway
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

# 2. Ajuste de carpetas estáticas: 
# En Railway, la estructura será plana o relativa al directorio de ejecución.
app = Flask(__name__, 
            static_folder='../frontend', 
            static_url_path='')
CORS(app)

YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY', '')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')

# Inicialización segura
buscador = BuscadorCursosIA(YOUTUBE_API_KEY)
chatbot = ChatbotGemini(GEMINI_API_KEY)

historial_busquedas = []

@app.route('/')
def servir_frontend():
    # Intentar servir index.html, si falla dar un mensaje de API activa
    try:
        return send_from_directory(app.static_folder, 'index.html')
    except:
        return jsonify({"mensaje": "API de AI Course Finder Activa", "frontend": "No encontrado"}), 200

# ... (Tus rutas /api/buscar, /api/chat, etc., se mantienen IGUAL) ...

if __name__ == '__main__':
    # 3. Importante: debug debe ser False en producción (Railway)
    # Railway inyecta automáticamente la variable PORT
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
