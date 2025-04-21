from flask import Blueprint, flash, redirect, render_template, request, url_for
from src.database.db_mysql import db
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.DEBUG)

discoteca_info_bp = Blueprint("discoteca_info", __name__)

@discoteca_info_bp.route("/get_all_discotecas")
def index():
    try:
        result = db.session.execute(
            text("""
                SELECT d.id_discoteca, d.nombre, d.direccion, 
                    d.distrito, d.telefono FROM discoteca d;
            """)
        )
        discotecas = result.fetchall()
    except Exception as e:
        flash("Error al obtener las discotecas", "error")
        return redirect(url_for("home.index"))
    finally:
        db.session.close()
    return render_template("discoteca_info/index.html", discotecas=discotecas)

@discoteca_info_bp.route("/edit_discoteca/<int:id>", methods=["GET", "POST"])
def edit_discoteca(id):
    if request.method == "POST":
        dias = request.form["dias"]
        horario = request.form["horario"]
        descripcion = request.form["descripcion"]
        genero = request.form["genero"]
        latitud = request.form["latitud"]
        longitud = request.form["longitud"]

        logging.debug(f"Updating discoteca with data: dias={dias}, horario={horario}, descripcion={descripcion}, genero={genero}, latitud={latitud}, longitud={longitud}")

        try:
            result = db.session.execute(
                text("""
                    UPDATE info_complementaria
                    SET dias = :dias, horario = :horario, descripcion = :descripcion,
                        generos_musica = :genero, ubicacion_latitud = :latitud,
                        ubicacion_longitud = :longitud
                    WHERE id_discoteca = :id;
                """),
                {"dias": dias, "horario": horario, "descripcion": descripcion, "genero": genero, 
                    "latitud": latitud, "longitud": longitud, "id": id}
            )
            db.session.commit()
        except Exception as e:
            logging.error(e)
            flash("Error al actualizar la discoteca", "error")
            return redirect(url_for("discoteca_info.index"))
        finally:
            db.session.close()
        flash("Discoteca actualizada correctamente", "success")
        return redirect(url_for("discoteca_info.index"))
    else:
        try:
            result = db.session.execute(
                text("""
                    SELECT d.nombre, d.id_discoteca, ic.dias,
                    ic.horario, ic.descripcion, ic.generos_musica,
                    ic.ubicacion_latitud, ic.ubicacion_longitud
                    FROM discoteca d
                    INNER JOIN info_complementaria ic
                    on d.id_discoteca = ic.id_discoteca
                    WHERE d.id_discoteca = :id;
                """),
                {"id": id}
            )
            discoteca = result.fetchone()
        except Exception as e:
            logging.error(e)
            flash("Error al obtener la discoteca", "error")
            return redirect(url_for("discoteca_info.index"))
        finally:
            db.session.close()
        return render_template("discoteca_info/edit.html", discoteca=discoteca)