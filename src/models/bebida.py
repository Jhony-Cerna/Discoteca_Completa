from src.database.db_mysql import db

class Bebida(db.Model):
    __tablename__ = 'bebidas'
    
    id_producto = db.Column(db.Integer, db.ForeignKey('productos.id_producto'), primary_key=True)
    marca = db.Column(db.String(50))
    tamanio = db.Column(db.Numeric(10, 2))
    stock = db.Column(db.Integer, default=0)
    id_categoria = db.Column(db.Integer, db.ForeignKey('categoria_bebidas.id_categoria'))
    
    # Relaciones
    producto = db.relationship('src.models.producto.Producto', backref='bebida', uselist=False)
    categoria = db.relationship('CategoriaBebida', backref='bebidas')

    def __repr__(self):
        return f'<Bebida {self.marca} {self.tamanio}L>'