import logging
import os
from flask import Flask
from src.database.db_mysql import init_db

from src.routes import main  # Asegúrate de que esto esté importado correctamente
from src.routes.mesasyboxes import mesasyboxes_bp  # Importa el nuevo blueprint
from src.routes.eventos import eventos_bp
# MODELS:
from src.models.artistas import Artista
from src.models.evento import Evento
#Para imagenes y videos:
from werkzeug.utils import secure_filename

from src.routes.artistas import artistas_bp

from src.models.red_social import RedSocial, DetalleRedSocial

from src.routes.redes_sociales import redes_bp


from src.routes.bebidas import bebidas_bp  # Nueva importación

from src.routes.discoteca_info import discoteca_info_bp

from src.routes.productos import productos_bp

from src.routes.admin import admin_bp

from src.routes.clientes import clientes_bp

from src.routes.categorias import categorias_bp

from src.routes.discotecas import discotecas_bp

from src.routes.servicios import servicios_bp

from src.routes.promociones_routes import promociones_bp

# Configuración del logger
logging.basicConfig(level=logging.INFO) # O podrías usar logging.DEBUG para ver incluso más detalles
        # Asegúrate de que el logger de la app también esté en el nivel deseado


from flask import Flask
from flask_wtf.csrf import CSRFProtect


from config import Config

app = Flask(__name__, template_folder='src/templates', static_folder='src/static')
app.config.from_object(Config)


# Configuración explícita del nivel del logger de la app
if app.debug:
    app.logger.setLevel(logging.DEBUG)  # Mensajes DEBUG, INFO, WARNING, ERROR, CRITICAL
    logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO) # Opcional: para ver logs de SQLAlchemy
else:
    app.logger.setLevel(logging.INFO)



# Filtro para videos
@app.template_filter('format_video_url')
def format_video_url(url):
    if 'youtube.com/watch?v=' in url:
        return url.replace('watch?v=', 'embed/')
    elif 'youtu.be/' in url:
        return url.replace('youtu.be/', 'youtube.com/embed/')
    elif 'vimeo.com/' in url:
        return url.replace('vimeo.com/', 'player.vimeo.com/video/')
    return url

#Imagenes
app.config['UPLOAD_FOLDER'] = 'src/static/uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'mov'}
#termina lo de imagenes

init_db(app)  # Inicializa la base de datos
app.register_blueprint(main)  # Registra el Blueprint principal
app.register_blueprint(mesasyboxes_bp, url_prefix='/mesas_y_cajas')
app.register_blueprint(eventos_bp)

app.register_blueprint(artistas_bp)

app.register_blueprint(redes_bp)


app.register_blueprint(bebidas_bp)  # Nuevo registro

app.register_blueprint(discoteca_info_bp, url_prefix='/discoteca_info')

app.register_blueprint(productos_bp, url_prefix='/productos')

app.register_blueprint(admin_bp, url_prefix='/admin')

app.register_blueprint(clientes_bp, url_prefix='/clientes')

app.register_blueprint(categorias_bp, url_prefix='/categorias')

app.register_blueprint(discotecas_bp, url_prefix='/discotecas')

app.register_blueprint(servicios_bp, url_prefix='/servicios')

app.register_blueprint(promociones_bp, url_prefix='/promociones')

# Imprime las rutas registradas
for rule in app.url_map.iter_rules():
    print(rule)

if __name__ == '__main__':
    app.run(debug=True)
