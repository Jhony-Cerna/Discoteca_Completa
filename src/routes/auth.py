from flask import Blueprint, render_template, redirect, url_for, request, flash
from src.database.db_mysql import db  # Asegúrate de que esto esté importado correctamente
from werkzeug.security import check_password_hash  # Para verificar la contraseña
from sqlalchemy import text  # Importa text de SQLAlchemy

auth = Blueprint('auth', __name__)

# Ruta para el login
@auth.route('/', methods=['GET'])
def login():
    return render_template('login.html')  # Renderiza el archivo login.html



# Ruta para manejar el ingreso
@auth.route('/ingresar', methods=['POST'])
def ingresar():
    email = request.form.get('email')
    password = request.form.get('password')

    print(f"Email ingresado: {email}")  # Verifica el correo ingresado
    print(f"Contraseña ingresada: {password}")  # Verifica la contraseña ingresada

    # Verificar si el correo existe en la tabla personas
    persona = db.session.execute(
        text("SELECT * FROM personas WHERE correo = :correo"), 
        {"correo": email}
    ).fetchone()

    if persona is None:
        print("No se encontró la persona con ese correo.")  # Mensaje de depuración
        flash("Correo o contraseña incorrectos", "error")
        return redirect(url_for('main.auth.login'))

    # Verificar la contraseña
    if persona.contrasenia != password:  # Comparar directamente si está en texto plano
        print("La contraseña no coincide.")  # Mensaje de depuración
        flash("Correo o contraseña incorrectos", "error")
        return redirect(url_for('main.auth.login'))


    # Obtener el id_persona
    id_persona = persona.id_persona

    # Verificar el rol en la tabla usuarios
    usuario = db.session.execute(
        text("SELECT * FROM usuarios WHERE id_persona = :id_persona"), 
        {"id_persona": id_persona}
    ).fetchone()

    if usuario is None:
        print("No se encontró el usuario asociado.")  # Mensaje de depuración
        flash("No se encontró el usuario asociado", "error")
        return redirect(url_for('main.auth.login'))

    # Verificar el rol
    if usuario.rol == 'Administrador':
        return redirect(url_for('main.pag_admin_principal'))
    elif usuario.rol == 'SuperAdministrador':
        return redirect(url_for('main.pag_SuperAdmin_principal'))
    else:
        print("El usuario no tiene permisos para acceder.")  # Mensaje de depuración
        flash("No tienes permisos para acceder", "error")
        return redirect(url_for('main.auth.login'))





