from flask import Flask
from src.database.db_mysql import init_db
from src.routes import main  # Asegúrate de que esto esté importado correctamente
from src.routes.mesasyboxes import mesasyboxes_bp  # Importa el nuevo blueprint
from src.routes.eventos import eventos_bp
# MODELS:
from src.models.artistas import Artista
from src.models.evento import Evento

from src.routes.artistas import artistas_bp

from src.models.red_social import RedSocial, DetalleRedSocial

from src.routes.redes_sociales import redes_bp

from src.routes.promociones import promociones_bp

from src.routes.bebidas import bebidas_bp  # Nueva importación

from src.routes.discoteca_info import discoteca_info_bp

from src.routes.productos import productos_bp

from config import Config

app = Flask(__name__, template_folder='src/templates', static_folder='src/static')
app.config.from_object(Config)

init_db(app)  # Inicializa la base de datos
app.register_blueprint(main)  # Registra el Blueprint principal
app.register_blueprint(mesasyboxes_bp, url_prefix='/mesas_y_cajas')
app.register_blueprint(eventos_bp)

app.register_blueprint(artistas_bp)

app.register_blueprint(redes_bp)

app.register_blueprint(promociones_bp)

app.register_blueprint(bebidas_bp)  # Nuevo registro

app.register_blueprint(discoteca_info_bp, url_prefix='/discoteca_info')

app.register_blueprint(productos_bp, url_prefix='/productos')

# Imprime las rutas registradas
for rule in app.url_map.iter_rules():
    print(rule)

if __name__ == '__main__':
    app.run(debug=True)
