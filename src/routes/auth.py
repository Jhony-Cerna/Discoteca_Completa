from flask import Blueprint, render_template, redirect, url_for, request, flash
from src.database.db_mysql import db
from werkzeug.security import check_password_hash
from sqlalchemy import text

auth = Blueprint('auth', __name__)


@auth.route('/', methods=['GET'])
def login():
    return render_template('login.html')


@auth.route('/ingresar', methods=['POST'])
def ingresar():
    email = request.form.get('email')
    password = request.form.get('password')

    print(f"Email ingresado: {email}")
    print(f"Contraseña ingresada: {password}")

    persona = db.session.execute(
        text("SELECT * FROM personas WHERE correo = :correo"),
        {"correo": email}
    ).fetchone()

    if persona is None:
        print("No se encontró la persona con ese correo.")
        flash("Correo o contraseña incorrectos", "error")
        return redirect(url_for('main.auth.login'))

    # Verificar la contraseña (usa hash si está encriptada)
    # o usar check_password_hash(persona.contrasenia, password)
    if persona.contrasenia != password:
        print("La contraseña no coincide.")
        flash("Correo o contraseña incorrectos", "error")
        return redirect(url_for('main.auth.login'))

    id_persona = persona.id_persona

    usuario = db.session.execute(
        text("SELECT * FROM usuarios WHERE id_persona = :id_persona"),
        {"id_persona": id_persona}
    ).fetchone()

    if usuario is None:
        print("No se encontró el usuario asociado.")
        flash("No se encontró el usuario asociado", "error")
        return redirect(url_for('main.auth.login'))

    # Validación adicional si el usuario es Administrador
    if usuario.rol == 'Administrador':
        # Verifica que tenga una discoteca aprobada
        discoteca = db.session.execute(
            text("SELECT * FROM discoteca WHERE admin_id = :admin_id"),
            {"admin_id": usuario.id_usuario}
        ).fetchone()

        if discoteca is None:
            flash("No tienes una discoteca asociada", "error")
            return redirect(url_for('main.auth.login'))
        
        # validacion de estado de la discoteca 
        if discoteca.estado != 1:  # 1 = Aprobado
            flash("Tu discoteca aún no ha sido aprobada", "error")
            return redirect(url_for('main.auth.login'))

        return redirect(url_for('main.pag_admin_principal'))

    elif usuario.rol == 'SuperAdministrador':
        return redirect(url_for('main.pag_SuperAdmin_principal'))

    else:
        print("El usuario no tiene permisos para acceder.")
        flash("No tienes permisos para acceder", "error")
        return redirect(url_for('main.auth.login'))
<<<<<<< HEAD
=======





>>>>>>> 8aaea206c700237b703ca5bf15974abe0c4cc594
