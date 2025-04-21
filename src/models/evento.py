from datetime import datetime
from src.database.db_mysql import db

# Tabla de asociación definida primero
artistas_evento = db.Table('artistas_evento',
    db.Column('id_evento', db.Integer, db.ForeignKey('eventos.id_evento'), primary_key=True),
    db.Column('id_artista', db.Integer, db.ForeignKey('artistas.id_artista'), primary_key=True)
)

class Evento(db.Model):
    __tablename__ = 'eventos'
    __table_args__ = {'extend_existing': True}

    id_evento = db.Column(db.Integer, primary_key=True)
    nombre_evento = db.Column(db.String(100), nullable=False, unique=True)
    descripcion = db.Column(db.Text, nullable=False)
    fecha = db.Column(db.Date, nullable=False)
    lugar = db.Column(db.String(100), nullable=False)
    hora = db.Column(db.Time, nullable=False)
    id_discoteca = db.Column(db.Integer, default=1)

    # La relación ahora puede referenciar correctamente a Artista
    artistas = db.relationship(
    'Artista',
    secondary=artistas_evento,
    back_populates='eventos',  # Cambiado a back_populates
    lazy='dynamic'
)

    def __repr__(self):
        return f'<Evento {self.nombre_evento}>'

    def to_dict(self):
        return {
            'id_evento': self.id_evento,
            'nombre_evento': self.nombre_evento,
            'fecha': self.fecha.isoformat(),
            'hora': self.hora.strftime('%H:%M'),
            'lugar': self.lugar
        }

# Importación diferida para evitar circularidad
from src.models.artistas import Artista