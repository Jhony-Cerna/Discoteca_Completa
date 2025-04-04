from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from src.models.promocion import Promocion
from src.models.producto import Producto
from src.database.db_mysql import db
from datetime import datetime

promociones_bp = Blueprint('promociones', __name__, url_prefix='/promociones')

@promociones_bp.route('/')
def lista_promociones():
    promociones = Promocion.query.join(Producto).order_by(Promocion.id_promocion.desc()).all()
    return render_template('Promociones_tabla.html', promocionestotales=promociones)

@promociones_bp.route('/crear', methods=['GET'])
def crear_promocion():
    productos = Producto.query.all()  # Obtener todos los objetos Producto
    return render_template('Crear_Promocion.html', productos=productos)

@promociones_bp.route('/crear', methods=['POST'])
def guardar_promocion():
    try:
        # Validar que el producto existe
        producto = Producto.query.get(request.form['id_producto'])
        if not producto:
            return "Producto no encontrado", 404

        nueva_promocion = Promocion(
            nombre=request.form['nombre'],
            descripcion=request.form['descripcion'],
            tipo_promocion=request.form['tipo_promocion'],
            stock=int(request.form['stock']),
            fecha_inicio=datetime.strptime(request.form['inicio'], '%Y-%m-%d'),
            fecha_fin=datetime.strptime(request.form['fin'], '%Y-%m-%d'),
            id_producto=request.form['id_producto']
        )

        tipo = request.form['tipo_promocion']
        if tipo == 'descuento':
            nueva_promocion.porcentaje_descuento = float(request.form['descuento']) if request.form['descuento'] else None
        elif tipo == '2x1':
            nueva_promocion.cantidad_comprar = int(request.form['cantidad_comprar'])
            nueva_promocion.cantidad_pagar = int(request.form['cantidad_pagar'])
        elif tipo == 'precio_fijo':
            nueva_promocion.precio_fijo = float(request.form['precio_fijo'])
        elif tipo == 'cantidadXprecio_fijo':
            nueva_promocion.cantidad_comprar = int(request.form['cantidad_comprar'])
            nueva_promocion.precio_fijo = float(request.form['precio_fijo'])

        db.session.add(nueva_promocion)
        db.session.commit()
        return redirect(url_for('promociones.lista_promociones'))

    except Exception as e:
        db.session.rollback()
        return f"Error: {str(e)}", 500

@promociones_bp.route('/<int:id>/eliminar')
def eliminar_promocion(id):
    promocion = Promocion.query.get_or_404(id)
    db.session.delete(promocion)
    db.session.commit()
    return redirect(url_for('promociones.lista_promociones'))