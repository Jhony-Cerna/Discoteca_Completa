import os

class Config:
    SQLALCHEMY_DATABASE_URI = 'mysql://root:Kaniem108%@localhost/discoteca'  # Cambia la URI según tus credenciales
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = 'mysecretkey'  # Clave secreta para sesiones
