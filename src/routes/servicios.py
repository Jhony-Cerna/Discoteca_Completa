from flask import Blueprint, flash, redirect, render_template, request, url_for
from src.database.db_mysql import db
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.DEBUG)

servicios_bp = Blueprint("servicios", __name__)

@servicios_bp.route('/get_all_services')
def index():
    try:
        result = db.session.execute(
            text("""
                SELECT * FROM servicios;
            """)
        )
        servicios = result.fetchall()
    except Exception as e:
        flash('Error al obtener los servicios', 'error')
        return redirect(url_for('home.index'))
    finally:
        db.session.close()
    return render_template('servicios/index.html', servicios=servicios)

@servicios_bp.route('/add', methods=['GET', 'POST'])
def add_servicio():
    if request.method == 'POST':
        nombre = request.form['nombre_servicio']
        descripcion = request.form['descripcion']
        id_discoteca = request.form['id_discoteca']
        
        logging.debug(f"Adding servicio with data: nombre={nombre}, descripcion={descripcion}, id_discoteca={id_discoteca}")
        
        try:
            result = db.session.execute(
                text("""
                    INSERT INTO servicios (nombre_servicio, descripcion, id_discoteca)
                    VALUES (:nombre, :descripcion, :id_discoteca);
                """),
                {'nombre': nombre, 'descripcion': descripcion, 'id_discoteca': id_discoteca}
            )
            db.session.commit()
        except Exception as e:
            logging.error(e)
            flash('Error al agregar el servicio', 'error')
            return redirect(url_for('servicios.index'))
        finally:
            db.session.close()
        flash('Servicio agregado correctamente', 'success')
        return redirect(url_for('servicios.index'))
    return render_template('servicios/add.html')

@servicios_bp.route('/update_servicio/<int:id>', methods=['GET', 'POST'])
def update_servicio(id):
    if request.method == 'POST':
        nombre = request.form['nombre_servicio']
        descripcion = request.form['descripcion']
        id_discoteca = request.form['id_discoteca']

        logging.debug(f"Updating servicio with data: nombre={nombre}, descripcion={descripcion}, id_discoteca={id_discoteca}")
        
        try:
            result = db.session.execute(
                text("""
                    UPDATE servicios
                    SET nombre_servicio = :nombre, descripcion = :descripcion, id_discoteca = :id_discoteca
                    WHERE id_servicio = :id;
                """),
                {'nombre': nombre, 'descripcion': descripcion, 'id_discoteca': id_discoteca, 'id': id}
            )
            db.session.commit()
        except Exception as e:
            logging.error(e)
            flash('Error al actualizar el servicio', 'error')
            return redirect(url_for('servicios.index'))
        finally:
            db.session.close()
        flash('Servicio actualizado correctamente', 'success')
        return redirect(url_for('servicios.index'))
    else:
        try:
            result = db.session.execute(
                text("""
                    SELECT * FROM servicios
                    WHERE id_servicio = :id;
                """),
                {'id': id}
            )
            servicio = result.fetchone()
        except Exception as e:
            logging.error(e)
            flash('Error al obtener el servicio', 'error')
            return redirect(url_for('servicios.index'))
        finally:
            db.session.close()
        return render_template('servicios/edit.html', servicio=servicio)

@servicios_bp.route('/delete_servicio/<int:id>')
def delete_servicio(id):
    try:
        result = db.session.execute(
            text("""
                DELETE FROM servicios
                WHERE id_servicio = :id;
            """), 
            {'id': id}
        )
        db.session.commit()
    except Exception as e:
        logging.error(e)
        flash('Error al eliminar el servicio', 'error')
    finally:
        db.session.close()
    flash('Servicio eliminado correctamente', 'success')
    return redirect(url_for('servicios.index'))