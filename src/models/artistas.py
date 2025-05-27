# src/models/artistas.py
from src.database.db_mysql import db
from src.models.evento import artistas_evento  # Importar la tabla de asociación

class Artista(db.Model):
    __tablename__ = 'artistas'
    __table_args__ = {'extend_existing': True}

    id_artista = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False, unique=True)
    genero_musical = db.Column(db.String(50), nullable=False)
    descripcion = db.Column(db.Text, nullable=False)
    
    # Relación corregida usando la tabla importada
    eventos = db.relationship(
    'Evento', 
    secondary=artistas_evento, 
    back_populates='artistas',  # Debe coincidir con el nombre en Evento
    lazy='dynamic'
)
    
    redes_sociales = db.relationship(
        'RedSocial', 
        back_populates='artista',
        foreign_keys='RedSocial.id_referencia',  # Especificar clave foránea
        cascade='all, delete-orphan'
    )

    def __repr__(self):
        return f'<Artista {self.nombre}>'
    
    