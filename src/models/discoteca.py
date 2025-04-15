from src.database.db_mysql import db

class Discoteca(db.Model):
    __tablename__ = 'discoteca'
    
    id_discoteca = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False)
    direccion = db.Column(db.String(255), nullable=False)
    departamento = db.Column(db.String(50), nullable=False)
    provincia = db.Column(db.String(50), nullable=False)
    distrito = db.Column(db.String(50), nullable=False)
    telefono = db.Column(db.String(15), nullable=False)
    estado = db.Column(db.SmallInteger, nullable=False)
    admin_id = db.Column(db.Integer, db.ForeignKey('usuarios.id_usuario'), nullable=False)

    # Relación simplificada
    administrador = db.relationship('Usuario', back_populates='discotecas')
    
    def estado_texto(self):
        return ['Pendiente', 'Aprobado', 'Rechazado'][self.estado]