from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from src.database.db_mysql import db
from sqlalchemy import text

categorias_bp = Blueprint("categorias", __name__)

@categorias_bp.route('/get_all_categorias')
def index():
    try:
        result = db.session.execute(
            text("""
                SELECT * FROM categoria_bebidas
            """)
        )
        categorias = result.fetchall()
    except Exception as e:
        flash('Error al obtener las categorias', 'error')
        return redirect(url_for('home.index'))
    finally:
        db.session.close()
    return render_template('categorias/index.html', categorias=categorias)
    
@categorias_bp.route('/add_categoria', methods=['GET', 'POST'])
def add_categoria():
    if request.method == 'POST':
        nombre = request.form['nombre_categoria']
        descripcion = request.form['descripcion_categoria']
        
        try:
            result = db.session.execute(
                text("""
                    INSERT INTO categoria_bebidas (nombre_categoria, descripcion)
                    VALUES (:nombre, :descripcion);
                """), 
                {'nombre': nombre, 'descripcion': descripcion}
            )
            db.session.commit()
        except Exception as e:
            flash('Error al agregar la categoria', 'error')
            return redirect(url_for('categorias.index'))
        finally:
            db.session.close()
        flash('Categoria agregada correctamente', 'success')
        return redirect(url_for('categorias.index'))
    return render_template('categorias/add.html')


@categorias_bp.route('/update_categoria/<int:id>', methods=['GET', 'POST'])
def update_categoria(id):
    if request.method == 'POST':
        nombre = request.form['nombre_categoria']
        descripcion = request.form['descripcion_categoria']
        
        try:
            result = db.session.execute(
                text("""
                    UPDATE categoria_bebidas
                    SET nombre_categoria = :nombre, descripcion = :descripcion
                    WHERE id_categoria = :id;
                """), 
                {'nombre': nombre, 'descripcion': descripcion, 'id': id}
            )
            db.session.commit()
        except Exception as e:
            flash('Error al actualizar la categoria', 'error')
            return redirect(url_for('categorias.index'))
        finally:
            db.session.close()
        flash('Categoria actualizada correctamente', 'success')
        return redirect(url_for('categorias.index'))
    try:
        result = db.session.execute(
            text("""
                SELECT * FROM categoria_bebidas
                WHERE id_categoria = :id;
            """), 
            {'id': id}
        )
        categoria = result.fetchone()
    except Exception as e:
        flash('Error al obtener la categoria', 'error')
        return redirect(url_for('categorias.index'))
    finally:
        db.session.close()
    return render_template('categorias/edit.html', categoria=categoria)

@categorias_bp.route('/delete_categoria/<int:id>')
def delete_categoria(id):
    try:
        result = db.session.execute(
            text("""
                DELETE FROM categoria_bebidas
                WHERE id_categoria = :id;
            """), 
            {'id': id}
        )
        db.session.commit()
    except Exception as e:
        flash('Error al eliminar la categoria', 'error')
        return redirect(url_for('categorias.index'))
    finally:
        db.session.close()
    flash('Categoria eliminada correctamente', 'success')
    return redirect(url_for('categorias.index'))