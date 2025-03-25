from flask import Flask
from src.database.db_mysql import init_db
from src.routes import main  # Asegúrate de que esto esté importado correctamente
from src.routes.mesasyboxes import mesasyboxes_bp  # Importa el nuevo blueprint
from src.routes.productos import productos_bp
from src.routes.categorias import categorias_bp
from src.routes.servicios import servicios_bp
from src.routes.admin import admin_bp
from src.routes.clientes import clientes_bp
from src.routes.discoteca_info import discoteca_info_bp
from config import Config

app = Flask(__name__, template_folder='src/templates', static_folder='src/static')
app.config.from_object(Config)

init_db(app)  # Inicializa la base de datos
app.register_blueprint(main)  # Registra el Blueprint principal
app.register_blueprint(mesasyboxes_bp, url_prefix='/mesas_y_cajas')
app.register_blueprint(productos_bp, url_prefix='/productos')
app.register_blueprint(categorias_bp, url_prefix='/categorias')
app.register_blueprint(servicios_bp, url_prefix='/servicios')
app.register_blueprint(admin_bp, url_prefix='/admin')
app.register_blueprint(clientes_bp, url_prefix='/clientes')
app.register_blueprint(discoteca_info_bp, url_prefix='/discoteca_info')

# Imprime las rutas registradas
for rule in app.url_map.iter_rules():
    print(rule)

if __name__ == '__main__':
    app.run(debug=True)
