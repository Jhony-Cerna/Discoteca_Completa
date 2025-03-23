from flask import Blueprint, flash, redirect, render_template, request, url_for
from src.database.db_mysql import db
from sqlalchemy import text
import logging
from datetime import datetime

logging.basicConfig(level=logging.DEBUG)

clientes_bp = Blueprint("clientes", __name__)

##clientes
@clientes_bp.route("/get_all_clients")
def indexUser():
    try:
        result = db.session.execute(
            text("""
                SELECT p.id_persona, p.nombre, p.apellido_paterno, p.apellido_materno, 
                    p.dni, p.telefono, p.correo, p.estado FROM personas p
                    inner join usuarios u
                    on p.id_persona = u.id_persona
                    WHERE rol = "cliente";
            """)
        )
        usuarios = result.fetchall()
    except Exception as e:
        flash("Error al obtener los usuarios", "error")
        print(e)
        return redirect(url_for("home.index"))
    finally:
        db.session.close()
    return render_template("usuarios/clientes/index.html", usuarios=usuarios)

@clientes_bp.route("/add_client", methods=["GET", "POST"])
def add_client():
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
        estado = False
        fecha_registro = datetime.now()
        rol = "cliente"

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
            return redirect(url_for("home.index"))
        finally:
            db.session.close()
        flash("Usuario agregado correctamente", "success")
        return redirect(url_for("clientes.indexUser"))
    return render_template("usuarios/clientes/add.html")

@clientes_bp.route("/delete_client/<int:id>")
def delete_client(id):
    try:
        result = db.session.execute(
            text("""
                DELETE FROM usuarios WHERE id_persona = :id;
            """),
            {"id": id}
        )
        result = db.session.execute(
            text("""
                DELETE FROM personas WHERE id_persona = :id;
            """),
            {"id": id}
        )
        db.session.commit()
    except Exception as e:
        flash("Error al eliminar el usuario", "error")
        print(e)
        return redirect(url_for("clientes.indexUser"))
    finally:
        db.session.close()
    flash("Usuario eliminado correctamente", "success")
    return redirect(url_for("clientes.indexUser"))

@clientes_bp.route("/edit_client/<int:id>", methods=["GET", "POST"])
def edit_client(id):
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
                     contrasenia = :contrasenia, estado = :estado
                    WHERE id_persona = :id;
                """),
                {"nombre": nombre, "apellido_paterno": apellido_paterno, "apellido_materno": apellido_materno, 
                 "dni": dni, "telefono": telefono, "sexo": sexo, "fecha_nacimiento": fecha_nacimiento, 
                 "correo": correo, "contrasenia": contrasenia, "estado": estado, "id": id}
            )
            db.session.commit()
        except Exception as e:
            flash("Error al editar el usuario", "error")
            print(e)
            return redirect(url_for("clientes.indexUser"))
        finally:
            db.session.close()
        flash("Usuario editado correctamente", "success")
        return redirect(url_for("clientes.indexUser"))
    try:
        result = db.session.execute(
            text("""
                SELECT p.id_persona, p.nombre, p.apellido_paterno, p.apellido_materno, 
                    p.dni, p.telefono, p.sexo, p.fecha_nacimiento, p.estado, p.correo, 
                    p.contrasenia FROM personas p
                    inner join usuarios u
                    on p.id_persona = u.id_persona
                    WHERE p.id_persona = :id;
            """),
            {"id": id}
        )
        usuario = result.fetchone()
    except Exception as e:
        flash("Error al obtener el usuario", "error")
        print(e)
        return redirect(url_for("clientes.indexUser"))
    finally:
        db.session.close()
    return render_template("usuarios/clientes/edit.html", usuario=usuario)