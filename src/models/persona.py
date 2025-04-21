from src.database.db_mysql import db
from datetime import datetime

class Persona(db.Model):
    __tablename__ = 'personas'

    id_persona = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False)
    apellido_paterno = db.Column(db.String(50), nullable=False)
    apellido_materno = db.Column(db.String(50), nullable=False)
    dni = db.Column(db.String(8), unique=True, nullable=False)
    telefono = db.Column(db.String(15))
    sexo = db.Column(db.Enum('masculino', 'femenino', name='sexo_types'))
    fecha_nacimiento = db.Column(db.Date, nullable=False)
    correo = db.Column(db.String(150), unique=True, nullable=False)
    contrasenia = db.Column(db.String(255), nullable=False)
    estado = db.Column(db.Boolean, default=True)
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)

    # Relación corregida
    usuario = db.relationship('Usuario', back_populates='persona', uselist=False)

    def nombre_completo(self):
        return f"{self.nombre} {self.apellido_paterno} {self.apellido_materno}"