# src/models/media.py
from src.database.db_mysql import db

class ImagenVideo(db.Model):  # <- ¡El nombre debe coincidir exactamente!
    __tablename__ = 'ImagenesVideos'
    
    Id_imgV = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Id_Discoteca = db.Column(db.Integer, db.ForeignKey('discoteca.id_discoteca'), nullable=False)
    Tipo_Tabla = db.Column(db.String(50), nullable=False)
    Id_referenciaTabla = db.Column(db.Integer, nullable=False)
    Descripcion = db.Column(db.Text)
    Tipo_Archivo = db.Column(db.Enum('imagen', 'video', name='tipo_archivo'), nullable=False)
    Archivo = db.Column(db.String(255), nullable=False)
    
    # Relación opcional con Discoteca
    discoteca = db.relationship('Discoteca', backref='multimedia')