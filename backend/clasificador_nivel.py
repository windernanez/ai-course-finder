import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import make_pipeline
import joblib
import os
import re

class ClasificadorNivelCursos:
    def __init__(self):
        self.modelo = None
        self.vectorizer = None
        self.palabras_clave = {
            'principiante': [
                'introducción', 'básico', 'principiante', 'desde cero', 'para empezar',
                'fundamentos', 'primeros pasos', 'inicial', 'fácil', 'simple',
                'aprender', 'guía', 'tutorial básico', 'conceptos básicos',
                'introduction', 'beginner', 'basics', 'easy', 'simple',
                'fundamentals', 'first steps', 'tutorial for beginners'
            ],
            'intermedio': [
                'intermedio', 'medio', 'continuación', 'avanzando', 'práctico',
                'ejercicios', 'proyectos', 'implementación', 'desarrollo',
                'intermediate', 'medium', 'practical', 'projects', 'implementation',
                'hands-on', 'real world', 'building'
            ],
            'avanzado': [
                'avanzado', 'experto', 'profesional', 'complejo', 'optimización',
                'patrones', 'arquitectura', 'escalabilidad', 'rendimiento',
                'advanced', 'expert', 'professional', 'complex', 'optimization',
                'patterns', 'architecture', 'scalability', 'performance',
                'masterclass', 'deep dive'
            ]
        }
        self.entrenar_modelo()
    
    def preprocesar_texto(self, texto):
        """Limpia y normaliza el texto"""
        if not isinstance(texto, str):
            texto = str(texto)
        texto = texto.lower()
        texto = re.sub(r'[^\w\s]', ' ', texto)
        texto = re.sub(r'\d+', ' ', texto)
        texto = re.sub(r'\s+', ' ', texto).strip()
        return texto
    
    def crear_caracteristicas(self, texto):
        """Crea características adicionales basadas en palabras clave"""
        texto_procesado = self.preprocesar_texto(texto)
        caracteristicas = []
        
        for nivel, palabras in self.palabras_clave.items():
            conteo = sum(1 for palabra in palabras if palabra in texto_procesado)
            caracteristicas.append(conteo)
        
        return texto_procesado, caracteristicas
    
    def entrenar_modelo(self):
        """Entrena el clasificador con datos de ejemplo"""
        print("🔄 Entrenando modelo de clasificación...")
        
        # Datos de entrenamiento
        textos_entrenamiento = []
        niveles_entrenamiento = []
        
        # Generar ejemplos para cada nivel
        for nivel, palabras in self.palabras_clave.items():
            for palabra in palabras[:5]:  # Usar primeras 5 palabras de cada categoría
                # Variaciones de títulos para cada nivel
                textos_entrenamiento.append(f"Curso de programación {palabra} tutorial completo")
                niveles_entrenamiento.append(nivel)
                
                textos_entrenamiento.append(f"Aprende a programar {palabra} desde lo básico")
                niveles_entrenamiento.append(nivel)
                
                textos_entrenamiento.append(f"{palabra} programación curso")
                niveles_entrenamiento.append(nivel)
                
                textos_entrenamiento.append(f"Tutorial de {palabra} para programadores")
                niveles_entrenamiento.append(nivel)
        
        # Crear pipeline - SIN parámetro stop_words
        self.modelo = make_pipeline(
            TfidfVectorizer(max_features=1000),  # Quitado stop_words completamente
            MultinomialNB()
        )
        
        # Entrenar
        textos_procesados = [self.preprocesar_texto(t) for t in textos_entrenamiento]
        self.modelo.fit(textos_procesados, niveles_entrenamiento)
        
        print("✅ Modelo de clasificación entrenado correctamente")
        print(f"   Clases: {self.modelo.classes_}")
    
    def predecir_nivel(self, titulo, descripcion=""):
        """Predice el nivel de un curso basado en título y descripción"""
        try:
            texto_completo = f"{titulo} {descripcion}"
            texto_procesado = self.preprocesar_texto(texto_completo)
            
            # Verificar si el texto tiene contenido
            if not texto_procesado or len(texto_procesado) < 3:
                return 'principiante', 50.0
            
            # Predicción del modelo
            nivel_predicho = self.modelo.predict([texto_procesado])[0]
            
            # Calcular confianza
            probabilidades = self.modelo.predict_proba([texto_procesado])[0]
            confianza = max(probabilidades) * 100
            
            # Verificar palabras clave para ajustar
            texto_lower = texto_completo.lower()
            
            # Sistema de votación por palabras clave
            votos = {'principiante': 0, 'intermedio': 0, 'avanzado': 0}
            
            for nivel, palabras in self.palabras_clave.items():
                for palabra in palabras:
                    if palabra in texto_lower:
                        votos[nivel] += 2  # Peso 2 por coincidencia directa
            
            # Si hay palabras clave muy específicas, dar más peso
            for palabra in ['básico', 'principiante', 'desde cero', 'introducción']:
                if palabra in texto_lower:
                    votos['principiante'] += 3
            
            for palabra in ['avanzado', 'experto', 'profesional', 'master']:
                if palabra in texto_lower:
                    votos['avanzado'] += 3
            
            # Determinar el nivel por votación si hay suficientes votos
            max_votos = max(votos.values())
            if max_votos > 3:  # Si hay suficientes votos de palabras clave
                for nivel, voto in votos.items():
                    if voto == max_votos:
                        return nivel, 85.0
            
            return nivel_predicho, round(confianza, 1)
            
        except Exception as e:
            print(f"Error en predicción: {e}")
            return 'principiante', 50.0
    
    def guardar_modelo(self, ruta='modelo_nivel.pkl'):
        """Guarda el modelo entrenado"""
        try:
            joblib.dump(self.modelo, ruta)
            print(f"✅ Modelo guardado en {ruta}")
            return True
        except Exception as e:
            print(f"Error guardando modelo: {e}")
            return False
    
    def cargar_modelo(self, ruta='modelo_nivel.pkl'):
        """Carga un modelo previamente entrenado"""
        try:
            if os.path.exists(ruta):
                self.modelo = joblib.load(ruta)
                print(f"✅ Modelo cargado desde {ruta}")
                return True
            return False
        except Exception as e:
            print(f"Error cargando modelo: {e}")
            return False