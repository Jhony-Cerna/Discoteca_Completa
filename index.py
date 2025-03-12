from flask import Flask
from src.database.db_mysql import init_db
from src.routes import main  # Asegúrate de que esto esté importado correctamente
from src.routes.mesasyboxes import mesasyboxes_bp  # Importa el nuevo blueprint
from config import Config

app = Flask(__name__, template_folder='src/templates', static_folder='src/static')
app.config.from_object(Config)

init_db(app)  # Inicializa la base de datos
app.register_blueprint(main)  # Registra el Blueprint principal
app.register_blueprint(mesasyboxes_bp, url_prefix='/mesas_y_cajas')


# Imprime las rutas registradas
for rule in app.url_map.iter_rules():
    print(rule)

if __name__ == '__main__':
    app.run(debug=True)
