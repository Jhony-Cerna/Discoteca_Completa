from flask import Blueprint, render_template, redirect, url_for, request, flash, session # <--- Importa session
from src.database.db_mysql import db
from werkzeug.security import check_password_hash # Asegúrate de usar esto si tus contraseñas están hasheadas
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

    # IMPORTANTE: Deberías estar usando check_password_hash si las contraseñas están encriptadas.
    # Ejemplo: if not check_password_hash(persona.contrasenia, password):
    if persona.contrasenia != password: # Asegúrate que esto sea lo que quieres. Si no hay hash, es inseguro.
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

    # Guardar información básica del usuario en sesión
    session['user_id'] = usuario.id_usuario
    session['user_rol'] = usuario.rol
    session['user_persona_id'] = id_persona


    if usuario.rol == 'Administrador':
        discoteca = db.session.execute(
            text("SELECT id_discoteca, estado FROM discoteca WHERE admin_id = :admin_id"), # Selecciona también id_discoteca
            {"admin_id": usuario.id_usuario}
        ).fetchone()

        if discoteca is None:
            flash("No tienes una discoteca asociada", "error")
            session.clear() # Limpiar sesión si hay error
            return redirect(url_for('main.auth.login'))
        
        if discoteca.estado != 1:  # 1 = Aprobado
            flash("Tu discoteca aún no ha sido aprobada", "error")
            session.clear() # Limpiar sesión si hay error
            return redirect(url_for('main.auth.login'))

        # Si todo está bien, guarda el id_discoteca en la sesión
        session['id_discoteca'] = discoteca.id_discoteca
        print(f"Discoteca ID {discoteca.id_discoteca} guardado en sesión para el admin {usuario.id_usuario}")

        return redirect(url_for('main.pag_admin_principal'))

    elif usuario.rol == 'SuperAdministrador':
        # El SuperAdministrador podría no tener una 'id_discoteca' específica
        # o podrías manejarlo de otra forma si es necesario.
        # Por ahora, no guardamos 'id_discoteca' para él.
        if 'id_discoteca' in session:
            session.pop('id_discoteca', None) # Eliminar si existiera de un login anterior
        return redirect(url_for('main.pag_SuperAdmin_principal'))

    else:
        print("El usuario no tiene permisos para acceder.")
        flash("No tienes permisos para acceder", "error")
        session.clear() # Limpiar sesión
        return redirect(url_for('main.auth.login'))

# Es buena práctica tener una ruta para cerrar sesión
@auth.route('/logout')
def logout():
    session.clear() # Elimina todas las variables de la sesión
    flash("Has cerrado sesión exitosamente.", "info")
    return redirect(url_for('main.auth.login'))