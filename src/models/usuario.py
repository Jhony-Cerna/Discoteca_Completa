from src.database.db_mysql import db

class Usuario(db.Model):
    __tablename__ = 'usuarios'

    id_usuario = db.Column(db.Integer, primary_key=True)
    id_persona = db.Column(db.Integer, db.ForeignKey('personas.id_persona'), nullable=False)
    rol = db.Column(db.String(25), nullable=False)

    persona = db.relationship('Persona', back_populates='usuario')
    discotecas = db.relationship('Discoteca', back_populates='administrador')