# src/models/media.py
from src.database.db_mysql import db

class ImagenVideo(db.Model):
    __tablename__ = 'imagenesvideos' # El nombre de la tabla que se crea/usa en la BD
    
    Id_imgV = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Id_Discoteca = db.Column(db.Integer, db.ForeignKey('discoteca.id_discoteca'), nullable=False)
    Tipo_Tabla = db.Column(db.String(50), nullable=False)  # Ej: 'artistas', 'eventos', 'discotecas'
    Id_referenciaTabla = db.Column(db.Integer, nullable=False) # FK a la tabla especificada en Tipo_Tabla
    Descripcion = db.Column(db.Text, nullable=True) # Descripción puede ser opcional
    Tipo_Archivo = db.Column(db.Enum('imagen', 'video', name='tipo_archivo_enum'), nullable=False) # 'tipo_archivo_enum' es el nombre del tipo ENUM en la BD
    Archivo = db.Column(db.String(255), nullable=False) # Path al archivo o URL
    
    # Relación con Discoteca (si una imagen/video siempre pertenece a una discoteca directamente)
    # El backref 'multimedia' en Discoteca permitirá acceder a discoteca.multimedia
    discoteca = db.relationship('Discoteca', backref=db.backref('multimedia', lazy='dynamic'))

    def __repr__(self):
        return f'<ImagenVideo {self.Id_imgV} ({self.Tipo_Archivo}) para {self.Tipo_Tabla} ID {self.Id_referenciaTabla}>'