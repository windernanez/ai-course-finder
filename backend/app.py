from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from buscador_ia import BuscadorCursosIA
from chatbot_gemini import ChatbotGemini
import os
from dotenv import load_dotenv
from datetime import datetime
import sys
from models import db, BusquedaHistorial, User, UserProgress
from sqlalchemy import func
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_mail import Mail, Message
from google_auth_oauthlib.flow import Flow
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
import requests
import json
import base64
from io import BytesIO
from reportlab.lib.pagesizes import landscape, letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib import colors

# Añadir el directorio frontend al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Cargar variables de entorno
load_dotenv()

basedir = os.path.abspath(os.path.dirname(__file__))
frontend_dir = os.path.abspath(os.path.join(basedir, '..', 'frontend'))

app = Flask(__name__, 
            static_folder=frontend_dir,
            static_url_path='')
CORS(app)

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'supersecretkey-replacethis')

# Configuración de Flask-Mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_USERNAME')

mail = Mail(app)

# Configuración de Google OAuth2
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'  # Permitir HTTP para desarrollo local
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
REDIRECT_URI = os.getenv('REDIRECT_URI', 'http://localhost:5000/callback')

db.init_app(app)

with app.app_context():
    db.create_all()

# Inicializar buscador con API key
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY', '')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')

if not YOUTUBE_API_KEY:
    print("⚠️  ADVERTENCIA: No se encontró YOUTUBE_API_KEY en el archivo .env")
if not GEMINI_API_KEY:
    print("⚠️  ADVERTENCIA: No se encontró GEMINI_API_KEY en el archivo .env")

buscador = BuscadorCursosIA(YOUTUBE_API_KEY)
chatbot = ChatbotGemini(GEMINI_API_KEY)



# Ruta principal - sirve el frontend (y reinicia las búsquedas como solicitó el usuario)
@app.route('/')
def servir_frontend():
    try:
        # El usuario pidió reiniciar las búsquedas cada vez que se refresque la página
        BusquedaHistorial.query.delete()
        db.session.commit()
    except Exception as e:
        print(f"Error al limpiar historial: {e}")
        db.session.rollback()
    
    # Reiniciar también el chatbot
    try:
        chatbot.reiniciar_sesiones()
    except Exception as e:
        print(f"Error al reiniciar chatbot: {e}")
    
    return send_from_directory(app.static_folder, 'index.html')

# Ruta para archivos estáticos
@app.route('/<path:path>')
def servir_archivos(path):
    return send_from_directory(app.static_folder, path)

# --- AUTH ROUTES ---
@app.route('/login')
def login():
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        return "Error: Google OAuth credentials not configured in .env", 500
        
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [REDIRECT_URI]
            }
        },
        scopes=['https://www.googleapis.com/auth/userinfo.profile', 'https://www.googleapis.com/auth/userinfo.email', 'openid'],
        redirect_uri=REDIRECT_URI
    )
    authorization_url, state = flow.authorization_url()
    from flask import session
    session['state'] = state
    session['code_verifier'] = flow.code_verifier # Guardar verificador para PKCE
    return jsonify({'auth_url': authorization_url})

@app.route('/callback')
def callback():
    from flask import session, redirect, url_for
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [REDIRECT_URI]
            }
        },
        scopes=['https://www.googleapis.com/auth/userinfo.profile', 'https://www.googleapis.com/auth/userinfo.email', 'openid'],
        redirect_uri=REDIRECT_URI
    )
    
    # Restaurar verificador PKCE desde la sesión
    code_verifier = session.get('code_verifier')
    
    flow.fetch_token(authorization_response=request.url, code_verifier=code_verifier)

    credentials = flow.credentials
    request_session = google_requests.Request()
    id_info = id_token.verify_oauth2_token(
        credentials.id_token, request_session, GOOGLE_CLIENT_ID
    )

    google_id = id_info.get('sub')
    email = id_info.get('email')
    nombre = id_info.get('name')
    imagen = id_info.get('picture')

    user = User.query.filter_by(google_id=google_id).first()
    if not user:
        user = User(google_id=google_id, email=email, nombre=nombre, imagen=imagen)
        db.session.add(user)
        db.session.commit()
    else:
        # Actualizar info si cambió
        user.nombre = nombre
        user.imagen = imagen
        db.session.commit()

    session['user_id'] = user.id
    session['user_name'] = user.nombre
    session['user_email'] = user.email

    return redirect('/')

