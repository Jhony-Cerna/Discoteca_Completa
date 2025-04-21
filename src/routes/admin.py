from flask import Blueprint, flash, redirect, render_template, request, url_for
from src.database.db_mysql import db
from sqlalchemy import text
import logging
from datetime import datetime

logging.basicConfig(level=logging.DEBUG)

admin_bp = Blueprint("admin", __name__)

##administradores
@admin_bp.route("/get_all_admin")
def indexAdmin():
    try:
        result = db.session.execute(
            text("""
                SELECT p.id_persona, p.nombre, p.apellido_paterno, p.apellido_materno, 
                    p.dni, p.telefono, p.correo, p.estado FROM personas p
                    inner join usuarios u
                    on p.id_persona = u.id_persona
                    WHERE rol = "administrador";
            """)
        )
        usuarios = result.fetchall()
    except Exception as e:
        flash("Error al obtener los usuarios", "error")
        print(e)
        return redirect(url_for("home.index"))
    finally:
        db.session.close()
    return render_template("usuarios/admin/index.html", usuarios=usuarios)

@admin_bp.route("/add_admin", methods=["GET", "POST"])
def add_admin():
    if request.method == "POST":
        nombre = request.form["nombre"]
        apellido_paterno = request.form["apellido_paterno"]
        apellido_materno = request.form["apellido_materno"]
        dni = request.form["dni"]
        telefono = request.form["telefono"]
        sexo = request.form["sexo"]
        fecha_nacimiento = request.form["fecha_nacimiento"]
        correo = request.form["correo"]
        contrasenia = request.form["contrasenia"]
        estado = True
        fecha_registro = datetime.now()
        rol = "Administrador"

        try:
            result = db.session.execute(
                text("""
                    INSERT INTO personas (nombre, apellido_paterno, apellido_materno, dni, 
                        telefono, sexo, fecha_nacimiento, correo, contrasenia, estado, fecha_registro)
                    VALUES (:nombre, :apellido_paterno, :apellido_materno, :dni, :telefono, :sexo, 
                        :fecha_nacimiento, :correo, :contrasenia, :estado, :fecha_registro)
                """),
                {"nombre": nombre, "apellido_paterno": apellido_paterno, "apellido_materno": apellido_materno, 
                    "dni": dni, "telefono": telefono, "sexo": sexo, "fecha_nacimiento": fecha_nacimiento, 
                    "correo": correo, "contrasenia": contrasenia, "estado": estado, "fecha_registro": fecha_registro}
            )
            id_persona = result.lastrowid
            result = db.session.execute(
                text("""
                    INSERT INTO usuarios (id_persona, rol)
                    VALUES (:id_persona, :rol)
                """),
                {"id_persona": id_persona, "rol": rol}
            )
            db.session.commit()
        except Exception as e:
            flash("Error al agregar el usuario", "error")
            print(e)
            return redirect(url_for("admin.indexAdmin"))
        finally:
            db.session.close()
        flash("Usuario agregado correctamente", "success")
        return redirect(url_for("admin.indexAdmin"))
    return render_template("usuarios/admin/add.html")

@admin_bp.route("/delete_admin/<int:id_persona>")
def deleteAdmin(id_persona):
    try:
        result = db.session.execute(
            text("""
            DELETE FROM usuarios WHERE id_persona = :id_persona;
            """),
            {"id_persona": id_persona}
        )
        result = db.session.execute(
            text("""
            DELETE FROM personas WHERE id_persona = :id_persona;
            """),
            {"id_persona": id_persona}
        )
        db.session.commit()
    except Exception as e:
        flash("Error al eliminar el usuario", "error")
        print(e)
        return redirect(url_for("admin.indexAdmin"))
    finally:
        db.session.close()
    flash("Usuario eliminado correctamente", "success")
    return redirect(url_for("admin.indexAdmin"))

@admin_bp.route("/edit_admin/<int:id_persona>", methods=["GET", "POST"])
def editAdmin(id_persona):
    if request.method == "POST":
        nombre = request.form["nombre"]
        apellido_paterno = request.form["apellido_paterno"]
        apellido_materno = request.form["apellido_materno"]
        dni = request.form["dni"]
        telefono = request.form["telefono"]
        sexo = request.form["sexo"]
        fecha_nacimiento = request.form["fecha_nacimiento"]
        correo = request.form["correo"]
        contrasenia = request.form["contrasenia"]
        estado = request.form["estado"]

        try:
            result = db.session.execute(
                text("""
                    UPDATE personas SET nombre = :nombre, apellido_paterno = :apellido_paterno, 
                    apellido_materno = :apellido_materno, dni = :dni, telefono = :telefono, 
                    sexo = :sexo, fecha_nacimiento = :fecha_nacimiento, correo = :correo, 
                    contrasenia = :contrasenia, estado = :estado WHERE id_persona = :id_persona;
                """),
                {"nombre": nombre, "apellido_paterno": apellido_paterno, "apellido_materno": apellido_materno, 
                    "dni": dni, "telefono": telefono, "sexo": sexo, "fecha_nacimiento": fecha_nacimiento, 
                    "correo": correo, "contrasenia": contrasenia, "estado": estado, "id_persona": id_persona}
            )
            db.session.commit()
        except Exception as e:
            flash("Error al editar el usuario", "error")
            print(e)
            return redirect(url_for("admin.indexAdmin"))
        finally:
            db.session.close()
        flash("Usuario editado correctamente", "success")
        return redirect(url_for("admin.indexAdmin"))
    try:
        result = db.session.execute(
            text("""
                SELECT p.id_persona, p.nombre, p.apellido_paterno, p.apellido_materno, 
                    p.dni, p.telefono, p.sexo, p.fecha_nacimiento, p.estado, p.correo, 
                    p.contrasenia FROM personas p
                    inner join usuarios u
                    on p.id_persona = u.id_persona
                    WHERE p.id_persona = :id_persona;
            """),
            {"id_persona": id_persona}
        )
        usuario = result.fetchone()
    except Exception as e:
        flash("Error al obtener el usuario", "error")
        print(e)
        return redirect(url_for("admin.indexAdmin"))
    finally:
        db.session.close()
    return render_template("usuarios/admin/edit.html", usuario=usuario)