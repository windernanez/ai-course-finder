
from chatbot_gemini import ChatbotGemini
from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv('GEMINI_API_KEY')
print(f"API Key: {api_key[:10]}...")

chatbot = ChatbotGemini(api_key)

# Probar un mensaje
respuesta = chatbot.generar_respuesta("session_test", "Hola, ¿qué puedes hacer?")
print(f"Respuesta: {respuesta}")

# Salir de Python
exit()