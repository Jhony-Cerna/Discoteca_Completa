# src/models/tablas_asociacion.py
from src.database.db_mysql import db

artistas_evento = db.Table(
    'artistas_evento',
    db.Column('id_evento', db.Integer, db.ForeignKey('eventos.id_evento'), primary_key=True),
    db.Column('id_artista', db.Integer, db.ForeignKey('artistas.id_artista'), primary_key=True)
)