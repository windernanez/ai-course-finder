from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class BusquedaHistorial(db.Model):
    __tablename__ = 'historial_busquedas'
    
    id = db.Column(db.Integer, primary_key=True)
    lenguaje = db.Column(db.String(50), nullable=False)
    nivel = db.Column(db.String(50), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    total_videos = db.Column(db.Integer, default=0)

    def to_dict(self):
        return {
            'id': self.id,
            'lenguaje': self.lenguaje,
            'nivel': self.nivel,
            'timestamp': str(self.timestamp),
            'total_videos': self.total_videos
        }

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    google_id = db.Column(db.String(100), unique=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    nombre = db.Column(db.String(100))
    imagen = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'nombre': self.nombre,
            'imagen': self.imagen
        }

class UserProgress(db.Model):
    __tablename__ = 'user_progress'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    lenguaje = db.Column(db.String(50), nullable=False)
    nivel = db.Column(db.String(50), nullable=False)
    videos_vistos = db.Column(db.Text, default='') # IDs separados por coma
    total_videos = db.Column(db.Integer, default=0)
    examen_aprobado = db.Column(db.Boolean, default=False)
    puntuacion_examen = db.Column(db.Integer, default=0)
    certificado_generado = db.Column(db.Boolean, default=False)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        vistos = [v for v in self.videos_vistos.split(',') if v] if self.videos_vistos else []
        # Requisito de 4 videos para llegar al 100% (según pedido del usuario)
        progreso = min(len(vistos) / 4 * 100, 100)
        return {
            'id': self.id,
            'user_id': self.user_id,
            'lenguaje': self.lenguaje,
            'nivel': self.nivel,
            'videos_vistos': vistos,
            'total_videos': self.total_videos,
            'progreso': round(progreso, 2),
            'examen_aprobado': self.examen_aprobado,
            'puntuacion_examen': self.puntuacion_examen,
            'certificado_generado': self.certificado_generado
        }
