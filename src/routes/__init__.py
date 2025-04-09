from flask import Blueprint, jsonify, render_template
from sqlalchemy import text
from src.database.db_mysql import db
from .auth import auth  # Importa el Blueprint de auth

main = Blueprint('main', __name__)

# Registra el Blueprint de autenticación
main.register_blueprint(auth)


@main.route('/verificar_conexion', methods=['GET'])
def verificar_conexion():
    try:
        db.session.execute(text('SELECT 1'))
        return jsonify({"mensaje": "Conexión a la base de datos exitosa!"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@main.route('/test', methods=['GET'])
def test():
    return jsonify({"mensaje": "Ruta de prueba exitosa!"}), 200


# Ruta para la página principal
@main.route('/pagAdmin_principal', methods=['GET'])
def pag_admin_principal():
    return render_template('pagAdmin_principal.html')  # Renderiza el archivo pagAdmin_principal.html

# Ruta para la página principal del Super Admin
@main.route('/pagSuperAdmin_principal', methods=['GET'])
def pag_SuperAdmin_principal():
    return render_template('pagSuperAdmin_principal.html')  # Renderiza el archivo pagAdmin_principal.html
