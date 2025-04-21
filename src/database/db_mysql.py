from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Importar modelos DESPUÉS de crear la instancia
from src.models import Persona, Usuario, Discoteca

def init_db(app):
    db.init_app(app)
