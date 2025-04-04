# models/red_social.py
from src.database.db_mysql import db

class RedSocial(db.Model):
    __tablename__ = 'links'
    
    id_link = db.Column(db.Integer, primary_key=True)
    nombre_referencia = db.Column(db.String(100))
    id_discoteca = db.Column(db.Integer, default=1)
    id_referencia = db.Column(db.Integer, db.ForeignKey('artistas.id_artista'))  # Nombre real en tu BD
    
    # Relación con Artista usando el nombre correcto
    artista = db.relationship('Artista', 
                            back_populates='redes_sociales',
                            foreign_keys=[id_referencia])
    
    detalle = db.relationship('DetalleRedSocial', 
                            uselist=False, 
                            back_populates='red_social',
                            cascade='all, delete-orphan')

class DetalleRedSocial(db.Model):
    __tablename__ = 'detalle_link'
    
    id_detalle = db.Column(db.Integer, primary_key=True)
    tipo_link = db.Column(db.String(50))
    descripcion = db.Column(db.Text)
    url = db.Column(db.String(255))
    id_link = db.Column(db.Integer, db.ForeignKey('links.id_link'))

    red_social = db.relationship('RedSocial', back_populates='detalle')