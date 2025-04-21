# src/models/producto.py
from src.database.db_mysql import db
from sqlalchemy import Enum

class Producto(db.Model):
    __tablename__ = 'productos'
    __table_args__ = {'extend_existing': True}  # Mantenemos esto para evitar conflictos

    id_producto = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(Enum('box', 'mesa', 'bebida', 'piqueo', 'coctel', name='tipos_producto'), nullable=False)
    nombre = db.Column(db.String(50), nullable=False, unique=True)
    descripcion = db.Column(db.String(255))  # Nuevo campo del esquema SQL
    precio_regular = db.Column(db.Numeric(10, 2), nullable=False)  # Usamos Numeric para decimales
    promocion = db.Column(db.Boolean, default=False)  # Nuevo campo del esquema SQL
    

    # Relación con Promocion (ajustada para usar strings)
    promociones = db.relationship(
        'src.models.promocion.Promocion',
        back_populates='producto',
        cascade='all, delete-orphan',
        lazy='dynamic'
    )

    def __repr__(self):
        return f'<Producto {self.nombre}>'