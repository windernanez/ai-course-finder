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
        print("🔄 Inicializando Chatbot con Gemini...")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        self.historial = []
        self.contexto_actual = {
            'lenguaje': None,
            'nivel': None,
            'ultima_busqueda': None
        }
        
        # Sistema de prompts para dar contexto a Gemini
        self.system_prompt = """
        Eres un asistente virtual experto en programación, integrado en un buscador de cursos llamado "AI Course Finder".
        
        INFORMACIÓN IMPORTANTE SOBRE LA APLICACIÓN:
        - Los usuarios pueden buscar cursos por lenguaje (Python, JavaScript, Java, etc.)
        - Los niveles disponibles son: principiante, intermedio, avanzado
        - La aplicación usa IA para clasificar automáticamente el nivel de los videos
        - Puedes recomendar canales populares como: Pildorasinformaticas, The Net Ninja, etc.
        
        TUS FUNCIONES:
        1. Ayudar a elegir el mejor lenguaje según sus intereses
        2. Recomendar qué nivel elegir según su experiencia
        3. Dar consejos de aprendizaje
        4. Responder dudas sobre programación
        5. Ser amigable y motivador
        
        DIRECTRICES:
        - Responde en español siempre
        - Sé conciso pero útil (máximo 3-4 frases)
        - Si no sabes algo, sugiere buscar en la aplicación
        - Usa emojis ocasionalmente para ser más amigable 🚀
        - Pregunta por sus intereses para mejores recomendaciones
        
        EJEMPLOS DE INTERACCIÓN:
        Usuario: "Quiero aprender a programar"
        Tú: "¡Excelente decisión! 🚀 ¿Qué área te interesa más? Desarrollo web (JavaScript), ciencia de datos (Python), apps móviles (Kotlin/Swift) o algo más específico?"
        
        Usuario: "Soy principiante en Python"
        Tú: "¡Perfecto! Python es ideal para empezar. En la aplicación selecciona 'Python' y nivel 'Principiante'. Encontrarás cursos desde cero. ¿Tienes experiencia previa con algún otro lenguaje?"
        """
        
        print("✅ Chatbot de Gemini inicializado correctamente")
    
    def actualizar_contexto(self, lenguaje=None, nivel=None):
        """
        Actualiza el contexto con la información actual del usuario
        """
        if lenguaje:
            self.contexto_actual['lenguaje'] = lenguaje
        if nivel:
            self.contexto_actual['nivel'] = nivel
    
    def generar_respuesta(self, mensaje_usuario):
        """
        Genera una respuesta usando Gemini
        """
        try:
            # Construir el prompt con contexto
            contexto = f"""
            CONTEXTO ACTUAL DE LA APLICACIÓN:
            - Lenguaje seleccionado: {self.contexto_actual['lenguaje'] or 'Ninguno'}
            - Nivel seleccionado: {self.contexto_actual['nivel'] or 'Ninguno'}
            - Última búsqueda: {self.contexto_actual['ultima_busqueda'] or 'Ninguna'}
            
            HISTORIAL RECIENTE DE CONVERSACIÓN:
            """
            
            # Añadir últimos 3 mensajes del historial
            for msg in self.historial[-3:]:
                contexto += f"\nUsuario: {msg['usuario']}\nAsistente: {msg['respuesta']}"
            
            # Prompt completo
            prompt = f"""
            {self.system_prompt}
            
            {contexto}
            
            Mensaje actual del usuario: "{mensaje_usuario}"
            
            Responde de manera útil y amigable:
            """
            
            # Obtener respuesta de Gemini
            response = self.model.generate_content(prompt)
            respuesta = response.text
            
            # Guardar en historial
            self.historial.append({
                'usuario': mensaje_usuario,
                'respuesta': respuesta,
                'timestamp': datetime.now().isoformat(),
                'contexto': self.contexto_actual.copy()
            })
            
            # Limitar historial a 50 mensajes
            if len(self.historial) > 50:
                self.historial = self.historial[-50:]
            
            return respuesta
            
        except Exception as e:
            print(e)
            return "Lo siento, tuve un problema al procesar tu mensaje. ¿Puedes repetirlo? 🤔 {e}"
    
    def obtener_recomendacion_rapida(self, lenguaje, nivel):
        """
        Genera una recomendación rápida basada en la búsqueda actual
        """
        prompt = f"""
        El usuario acaba de buscar cursos de {lenguaje} nivel {nivel}.
        Genera un mensaje corto y motivador recomendándole cómo aprovechar estos cursos.
        Incluye un consejo específico para su nivel.
        Máximo 2 frases.
        """
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except:
            return f"¡Excelente elección! Los cursos de {lenguaje} nivel {nivel} son geniales para tu aprendizaje. 🚀"
    
    def obtener_historial_formateado(self):
        """
        Devuelve el historial formateado para el frontend
        """
        return [
            {
                'usuario': msg['usuario'],
                'bot': msg['respuesta'],
                'tiempo': msg['timestamp']
            }
            for msg in self.historial
        ]
