from src.database.db_mysql import db
from datetime import datetime

class Promocion(db.Model):
    __tablename__ = 'promociones'
    __table_args__ = {'extend_existing': True}

    id_promocion = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text)
    tipo_promocion = db.Column(db.String(50), nullable=False)
    porcentaje_descuento = db.Column(db.Float)
    cantidad_comprar = db.Column(db.Integer)
    cantidad_pagar = db.Column(db.Integer)
    precio_fijo = db.Column(db.Float)
    stock = db.Column(db.Integer, nullable=False)
    fecha_inicio = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    fecha_fin = db.Column(db.Date, nullable=False)
    id_producto = db.Column(db.Integer, db.ForeignKey('productos.id_producto'), nullable=False)

    # Relación corregida con path completo
    producto = db.relationship(
        'src.models.producto.Producto',
        back_populates='promociones',
        foreign_keys=[id_producto]
    )

    def __repr__(self):
        return f'<Promocion {self.nombre}>'