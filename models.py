# MultipleFiles/models.py
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Date, Text, DateTime, Boolean, ForeignKey, Table, LargeBinary
from sqlalchemy.orm import relationship
from flask_login import UserMixin
from datetime import datetime  # Importar datetime para la fecha de creación del post

db = SQLAlchemy()

# Tabla de asociación para la relación muchos a muchos entre User y Evento (asistentes)
event_attendees = Table('event_attendees', db.Model.metadata,
    Column('user_id', Integer, ForeignKey('Users.id'), primary_key=True),
    Column('event_id', Integer, ForeignKey('Eventos.id'), primary_key=True)
)

class User(db.Model, UserMixin):
    __tablename__ = 'Users'
    id = Column(Integer, primary_key=True)
    nombre = Column(String(100), nullable=False)
    apellido = Column(String(100), nullable=False)
    edad = Column(Integer, nullable=False)
    rol = Column(String(50), nullable=False, default='Estudiante')
    grado = Column(String(50), nullable=True)  # Grado puede ser nulo si no es estudiante
    fecha_inscripcion = Column(Date, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    is_admin = Column(Boolean, default=False)  # Campo para determinar si el usuario es administrador

    # Relación para las publicaciones del foro creadas por el usuario
    forum_posts = relationship('ForumPost', backref='autor', lazy=True)

    @property
    def is_active(self):
        return True

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)

    def __repr__(self):
        return f'<Usuario(nombre="{self.nombre}", apellido="{self.apellido}")>'

class Evento(db.Model):
    __tablename__ = 'Eventos'
    id = Column(Integer, primary_key=True)
    titulo = Column(String(200), nullable=False)
    descripcion = Column(Text, nullable=False)
    fecha_inicio = Column(DateTime, nullable=False)
    fecha_fin = Column(DateTime, nullable=False)
    ubicacion = Column(String(200), nullable=False)
    organizador_id = Column(Integer, ForeignKey('Users.id'), nullable=False)
    organizador = relationship('User', backref='eventos_organizados')

    # Relación para los asistentes al evento
    attendees = relationship('User', secondary=event_attendees, backref='events_attending')

    # Nuevas columnas para la imagen del evento
    imagen_data = Column(LargeBinary, nullable=True)
    imagen_mimetype = Column(String(50), nullable=True)

    def __repr__(self):
        return f'<Evento(titulo="{self.titulo}")>'

# Modelo para las publicaciones del foro
class ForumPost(db.Model):
    __tablename__ = 'ForumPosts'
    id = Column(Integer, primary_key=True)
    titulo = Column(String(255), nullable=False)
    contenido = Column(Text, nullable=False)
    imagen_data = Column(LargeBinary, nullable=True)
    imagen_mimetype = Column(String(50), nullable=True)
    video_url = Column(String(255), nullable=True)  # URL del video (ej: YouTube)
    fecha_creacion = Column(DateTime, nullable=False, default=datetime.now)
    autor_id = Column(Integer, ForeignKey('Users.id'), nullable=False)

    def __repr__(self):
        return f'<ForumPost(titulo="{self.titulo}", autor_id="{self.autor_id}")>'