@app.route('/logout')
def logout():
    from flask import session, redirect
    session.clear()
    return redirect('/')

@app.route('/api/user/me')
def get_me():
    from flask import session
    if 'user_id' not in session:
        return jsonify({'logged_in': False}), 200
    
    user = User.query.get(session['user_id'])
    if not user:
        return jsonify({'logged_in': False}), 200
        
    return jsonify({
        'logged_in': True,
        'user': user.to_dict()
    })

# --- PROGRESS ROUTES ---
@app.route('/api/progreso', methods=['GET'])
def obtener_progreso():
    from flask import session
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'No autenticado'}), 401
    
    lenguaje = request.args.get('lenguaje')
    nivel = request.args.get('nivel')
    
    if not lenguaje or not nivel:
        return jsonify({'error': 'Faltan parámetros'}), 400
        
    progreso = UserProgress.query.filter_by(user_id=user_id, lenguaje=lenguaje, nivel=nivel).first()
    if not progreso:
        return jsonify({'mensaje': 'Sin progreso previo', 'progreso': 0, 'videos_vistos': []}), 200
        
    return jsonify(progreso.to_dict())

@app.route('/api/completar-video', methods=['POST'])
def completar_video():
    from flask import session
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'No autenticado'}), 401
        
    datos = request.get_json()
    video_id = datos.get('video_id')
    lenguaje = datos.get('lenguaje')
    nivel = datos.get('nivel')
    total_videos = datos.get('total_videos', 10)
    visto = datos.get('visto', True) # Nuevo campo para saber si marcar o desmarcar
    
    if not all([video_id, lenguaje, nivel]):
        return jsonify({'error': 'Faltan datos'}), 400
        
    progreso = UserProgress.query.filter_by(user_id=user_id, lenguaje=lenguaje, nivel=nivel).first()
    
    if not progreso:
        vistos = [video_id] if visto else []
        progreso = UserProgress(
            user_id=user_id, 
            lenguaje=lenguaje, 
            nivel=nivel, 
            total_videos=total_videos,
            videos_vistos=video_id if visto else ""
        )
        db.session.add(progreso)
    else:
        vistos = [v for v in progreso.videos_vistos.split(',') if v] if progreso.videos_vistos else []
        if visto:
            if video_id not in vistos:
                vistos.append(video_id)
        else:
            if video_id in vistos:
                vistos.remove(video_id)
        
        progreso.videos_vistos = ','.join(vistos)
        progreso.total_videos = total_videos 
        
    db.session.commit()
    res_dict = progreso.to_dict()
    print(f"DEBUG PROGRESS: User {user_id}, {len(vistos)}/{total_videos} videos, Progreso: {res_dict['progreso']}%", flush=True)
    return jsonify(res_dict)

# --- QUIZ & CERTIFICATE ROUTES ---

@app.route('/api/generar-quiz', methods=['POST'])
def generar_quiz_endpoint():
    datos = request.get_json()
    lenguaje = datos.get('lenguaje')
    nivel = datos.get('nivel')
    
    if not lenguaje or not nivel:
        return jsonify({'error': 'Faltan parámetros'}), 400
        
    try:
        quiz_json = chatbot.generar_quiz(lenguaje, nivel)
        if not quiz_json:
            raise Exception("No AI quiz available")
        quiz_data = json.loads(quiz_json)
    except Exception as e:
        print(f"Fallback to static quiz: {e}")
        from quizzes import obtener_quiz_estatico
        import copy
        quiz_data = copy.deepcopy(obtener_quiz_estatico(lenguaje, nivel))
        
    # El bloque try anterior ya pobló quiz_data, ya sea con IA o con el fallback estático
    try:
        # Guardar las respuestas correctas en la sesión para validar luego
        from flask import session
        session[f'quiz_answers_{lenguaje}_{nivel}'] = [p['respuesta_correcta'] for p in quiz_data['preguntas']]
        
        # Ocultar las respuestas correctas al enviarlas al cliente para evitar trampas
        for p in quiz_data['preguntas']:
            if 'respuesta_correcta' in p:
                del p['respuesta_correcta']
            
        return jsonify(quiz_data)
    except Exception as e:
        print(f"Error procesando quiz data: {e}")
        return jsonify({'error': 'Error de formato en el quiz'}), 500

