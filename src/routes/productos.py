from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from src.database.db_mysql import db
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.DEBUG)

productos_bp = Blueprint("productos", __name__)

@productos_bp.route('/get_all_products')
def index():
    try:
        result = db.session.execute(
            text("""
                SELECT p.id_producto, p.tipo, p.nombre, p.descripcion, p.precio_regular, p.promocion, 
                    pc.tamanio, pc.insumos, pc.stock
                FROM productos p
                LEFT JOIN piqueos_cocteles pc ON p.id_producto = pc.id_producto
                WHERE p.tipo IN ('piqueo', 'coctel');
            """)
        )
        productos = result.fetchall()
    except Exception as e:
        logging.error(e)
        flash('Error al obtener los productos', 'error')
        return redirect(url_for('home.index'))
    finally:
        db.session.close()
    return render_template('productos/index.html', productos=productos)

@productos_bp.route('/add', methods=['GET', 'POST'])
def add_producto():
    if request.method == 'POST':
        tipo = request.form['tipo']
        nombre = request.form['nombre']
        descripcion = request.form['descripcion']
        precio_regular = request.form['precio_regular']
        promocion = request.form.get('promocion', 0)
        tamanio = request.form['tamanio']
        insumos = request.form['insumos']
        stock = request.form['stock']
        
        logging.debug(f"Adding producto with data: tipo={tipo}, nombre={nombre}, descripcion={descripcion}, precio_regular={precio_regular}, promocion={promocion}, tamanio={tamanio}, insumos={insumos}, stock={stock}")
        
        try:
            result = db.session.execute(
                text("""
                    INSERT INTO productos (tipo, nombre, descripcion, precio_regular, promocion)
                    VALUES (:tipo, :nombre, :descripcion, :precio_regular, :promocion);
                """), 
                {'tipo': tipo, 'nombre': nombre, 'descripcion': descripcion, 'precio_regular': precio_regular, 'promocion': promocion}
            )
            db.session.commit()
            id_producto = result.lastrowid
            db.session.execute(
                text("""
                    INSERT INTO piqueos_cocteles (id_producto, tamanio, insumos, stock)
                    VALUES (:id_producto, :tamanio, :insumos, :stock);
                """), 
                {'id_producto': id_producto, 'tamanio': tamanio, 'insumos': insumos, 'stock': stock}
            )
            db.session.commit()
            flash('Producto agregado correctamente', 'success')
            return redirect(url_for('productos.index'))
        except Exception as e:
            logging.error(e)
            flash('Error al agregar el producto', 'error')
            return redirect(url_for('productos.index'))
        finally:
            db.session.close()
    return render_template('productos/add.html')

@productos_bp.route('/update/<int:id>', methods=['GET', 'POST'])
def update_producto(id):
    try:
        result = db.session.execute(
            text("""
                SELECT p.id_producto, p.tipo, p.nombre, p.descripcion, p.precio_regular, p.promocion, 
                    pc.tamanio, pc.insumos, pc.stock
                FROM productos p
                LEFT JOIN piqueos_cocteles pc ON p.id_producto = pc.id_producto
                WHERE p.id_producto = :id;
            """), 
            {'id': id}
        )
        producto = result.fetchone()
    except Exception as e:
        logging.error(e)
        flash('Error al obtener el producto', 'error')
        return redirect(url_for('productos.index'))
    finally:
        db.session.close()
        
    if request.method == 'POST':
        tipo = request.form['tipo']
        nombre = request.form['nombre']
        descripcion = request.form['descripcion']
        precio_regular = request.form['precio_regular']
        promocion = request.form['promocion']
        tamanio = request.form['tamanio']
        insumos = request.form['insumos']
        stock = request.form['stock']
        
        logging.debug(f"Updating producto id={id} with data: tipo={tipo}, nombre={nombre}, descripcion={descripcion}, precio_regular={precio_regular}, promocion={promocion}, tamanio={tamanio}, insumos={insumos}, stock={stock}")
        
        try:
            db.session.execute(
                text("""
                    UPDATE productos
                    SET tipo = :tipo, nombre = :nombre, descripcion = :descripcion, 
                        precio_regular = :precio_regular, promocion = :promocion
                    WHERE id_producto = :id;
                """), 
                {'id': id, 'tipo': tipo, 'nombre': nombre, 'descripcion': descripcion, 'precio_regular': precio_regular, 'promocion': promocion}
            )
            db.session.commit()
            db.session.execute(
                text("""
                    UPDATE piqueos_cocteles
                    SET tamanio = :tamanio, insumos = :insumos, stock = :stock
                    WHERE id_producto = :id;
                """), 
                {'id': id, 'tamanio': tamanio, 'insumos': insumos, 'stock': stock}
            )
            db.session.commit()
            flash('Producto actualizado correctamente', 'success')
            return redirect(url_for('productos.index'))
        except Exception as e:
            logging.error(e)
            flash('Error al actualizar el producto', 'error')
            return redirect(url_for('productos.index'))
        finally:
            db.session.close()
    return render_template('productos/edit.html', producto=producto)

@productos_bp.route('/delete/<int:id>')
def delete_producto(id):
    try:
        db.session.execute(
            text("""
                DELETE FROM piqueos_cocteles
                WHERE id_producto = :id;
            """), 
            {'id': id}
        )
        db.session.commit()
        db.session.execute(
            text("""
                DELETE FROM productos
                WHERE id_producto = :id;
            """), 
            {'id': id}
        )
        db.session.commit()
        flash('Producto eliminado correctamente', 'success')
    except Exception as e:
        logging.error(e)
        flash('Error al eliminar el producto', 'error')
    finally:
        db.session.close()
    return redirect(url_for('productos.index'))
