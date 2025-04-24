import os
from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from src.database.db_mysql import db

mesasyboxes_bp = Blueprint('mesasyboxes', __name__)

# Modelo para la tabla productos
class Producto(db.Model):
    __tablename__ = 'productos'
    id_producto = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(50), nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.String(255), nullable=True)
    precio_regular = db.Column(db.Float, nullable=False)
    promocion = db.Column(db.Boolean, default=False)

# Modelo para la tabla espacios
class Espacio(db.Model):
    __tablename__ = 'espacios'
    id_producto = db.Column(db.Integer, db.ForeignKey('productos.id_producto'), primary_key=True)
    capacidad = db.Column(db.Integer, nullable=False)
    tamanio = db.Column(db.String(50), nullable=True)
    contenido = db.Column(db.String(255), nullable=True)
    estado = db.Column(db.String(50), nullable=False)
    ubicacion = db.Column(db.String(255), nullable=True)
    reserva = db.Column(db.Float, nullable=False)

@mesasyboxes_bp.route('/', methods=['GET'])
def obtener_mesasyboxes():
    """Obtiene todos los productos y sus espacios y los muestra en una plantilla HTML."""
    productos = Producto.query.all()
    resultado = []
    for producto in productos:
        espacio = Espacio.query.filter_by(id_producto=producto.id_producto).first()
        resultado.append({
            'id_producto': producto.id_producto,
            'tipo': producto.tipo,
            'nombre': producto.nombre,
            'descripcion': producto.descripcion,
            'precio_regular': producto.precio_regular,
            'promocion': producto.promocion,
            'capacidad': espacio.capacidad if espacio else None,
            'tamanio': espacio.tamanio if espacio else None,
            'contenido': espacio.contenido if espacio else None,
            'estado': espacio.estado if espacio else None,
            'ubicacion': espacio.ubicacion if espacio else None,
            'reserva': espacio.reserva if espacio else None
        })
    print(resultado)  # 🔴 Agrega esto para verificar en consola si hay datos
    return render_template('index.html', productos=resultado)


@mesasyboxes_bp.route('/form_add_mesasyboxes', methods=['GET'])
def agregar_mesasyboxes_form():
    return render_template('Agregar_Box.html')

@mesasyboxes_bp.route('/add_mesasyboxes', methods=['POST'])
def agregar_mesasyboxes():
    if request.method == 'POST':
        # Obtener datos del formulario
        tipo = request.form['tipo']
        nombre = request.form['nombre']
        descripcion = request.form.get('descripcion', None)  
        precio_regular = float(request.form['precio_regular'])
        promocion = 'promocion' in request.form
        reserva = float(request.form.get('reserva', 0.00))

        # Crear el producto
        nuevo_producto = Producto(
            tipo=tipo,
            nombre=nombre,
            descripcion=descripcion,
            precio_regular=precio_regular,
            promocion=promocion
        )
        db.session.add(nuevo_producto)
        db.session.commit()

        # Obtener el id del producto insertado
        id_producto = nuevo_producto.id_producto

        # Si es un tipo con espacio, agregar datos en la tabla Espacio
        if tipo in ['box', 'mesa']:
            capacidad = request.form['capacidad']
            tamanio = request.form.get('tamanio', None)  
            contenido = request.form.get('contenido', None)
            estado = request.form['estado']

            nuevo_espacio = Espacio(
                id_producto=id_producto,
                capacidad=capacidad,
                tamanio=tamanio,
                contenido=contenido,
                estado=estado,
                reserva=reserva
            )
            db.session.add(nuevo_espacio)
            db.session.commit()

        flash("Producto y espacio agregados exitosamente.", "success")
        return redirect(url_for('mesasyboxes.obtener_mesasyboxes'))

@mesasyboxes_bp.route('/editar/<int:id_producto>', methods=['GET'])
def editar_mesasybox(id_producto):
    """Carga la página de edición con los datos del producto y su espacio."""
    producto = Producto.query.get(id_producto)
    if producto is None:
        return "Producto no encontrado", 404

    espacio = Espacio.query.filter_by(id_producto=id_producto).first()

    print("Producto:", producto)
    print("Espacio:", espacio)  # Verificar si el espacio se obtiene

    return render_template('Actualizar_Box.html', producto=producto, espacio=espacio)