@app.route('/api/validar-quiz', methods=['POST'])
def validar_quiz():
    from flask import session
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'No autenticado'}), 401
        
    datos = request.get_json()
    lenguaje = datos.get('lenguaje')
    nivel = datos.get('nivel')
    respuestas_usuario = datos.get('respuestas') # Lista de índices
    
    if not all([lenguaje, nivel, respuestas_usuario]):
        return jsonify({'error': 'Faltan datos'}), 400
        
    respuestas_correctas = session.get(f'quiz_answers_{lenguaje}_{nivel}')
    if not respuestas_correctas:
        return jsonify({'error': 'No hay un quiz activo para validar'}), 400
        
    aciertos = 0
    for u, c in zip(respuestas_usuario, respuestas_correctas):
        if u == c:
            aciertos += 1
            
    puntuacion = int((aciertos / len(respuestas_correctas)) * 100)
    aprobado = puntuacion >= 80 # Se aprueba con 80%
    
    # Actualizar progreso
    progreso = UserProgress.query.filter_by(user_id=user_id, lenguaje=lenguaje, nivel=nivel).first()
    if progreso:
        progreso.examen_aprobado = aprobado
        progreso.puntuacion_examen = puntuacion
        db.session.commit()
        
    return jsonify({
        'puntuacion': puntuacion,
        'aprobado': aprobado,
        'mensaje': '¡Felicidades! Has aprobado.' if aprobado else 'Lo siento, no has alcanzado la puntuacion requerida (80%).'
    })

def generar_pdf_certificado(nombre_usuario, lenguaje, nivel):
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=landscape(letter))
    width, height = landscape(letter)
    
    # Fondo decorativo simple
    p.setStrokeColor(colors.gold)
    p.rect(0.5*inch, 0.5*inch, width-1*inch, height-1*inch, stroke=1, fill=0)
    
    # Contenido
    p.setFont("Helvetica-Bold", 40)
    p.drawCentredString(width/2, height - 2*inch, "CERTIFICADO DE LOGRO")
    
    p.setFont("Helvetica", 20)
    p.drawCentredString(width/2, height - 3*inch, "Este certificado se otorga con orgullo a:")
    
    p.setFont("Helvetica-Bold", 35)
    p.drawCentredString(width/2, height - 4*inch, nombre_usuario.upper())
    
    p.setFont("Helvetica", 20)
    p.drawCentredString(width/2, height - 5*inch, f"Por haber completado exitosamente el curso de:")
    
    p.setFont("Helvetica-Bold", 28)
    p.drawCentredString(width/2, height - 5.8*inch, f"{lenguaje.capitalize()} - Nivel {nivel.capitalize()}")
    
    p.setFont("Helvetica", 14)
    fecha = datetime.now().strftime("%d de %B de %Y")
    p.drawCentredString(width/2, height - 7*inch, f"Otorgado el {fecha}")
    
    p.setFont("Helvetica-Oblique", 12)
    p.drawCentredString(width/2, height - 7.5*inch, "AI Course Finder - Generado por Inteligencia Artificial")
    
    p.showPage()
    p.save()
    
    buffer.seek(0)
    return buffer

