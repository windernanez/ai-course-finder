from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from buscador_ia import BuscadorCursosIA
import os
from dotenv import load_dotenv
from datetime import datetime
import sys

# Añadir el directorio frontend al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Cargar variables de entorno
load_dotenv()

app = Flask(__name__, 
            static_folder='../frontend',  # Carpeta de archivos estáticos
            static_url_path='')  # URL base para archivos estáticos
CORS(app)  # Permitir peticiones del frontend

# Inicializar buscador con API key
API_KEY = os.getenv('YOUTUBE_API_KEY', '')
if not API_KEY:
    print("⚠️  ADVERTENCIA: No se encontró YOUTUBE_API_KEY en el archivo .env")
    print("Por favor, configura tu API key en el archivo .env")

buscador = BuscadorCursosIA(API_KEY)

# Historial de búsquedas (en producción usaríamos una BD)
historial_busquedas = []

# Ruta principal - sirve el frontend
@app.route('/')
def servir_frontend():
    return send_from_directory(app.static_folder, 'index.html')

# Ruta para archivos estáticos (CSS, JS)
@app.route('/<path:path>')
def servir_archivos(path):
    return send_from_directory(app.static_folder, path)

# API Routes
@app.route('/api/buscar', methods=['POST'])
def buscar_cursos():
    """
    Endpoint para buscar cursos
    Espera JSON: {"lenguaje": "python", "nivel": "principiante"}
    """
    try:
        datos = request.get_json()
        
        if not datos:
            return jsonify({'error': 'No se proporcionaron datos'}), 400
        
        lenguaje = datos.get('lenguaje', '').strip().lower()
        nivel = datos.get('nivel', 'principiante').strip().lower()
        
        if not lenguaje:
            return jsonify({'error': 'El lenguaje es requerido'}), 400
        
        # Validar nivel
        niveles_validos = ['principiante', 'intermedio', 'avanzado']
        if nivel not in niveles_validos:
            nivel = 'principiante'
        
        # Buscar videos
        videos = buscador.buscar_videos(lenguaje, nivel)
        
        # Obtener recomendaciones de canales
        canales = buscador.recomendar_canales(lenguaje)
        
        # Guardar en historial
        historial_busquedas.append({
            'lenguaje': lenguaje,
            'nivel': nivel,
            'timestamp': str(datetime.now())
        })
        
        # Limitar historial
        if len(historial_busquedas) > 100:
            historial_busquedas.pop(0)
        
        return jsonify({
            'exito': True,
            'lenguaje': lenguaje,
            'nivel': nivel,
            'total_videos': len(videos),
            'videos': videos,
            'canales_recomendados': canales,
            'mensaje': f'Se encontraron {len(videos)} videos para {lenguaje} nivel {nivel}'
        })
        
    except Exception as e:
        print(f"Error en búsqueda: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/lenguajes', methods=['GET'])
def obtener_lenguajes():
    """Devuelve la lista de lenguajes soportados"""
    lenguajes = [
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
    return jsonify(lenguajes)

@app.route('/api/historial', methods=['GET'])
def obtener_historial():
    """Devuelve el historial de búsquedas"""
    return jsonify(historial_busquedas[-10:])  # Últimas 10 búsquedas

@app.route('/api/estadisticas', methods=['GET'])
def obtener_estadisticas():
    """Estadísticas de uso"""
    if not historial_busquedas:
        return jsonify({
            'total_busquedas': 0,
            'lenguajes_populares': []
        })
    
    # Contar búsquedas por lenguaje
    conteo = {}
    for busqueda in historial_busquedas:
        lang = busqueda['lenguaje']
        conteo[lang] = conteo.get(lang, 0) + 1
    
    # Ordenar por popularidad
    populares = sorted(conteo.items(), key=lambda x: x[1], reverse=True)[:5]
    
    return jsonify({
        'total_busquedas': len(historial_busquedas),
        'lenguajes_populares': [{'lenguaje': l, 'busquedas': c} for l, c in populares]
    })

@app.route('/api/health', methods=['GET'])
def health_check():
    """Verificar que la API funciona"""
    return jsonify({
        'status': 'OK',
        'mensaje': 'API de búsqueda de cursos funcionando correctamente'
    })

if __name__ == '__main__':
    print("🚀 Servidor unificado iniciado en http://localhost:5000")
    print("📁 Sirviendo frontend desde:", app.static_folder)
    print("🔗 API disponible en http://localhost:5000/api")
    app.run(debug=True, port=5000, host='0.0.0.0')