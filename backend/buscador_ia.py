from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import time
import re
from clasificador_nivel import ClasificadorNivelCursos

class BuscadorCursosIA:
    def __init__(self, api_key):
        self.api_key = api_key
        self.youtube = build('youtube', 'v3', developerKey=api_key)
        self.clasificador = ClasificadorNivelCursos()
        
        # Base de datos de canales recomendados por lenguaje
        self.canales_recomendados = {
            'python': [
                'UCwvNEsQ9QnVvL7tIqR7X6fA',  # Pildorasinformaticas
                'UCCezIgC97PvUuR4_gbFUs5g',  # Corey Schafer
                'UCCezIgC97PvUuR4_gbFUs5g',  # Sentdex
            ],
            'javascript': [
                'UCW5YeuERMmlnqo4oq8vwUpg',  # The Net Ninja
                'UCSJbGtTlrDami-tDGPUV9-w',  # Academind
                'UC8butISFwT-Wl7EV0hUK0BQ',  # freeCodeCamp
            ],
            'java': [
                'UCmRzEy2jVJ5JwQJxVwKx6xA',  # Programming with Mosh
                'UCF7x1q1IjqB0Eft-0lqI-0Q',  # Cave of Programming
            ]
        }
    
    def buscar_videos(self, lenguaje, nivel, max_resultados=15):
        """
        Busca videos de programación según lenguaje y nivel
        """
        try:
            # Construir consulta de búsqueda
            consultas = [
                f"curso {lenguaje} programación {nivel} tutorial",
                f"aprender {lenguaje} {nivel} desde cero",
                f"{lenguaje} programming {nivel} course",
            ]
            
            if nivel == 'principiante':
                consultas.insert(0, f"{lenguaje} para principiantes tutorial")
            elif nivel == 'avanzado':
                consultas.insert(0, f"{lenguaje} avanzado expertos tips")
            
            todos_videos = []
            
            # Realizar búsquedas con diferentes consultas
            for consulta in consultas[:2]:  # Solo usar 2 consultas para no exceder cuota
                videos = self._buscar_en_youtube(consulta, max_resultados // 2)
                todos_videos.extend(videos)
                time.sleep(0.5)  # Pequeña pausa entre consultas
            
            # Filtrar y clasificar videos
            videos_procesados = []
            for video in todos_videos:
                video_info = self._procesar_video(video, lenguaje, nivel)
                if video_info and self._validar_video(video_info, lenguaje):
                    videos_procesados.append(video_info)
            
            # Ordenar por relevancia
            videos_procesados.sort(key=lambda x: (x['relevancia'], x['confianza_nivel']), reverse=True)
            
            return videos_procesados[:max_resultados]
            
        except HttpError as e:
            print(f"Error en API de YouTube: {e}")
            return []
        except Exception as e:
            print(f"Error inesperado: {e}")
            return []
    
    def _buscar_en_youtube(self, consulta, max_resultados):
        """Realiza la búsqueda en YouTube"""
        try:
            request = self.youtube.search().list(
                part='snippet',
                q=consulta,
                type='video',
                maxResults=max_resultados,
                relevanceLanguage='es',
                videoDuration='medium',  # Videos de duración media (4-20 min)
                videoDefinition='high'   # Alta definición
            )
            
            response = request.execute()
            return response.get('items', [])
            
        except Exception as e:
            print(f"Error en búsqueda: {e}")
            return []
    
    def _procesar_video(self, video, lenguaje_busqueda, nivel_busqueda):
        """Procesa y enriquece la información del video"""
        try:
            snippet = video['snippet']
            video_id = video['id']['videoId']
            
            titulo = snippet['title']
            descripcion = snippet['description'][:500]  # Limitar descripción
            canal = snippet['channelTitle']
            canal_id = snippet['channelId']
            fecha = snippet['publishedAt'][:10]
            miniatura = snippet['thumbnails']['high']['url']
            
            # Obtener estadísticas del video
            stats = self._obtener_estadisticas(video_id)
            
            # Clasificar nivel
            nivel_predicho, confianza = self.clasificador.predecir_nivel(titulo, descripcion)
            
            # Calcular relevancia
            relevancia = self._calcular_relevancia(
                titulo, descripcion, lenguaje_busqueda, 
                nivel_busqueda, nivel_predicho, stats
            )
            
            # Crear enlace
            enlace = f"https://www.youtube.com/watch?v={video_id}"
            
            return {
                'id': video_id,
                'titulo': titulo,
                'canal': canal,
                'canal_id': canal_id,
                'descripcion': descripcion[:200] + '...' if len(descripcion) > 200 else descripcion,
                'fecha': fecha,
                'miniatura': miniatura,
                'nivel_detectado': nivel_predicho,
                'confianza_nivel': round(confianza, 1),
                'nivel_solicitado': nivel_busqueda,
                'relevancia': relevancia,
                'vistas': stats.get('vistas', 'N/A'),
                'likes': stats.get('likes', 'N/A'),
                'enlace': enlace,
                'duracion': stats.get('duracion', 'N/A')
            }
            
        except Exception as e:
            print(f"Error procesando video: {e}")
            return None
    
    def _obtener_estadisticas(self, video_id):
        """Obtiene estadísticas detalladas del video"""
        try:
            request = self.youtube.videos().list(
                part='statistics,contentDetails',
                id=video_id
            )
            response = request.execute()
            
            if response['items']:
                stats = response['items'][0]['statistics']
                detalles = response['items'][0]['contentDetails']
                
                # Formatear números
                vistas = self._formatear_numero(stats.get('viewCount', '0'))
                likes = self._formatear_numero(stats.get('likeCount', '0'))
                
                # Procesar duración ISO 8601
                duracion = self._procesar_duracion(detalles.get('duration', 'PT0M'))
                
                return {
                    'vistas': vistas,
                    'likes': likes,
                    'duracion': duracion
                }
        except:
            pass
        
        return {'vistas': 'N/A', 'likes': 'N/A', 'duracion': 'N/A'}
    
    def _calcular_relevancia(self, titulo, descripcion, lenguaje, nivel_buscado, nivel_detectado, stats):
        """Calcula un score de relevancia para el video"""
        score = 50  # Base
        
        texto_completo = f"{titulo} {descripcion}".lower()
        
        # Bonus por lenguaje en título
        if lenguaje.lower() in titulo.lower():
            score += 20
        
        # Bonus por nivel coincidente
        if nivel_buscado == nivel_detectado:
            score += 25
        elif (nivel_buscado == 'principiante' and nivel_detectado == 'intermedio'):
            score += 10  # Intermedio puede ser útil para principiantes
        
        # Bonus por palabras clave de calidad
        palabras_calidad = ['curso', 'tutorial', 'aprende', 'guía', 'completo']
        for palabra in palabras_calidad:
            if palabra in texto_completo:
                score += 2
        
        # Bonus por popularidad (si tenemos stats)
        if stats:
            vistas_num = self._extraer_numero(stats.get('vistas', '0'))
            if vistas_num > 10000:
                score += 10
            elif vistas_num > 1000:
                score += 5
        
        return min(100, score)  # Máximo 100
    
    def _validar_video(self, video_info, lenguaje):
        """Valida que el video sea relevante"""
        if not video_info:
            return False
        
        titulo = video_info['titulo'].lower()
        desc = video_info['descripcion'].lower()
        
        # Excluir ciertos patrones
        excluir = ['react', 'angular', 'vue', 'node']  # Otros frameworks
        if lenguaje.lower() == 'javascript':
            # Si buscamos JavaScript, no excluir estos términos
            pass
        else:
            for term in excluir:
                if term in titulo and term not in lenguaje.lower():
                    if term in desc:
                        return False
        
        return True
    
    def _formatear_numero(self, num_str):
        """Formatea números grandes (ej: 1500000 -> 1.5M)"""
        try:
            num = int(num_str)
            if num >= 1000000:
                return f"{num/1000000:.1f}M"
            elif num >= 1000:
                return f"{num/1000:.1f}K"
            return str(num)
        except:
            return num_str
    
    def _procesar_duracion(self, duracion_iso):
        """Convierte duración ISO 8601 a formato legible"""
        import re
        patron = re.compile(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?')
        match = patron.match(duracion_iso)
        
        if match:
            horas = match.group(1) or '0'
            minutos = match.group(2) or '0'
            segundos = match.group(3) or '0'
            
            if int(horas) > 0:
                return f"{horas}:{minutos.zfill(2)}:{segundos.zfill(2)}"
            else:
                return f"{minutos}:{segundos.zfill(2)}"
        
        return duracion_iso
    
    def _extraer_numero(self, valor):
        """Extrae número de string formateado (ej: 1.5K -> 1500)"""
        try:
            if valor == 'N/A':
                return 0
            
            valor = str(valor)
            if 'K' in valor:
                return int(float(valor.replace('K', '')) * 1000)
            elif 'M' in valor:
                return int(float(valor.replace('M', '')) * 1000000)
            else:
                return int(valor)
        except:
            return 0
    
    def recomendar_canales(self, lenguaje):
        """Recomienda canales populares para un lenguaje"""
        canales = self.canales_recomendados.get(lenguaje.lower(), [])
        info_canales = []
        
        for canal_id in canales[:3]:  # Limitar a 3 canales
            try:
                request = self.youtube.channels().list(
                    part='snippet,statistics',
                    id=canal_id
                )
                response = request.execute()
                
                if response['items']:
                    item = response['items'][0]
                    info_canales.append({
                        'nombre': item['snippet']['title'],
                        'id': canal_id,
                        'suscriptores': self._formatear_numero(item['statistics'].get('subscriberCount', '0')),
                        'videos': item['statistics'].get('videoCount', '0'),
                        'miniatura': item['snippet']['thumbnails']['default']['url']
                    })
            except:
                pass
        
        return info_canales