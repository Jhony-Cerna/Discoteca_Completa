from src.database.db_mysql import db

class CategoriaBebida(db.Model):
    __tablename__ = 'categoria_bebidas'
    
    id_categoria = db.Column(db.Integer, primary_key=True)
    nombre_categoria = db.Column(db.String(50), nullable=False)
    descripcion = db.Column(db.String(255))

    def __repr__(self):
        return f'<Categoria {self.nombre_categoria}>'