@app.route('/api/enviar-certificado', methods=['POST'])
def enviar_certificado():
    from flask import session
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'No autenticado'}), 401
        
    user = User.query.get(user_id)
    datos = request.get_json()
    lenguaje = datos.get('lenguaje')
    nivel = datos.get('nivel')
    
    progreso = UserProgress.query.filter_by(user_id=user_id, lenguaje=lenguaje, nivel=nivel).first()
    if not progreso or not progreso.examen_aprobado:
        return jsonify({'error': 'Debes aprobar el examen primero'}), 400
        
    try:
        # Generar PDF
        pdf_buffer = generar_pdf_certificado(user.nombre, lenguaje, nivel)
        
        # Enviar correo
        msg = Message(
            f"Tu Certificado de {lenguaje.capitalize()} - AI Course Finder",
            recipients=[user.email]
        )
        msg.body = f"Hola {user.nombre},\n\n¡Felicidades por completar el curso de {lenguaje} nivel {nivel}! Adjunto encontrarás tu certificado.\n\nSigue aprendiendo con AI Course Finder."
        
        msg.attach(
            f"Certificado_{lenguaje}_{nivel}.pdf",
            "application/pdf",
            pdf_buffer.read()
        )
        
        mail.send(msg)
        
        progreso.certificado_generado = True
        db.session.commit()
        
        return jsonify({'exito': True, 'mensaje': 'Certificado enviado a tu correo'})
    except Exception as e:
        print(f"Error enviando correo: {e}")
        return jsonify({'error': f'Error al enviar el correo: {str(e)}'}), 500