@mesasyboxes_bp.route('/<int:id_producto>', methods=['GET'])
def obtener_mesasybox(id_producto):
    """Obtiene un producto y su espacio específico por su ID."""
    producto = Producto.query.get(id_producto)
    if producto is None:
        return jsonify({"error": "Producto no encontrado."}), 404

    espacio = Espacio.query.filter_by(id_producto=id_producto).first()
    resultado = {
        'id_producto': producto.id_producto,
        'tipo': producto.tipo,
        'nombre': producto.nombre,
        'descripcion': producto.descripcion,
        'precio_regular': producto.precio_regular,
        'promocion': producto.promocion,
        'capacidad': espacio.capacidad if espacio else None,
        'tamanio': espacio.tamanio if espacio else None,
        'contenido': espacio.contenido if espacio else None,
        'estado': espacio.estado if espacio else None,
        'ubicacion': espacio.ubicacion if espacio else None,
        'reserva': espacio.reserva if espacio else None
    }
    return jsonify(resultado), 200


@mesasyboxes_bp.route('/editar/<int:id_producto>', methods=['POST'])
def actualizar_mesasybox(id_producto):
    """Actualiza el producto y su espacio."""
    if request.form.get('_method') == 'PUT':
        try:
            # Obtener datos del formulario
            data = request.form

            # Buscar el producto y su espacio
            producto = Producto.query.get_or_404(id_producto)
            espacio = Espacio.query.filter_by(id_producto=id_producto).first()

            # Actualizar campos del producto
            producto.tipo = data.get('tipo', producto.tipo)
            producto.nombre = data.get('nombre', producto.nombre)
            producto.descripcion = data.get('descripcion', producto.descripcion)
            producto.precio_regular = float(data.get('precio_regular', producto.precio_regular))
            producto.promocion = 'promocion' in data  # Checkbox

            # Actualizar campos del espacio (si existe)
            if espacio:
                espacio.capacidad = int(data.get('capacidad', espacio.capacidad))
                espacio.tamanio = data.get('tamanio', espacio.tamanio)
                espacio.contenido = data.get('contenido', espacio.contenido)
                espacio.estado = data.get('estado', espacio.estado)

                # Manejar reserva
                if 'reserva' in data:  # Checkbox marcado
                    reserva_precio = data.get('reserva_precio', '0')
                    try:
                        espacio.reserva = float(reserva_precio) if reserva_precio else None
                    except ValueError:
                        flash("El precio de reserva debe ser un número válido", "error")
                        return redirect(url_for('mesasyboxes.obtener_mesasyboxes'))
                else:  # Checkbox desmarcado
                    espacio.reserva = None  # Guardar como NULL (N/A)

            # Guardar cambios en la base de datos
            db.session.commit()
            flash("Producto actualizado correctamente", "success")
            return redirect(url_for('mesasyboxes.obtener_mesasyboxes'))

        except Exception as e:
            db.session.rollback()
            flash(f"Error al actualizar: {str(e)}", "error")
            return redirect(url_for('mesasyboxes.obtener_mesasyboxes'))


@mesasyboxes_bp.route('/eliminar/<int:id_producto>', methods=['POST'])
def eliminar_mesasybox(id_producto):
    if request.json.get('_method') == 'DELETE':
        try:
            producto = Producto.query.get_or_404(id_producto)
            espacio = Espacio.query.filter_by(id_producto=id_producto).first()

            if espacio:
                db.session.delete(espacio)
            db.session.delete(producto)
            
            db.session.commit()
            return jsonify(success=True), 200

        except Exception as e:
            db.session.rollback()
            print(f"Error en la base de datos: {str(e)}")
            return jsonify(success=False, error=str(e)), 500
        


@mesasyboxes_bp.route('/filtrar/<tipo>', methods=['GET'])
def filtrar_por_tipo(tipo):
    """Filtra los productos por tipo (box o mesa)."""
    productos_filtrados = Producto.query.filter_by(tipo=tipo).all()
    resultado = []

    for producto in productos_filtrados:
        espacio = Espacio.query.filter_by(id_producto=producto.id_producto).first()
        resultado.append({
            'id_producto': producto.id_producto,
            'tipo': producto.tipo,
            'nombre': producto.nombre,
            'descripcion': producto.descripcion,
            'precio_regular': producto.precio_regular,
            'promocion': producto.promocion,
            'capacidad': espacio.capacidad if espacio else None,
            'tamanio': espacio.tamanio if espacio else None,
            'contenido': espacio.contenido if espacio else None,
            'estado': espacio.estado if espacio else None,
            'ubicacion': espacio.ubicacion if espacio else None,
            'reserva': espacio.reserva if espacio else None
        })

    return render_template('index.html', productos=resultado, tipo_filtro=tipo)


