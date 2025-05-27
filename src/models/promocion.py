# src/models/promocion.py
from src.database.db_mysql import db
from sqlalchemy import Date, Numeric, ForeignKey, Integer, String, Text # Asegúrate de importar los tipos necesarios
from sqlalchemy.orm import relationship
# No necesitas importar Producto aquí directamente para la definición del modelo si usas strings en relationship

class Promocion(db.Model):
    __tablename__ = 'promociones'

    id_promocion = db.Column(Integer, primary_key=True, autoincrement=True)
    id_producto = db.Column(Integer, ForeignKey('productos.id_producto'), nullable=False)
    nombre = db.Column(String(100), nullable=False)
    descripcion = db.Column(Text) # Usar Text para descripciones más largas es una buena práctica
    precio_regular = db.Column(Numeric(10, 2), nullable=False)
    porcentaje_descuento = db.Column(Numeric(5, 2), nullable=False)
    cantidad_minima = db.Column(Integer, nullable=False, default=1)
    precio_final = db.Column(Numeric(10, 2), nullable=False)
    inicio = db.Column(Date, nullable=False) # Nombre de columna como en SQL
    fin = db.Column(Date, nullable=False)    # Nombre de columna como en SQL

    # Relación con Producto
    # El back_populates debe coincidir con el nombre de la relación en el modelo Producto
    producto = relationship('src.models.producto.Producto', back_populates='promociones')

    def __init__(self, id_producto, nombre, descripcion, precio_regular, porcentaje_descuento, cantidad_minima, precio_final, inicio, fin):
        self.id_producto = id_producto
        self.nombre = nombre
        self.descripcion = descripcion
        self.precio_regular = precio_regular
        self.porcentaje_descuento = porcentaje_descuento
        self.cantidad_minima = cantidad_minima
        self.precio_final = precio_final
        self.inicio = inicio
        self.fin = fin

    def __repr__(self):
        return f'<Promocion {self.id_promocion}: {self.nombre}>'