# API Routes
@app.route('/api/buscar', methods=['POST'])
@limiter.limit("5 per minute")
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
        session_id = datos.get('session_id', 'anon')
        
        if not lenguaje:
            return jsonify({'error': 'El lenguaje es requerido'}), 400
        
        # Validar nivel
        niveles_validos = ['principiante', 'intermedio', 'avanzado']
        if nivel not in niveles_validos:
            nivel = 'principiante'
        
        # Actualizar contexto del chatbot
        chatbot.actualizar_contexto(session_id, lenguaje=lenguaje, nivel=nivel)
        
        # Buscar videos usando el buscador con IA
        resultados = buscador.buscar_videos(lenguaje, nivel)
        
        # Obtener recomendaciones de canales
        canales = buscador.recomendar_canales(lenguaje)
        
        # Guardar en historial en DB
        nueva_busqueda = BusquedaHistorial(lenguaje=lenguaje, nivel=nivel, total_videos=len(resultados))
        db.session.add(nueva_busqueda)
        db.session.commit()
        
        busqueda_dict = nueva_busqueda.to_dict()
        
        # Actualizar última búsqueda en chatbot
        chatbot.actualizar_ultima_busqueda(session_id, busqueda_dict)
        
        # Generar recomendación del chatbot
        recomendacion_chat = chatbot.obtener_recomendacion_rapida(lenguaje, nivel)
        
        return jsonify({
            'exito': True,
            'lenguaje': lenguaje,
            'nivel': nivel,
            'videos': resultados,
            'canales_recomendados': canales,
            'total_videos': len(resultados),
            'recomendacion_chat': recomendacion_chat,
            'mensaje': f'Se encontraron {len(resultados)} videos para {lenguaje} nivel {nivel}'
        })
        
    except Exception as e:
        print(f"Error en búsqueda: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat', methods=['POST'])
@limiter.limit("15 per minute")
def chat():
    """
    Endpoint para el chatbot
    Espera JSON: {"mensaje": "texto del usuario", "lenguaje": "python" (opcional)}
    """
    try:
        datos = request.get_json()
        
        if not datos or 'mensaje' not in datos:
            return jsonify({'error': 'Mensaje no proporcionado'}), 400
        
        mensaje = datos['mensaje']
        lenguaje = datos.get('lenguaje', None)
        session_id = datos.get('session_id', 'anon')
        
        # Actualizar contexto si se proporciona lenguaje
        if lenguaje:
            chatbot.actualizar_contexto(session_id, lenguaje=lenguaje)
        
        # Generar respuesta
        respuesta = chatbot.generar_respuesta(session_id, mensaje)
        
        return jsonify({
            'exito': True,
            'respuesta': respuesta,
            'historial': chatbot.obtener_historial_formateado(session_id)[-10:]  # Últimos 10 mensajes
        })
        
    except Exception as e:
        print(f"Error en chat: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat/historial', methods=['GET'])
def obtener_historial_chat():
    """Devuelve el historial del chat"""
    session_id = request.args.get('session_id', 'anon')
    return jsonify({
        'historial': chatbot.obtener_historial_formateado(session_id)
    })

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
        {'id': 'typescript', 'nombre': 'TypeScript', 'icono': '📘'},
        {'id': 'dart', 'nombre': 'Dart', 'icono': '🎯'},
        {'id': 'r', 'nombre': 'R', 'icono': '📊'},
        {'id': 'scala', 'nombre': 'Scala', 'icono': '🔴'},
        {'id': 'perl', 'nombre': 'Perl', 'icono': '🐪'},
        {'id': 'haskell', 'nombre': 'Haskell', 'icono': 'λ'},
        {'id': 'clojure', 'nombre': 'Clojure', 'icono': '☯️'},
        {'id': 'elixir', 'nombre': 'Elixir', 'icono': '💧'},
        {'id': 'erlang', 'nombre': 'Erlang', 'icono': '📞'},
        {'id': 'fsharp', 'nombre': 'F#', 'icono': '🎼'},
        {'id': 'lua', 'nombre': 'Lua', 'icono': '🌙'},
        {'id': 'matlab', 'nombre': 'MATLAB', 'icono': '📐'},
        {'id': 'objectivec', 'nombre': 'Objective-C', 'icono': '🍎'},
        {'id': 'sql', 'nombre': 'SQL', 'icono': '🗄️'},
        {'id': 'html', 'nombre': 'HTML5', 'icono': '🌐'},
        {'id': 'css', 'nombre': 'CSS3', 'icono': '🎨'},
        {'id': 'shell', 'nombre': 'Bash/Shell', 'icono': '🐚'},
        {'id': 'powershell', 'nombre': 'PowerShell', 'icono': '💻'},
        {'id': 'vba', 'nombre': 'VBA', 'icono': '📊'},
        {'id': 'fortran', 'nombre': 'Fortran', 'icono': '🔢'},
        {'id': 'cobol', 'nombre': 'COBOL', 'icono': '📼'},
        {'id': 'assembly', 'nombre': 'Assembly', 'icono': '🔌'},
        {'id': 'solidity', 'nombre': 'Solidity', 'icono': '⛓️'},
        {'id': 'zig', 'nombre': 'Zig', 'icono': '⚡'},
        {'id': 'nim', 'nombre': 'Nim', 'icono': '👑'},
        {'id': 'julia', 'nombre': 'Julia', 'icono': '🍩'},
        {'id': 'v', 'nombre': 'V Language', 'icono': '✌️'},
        {'id': 'ocaml', 'nombre': 'OCaml', 'icono': '🐫'},
        {'id': 'pascal', 'nombre': 'Pascal/Delphi', 'icono': '🖋️'},
        {'id': 'ada', 'nombre': 'Ada', 'icono': '🛡️'},
        {'id': 'lisp', 'nombre': 'Common Lisp', 'icono': '📡'},
        {'id': 'scheme', 'nombre': 'Scheme', 'icono': '📜'},
        {'id': 'smalltalk', 'nombre': 'Smalltalk', 'icono': '💬'},
        {'id': 'prolog', 'nombre': 'Prolog', 'icono': '🔎'},
        {'id': 'vhdl', 'nombre': 'VHDL', 'icono': '📟'},
        {'id': 'verilog', 'nombre': 'Verilog', 'icono': '🔌'},
        {'id': 'tcl', 'nombre': 'Tcl/Tk', 'icono': '🏸'},
        {'id': 'crystal', 'nombre': 'Crystal', 'icono': '💎'},
        {'id': 'd', 'nombre': 'D Language', 'icono': '⚓'},
        {'id': 'groovy', 'nombre': 'Groovy', 'icono': '🎸'},
        {'id': 'apl', 'nombre': 'APL', 'icono': '📐'},
        {'id': 'forth', 'nombre': 'Forth', 'icono': '🔝'},
        {'id': 'mojo', 'nombre': 'Mojo', 'icono': '🔥'},
        {'id': 'gleam', 'nombre': 'Gleam', 'icono': '✨'},
        {'id': 'ballerina', 'nombre': 'Ballerina', 'icono': '🩰'},
        {'id': 'elm', 'nombre': 'Elm', 'icono': '🌳'},
        {'id': 'haxe', 'nombre': 'Haxe', 'icono': '🍊'},
        {'id': 'idris', 'nombre': 'Idris', 'icono': '🐉'},
        {'id': 'pure-script', 'nombre': 'PureScript', 'icono': '📜'},
        {'id': 'racket', 'nombre': 'Racket', 'icono': '🏸'},
        {'id': 'standard-ml', 'nombre': 'Standard ML', 'icono': '🐫'},
        {'id': 'scratch', 'nombre': 'Scratch', 'icono': '🐱'},
        {'id': 'labview', 'nombre': 'LabVIEW', 'icono': '🏗️'},
        {'id': 'abap', 'nombre': 'ABAP', 'icono': '📊'},
        {'id': 'apex', 'nombre': 'Apex', 'icono': '☁️'},
        {'id': 'sas', 'nombre': 'SAS', 'icono': '📉'},
        {'id': 'stata', 'nombre': 'Stata', 'icono': '📈'},
        {'id': 'pl-sql', 'nombre': 'PL/SQL', 'icono': '💾'},
        {'id': 't-sql', 'nombre': 'T-SQL', 'icono': '🖥️'},
        {'id': 'glsl', 'nombre': 'GLSL', 'icono': '🎮'},
        {'id': 'hlsl', 'nombre': 'HLSL', 'icono': '🖌️'},
        {'id': 'cool', 'nombre': 'Cool', 'icono': '❄️'},
        {'id': 'q-sharp', 'nombre': 'Q# (Quantum)', 'icono': '⚛️'}
    ]
    return jsonify(lenguajes)

@app.route('/api/presentacion/<lenguaje>', methods=['GET'])
@limiter.limit("10 per minute")
def obtener_presentacion_lenguaje(lenguaje):
    """Obtiene una presentación dinámica del lenguaje usando Gemini"""
    try:
        info_json = chatbot.obtener_informacion_lenguaje(lenguaje)
        if info_json:
            import json
            data = json.loads(info_json)
            return jsonify({
                'exito': True,
                'data': data
            })
        else:
            return jsonify({'exito': False, 'error': 'No se pudo generar la información'}), 500
    except Exception as e:
        print(f"Error en endpoint presentacion: {e}")
        return jsonify({'exito': False, 'error': str(e)}), 500

@app.route('/api/estadisticas', methods=['GET'])
def obtener_estadisticas():
    """Estadísticas de uso almacenadas en DB"""
    total = BusquedaHistorial.query.count()
    if total == 0:
        return jsonify({
            'total_busquedas': 0,
            'lenguajes_populares': []
        })
    
    conteo = db.session.query(
        BusquedaHistorial.lenguaje,
        func.count(BusquedaHistorial.id).label('total')
    ).group_by(BusquedaHistorial.lenguaje).order_by(db.text('total DESC')).limit(5).all()
    
    return jsonify({
        'total_busquedas': total,
        'lenguajes_populares': [{'lenguaje': c[0], 'busquedas': c[1]} for c in conteo]
    })

@app.route('/api/health', methods=['GET'])
def health_check():
    """Verificar que la API funciona"""
    return jsonify({
        'status': 'OK',
        'mensaje': 'API de búsqueda de cursos funcionando correctamente',
        'chatbot': 'activo' if GEMINI_API_KEY else 'desactivado (sin API key)'
    })

if __name__ == '__main__':
    print("="*50)
    print("🚀 AI COURSE FINDER CON CHATBOT GEMINI")
    print("="*50)
    print("📁 Servidor unificado iniciado")
    print("🌐 Frontend: http://localhost:5000")
    print("🔗 API: http://localhost:5000/api")
    print("🤖 Chatbot:", "✅ ACTIVADO" if GEMINI_API_KEY else "❌ DESACTIVADO (sin API key)")
    print("="*50)
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)