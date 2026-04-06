"""
Chatbot con Gemini AI para AI Course Finder
"""
import google.generativeai as genai
import os
from datetime import datetime
import re

class ChatbotGemini:
    def __init__(self, api_key):
        """
        Inicializa el chatbot con la API key de Gemini
        """
        print("🔄 Inicializando Chatbot con Gemini (Multisesión)...")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        self.sesiones = {}
        
        # Sistema de prompts para dar contexto a Gemini
        self.system_prompt = """
        Eres un asistente virtual experto en programación, integrado en un buscador de cursos llamado "AI Course Finder".
        
        INFORMACIÓN IMPORTANTE SOBRE LA APLICACIÓN:
        - Los usuarios pueden buscar cursos por lenguaje mediante la interfaz principal
        - Los niveles disponibles son: principiante, intermedio, avanzado
        
        TUS FUNCIONES:
        1. Ayudar a elegir el mejor lenguaje según sus intereses
        2. Recomendar qué nivel elegir según su experiencia
        3. Dar consejos de aprendizaje
        4. Ser amigable y motivador
        
        DIRECTRICES:
        - Responde en español siempre
        - Sé conciso pero útil (máximo 3-4 frases)
        - Si no sabes algo, sugiere buscar en la aplicación
        - Usa emojis ocasionalmente
        """
        
        print("✅ Chatbot inicializado")

    def reiniciar_sesiones(self):
        """Limpia todas las sesiones activas"""
        self.sesiones = {}
        print("🗑️  Sesiones de chatbot reiniciadas")
        
    def _obtener_sesion(self, session_id):
        if session_id not in self.sesiones:
            self.sesiones[session_id] = {
                'historial': [],
                'contexto': {
                    'lenguaje': None,
                    'nivel': None,
                    'ultima_busqueda': None
                }
            }
        return self.sesiones[session_id]

    def actualizar_contexto(self, session_id, lenguaje=None, nivel=None):
        sesion = self._obtener_sesion(session_id)
        if lenguaje:
            sesion['contexto']['lenguaje'] = lenguaje
        if nivel:
            sesion['contexto']['nivel'] = nivel
            
    def actualizar_ultima_busqueda(self, session_id, busqueda):
        sesion = self._obtener_sesion(session_id)
        sesion['contexto']['ultima_busqueda'] = busqueda

    def generar_respuesta(self, session_id, mensaje_usuario):
        sesion = self._obtener_sesion(session_id)
        historial = sesion['historial']
        contexto_actual = sesion['contexto']
        
        try:
            contexto = f"""
            CONTEXTO ACTUAL:
            - Lenguaje: {contexto_actual['lenguaje'] or 'Ninguno'}
            - Nivel: {contexto_actual['nivel'] or 'Ninguno'}
            - Última búsqueda: {contexto_actual['ultima_busqueda'] or 'Ninguna'}
            """
            
            for msg in historial[-3:]:
                contexto += f"\nUsuario: {msg['usuario']}\nAsistente: {msg['respuesta']}"
            
            prompt = f"{self.system_prompt}\n{contexto}\nMensaje del usuario: '{mensaje_usuario}'\nRespuesta:"
            
            response = self.model.generate_content(prompt)
            respuesta = response.text
            
            historial.append({
                'usuario': mensaje_usuario,
                'respuesta': respuesta,
                'timestamp': datetime.now().isoformat()
            })
            
            if len(historial) > 50:
                sesion['historial'] = historial[-50:]
            
            return respuesta
            
        except Exception as e:
            print(f"Error en Gemini para sesión {session_id}: {e}")
            return "Lo siento, tuve un problema. ¿Puedes repetirlo? 🤔"

    def obtener_informacion_lenguaje(self, lenguaje):
        """Genera información resumida y estructurada sobre un lenguaje de programación"""
        if not self.model:
            return None
            
        prompt = f"""
        Actúa como un experto en tecnología. Proporciona información estructurada sobre el lenguaje de programación: {lenguaje}.
        Responde ÚNICAMENTE en formato JSON con la siguiente estructura (sin bloques de código markdown, solo el texto JSON):
        {{
            "nombre": "Nombre del Lenguaje",
            "creador": "Nombre del creador o entidad",
            "anio_creacion": "Año",
            "descripcion": "Descripción concisa (máximo 2 frases)",
            "curiosidad": "Un dato curioso muy breve",
            "caracteristicas": ["característica 1", "característica 2", "característica 3"],
            "casos_uso": ["ejemplo 1", "ejemplo 2"],
            "ejemplos_relevantes": {{
                "sistemas": [
                    {{"nombre": "Nombre 1", "icono": "fas fa-desktop"}},
                    {{"nombre": "Nombre 2", "icono": "fab fa-linux"}}
                ],
                "apps": [
                    {{"nombre": "Nombre 1", "icono": "fab fa-instagram"}},
                    {{"nombre": "Nombre 2", "icono": "fab fa-whatsapp"}}
                ],
                "juegos": [
                    {{"nombre": "Nombre 1", "icono": "fas fa-gamepad"}},
                    {{"nombre": "Nombre 2", "icono": "fas fa-ghost"}}
                ]
            }},
            "proyectos_famosos": [
                {{
                    "nombre": "Nombre del Proyecto", 
                    "tipo": "App/Juego/Sistema", 
                    "icono": "Clase FontAwesome (ej: fab fa-facebook, fas fa-database)",
                    "descripcion": "Breve descripción", 
                    "info_detallada": "Explicación de por qué es importante y el impacto que tuvo.", 
                    "anio": "Año de creación"
                }}
            ],
            "popularidad": "Alta/Media/Baja con breve explicación",
            "estetica_color": "Un color hexadecimal que represente al lenguaje (ej: #3776ab para Python)"
        }}
        IMPORTANTE: En 'ejemplos_relevantes' incluye exactamente 2 elementos por categoría (2 de sistemas, 2 de apps, 2 de juegos). Luego, en 'proyectos_famosos', DEBES incluir la información detallada obligatoriamente para ESOS MISMOS 6 elementos listados en ejemplos_relevantes. Los nombres deben coincidir de forma exacta.
        Evita cualquier texto fuera del JSON.
        """
        
        response = self.model.generate_content(prompt)
        # Limpiar posible markdown si Gemini lo incluye a pesar de las instrucciones
        text = response.text.replace('```json', '').replace('```', '').strip()
        return text

    def obtener_recomendacion_rapida(self, lenguaje, nivel):
        prompt = f"El usuario acaba de buscar cursos de {lenguaje} nivel {nivel}. Genera un mensaje corto (1 frase) felicitándolo interactuando con estos cursos."
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except:
            return f"¡Excelente elección de {lenguaje} nivel {nivel}! 🚀"

    def obtener_historial_formateado(self, session_id):
        sesion = self._obtener_sesion(session_id)
        return [
            {
                'usuario': msg['usuario'],
                'bot': msg['respuesta'],
                'tiempo': msg['timestamp']
            }
            for msg in sesion['historial']
        ]

    def generar_quiz(self, lenguaje, nivel):
        """Genera un examen de 5 preguntas usando Gemini"""
        prompt = f"""
        Actúa como un profesor de programación. Genera un examen de 5 preguntas de opción múltiple para el lenguaje {lenguaje} nivel {nivel}. 
        El nivel {nivel} debe ser respetado estrictamente en la dificultad de las preguntas.
        
        Responde ÚNICAMENTE en formato JSON con la siguiente estructura (sin markdown):
        {{
            "titulo": "Examen de {lenguaje.capitalize()} - Nivel {nivel.capitalize()}",
            "preguntas": [
                {{
                    "pregunta": "¿Texto de la pregunta?",
                    "opciones": ["Opción A", "Opción B", "Opción C", "Opción D"],
                    "respuesta_correcta": 0
                }}
            ]
        }}
        Índice respuesta_correcta: 0 para la primera opción, 1 para la segunda, etc.
        """
        try:
            response = self.model.generate_content(prompt)
            text = response.text.replace('```json', '').replace('```', '').strip()
            return text
        except Exception as e:
            print(f"Error generando quiz: {e}")
            return None