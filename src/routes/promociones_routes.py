# src/routes/promociones_routes.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from src.models.promocion import Promocion
from src.models.producto import Producto # Para obtener los productos para el combo
from src.database.db_mysql import db
from decimal import Decimal # Para manejar los precios
from datetime import datetime # Para manejar las fechas

promociones_bp = Blueprint('promociones', __name__, url_prefix='/promociones')

@promociones_bp.route('/')
def listar_promociones():
    """
    Muestra la tabla de todas las promociones.
    """
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 10 # O el número de ítems que quieras por página
        # Query para obtener promociones con el nombre del producto asociado
        lista_promociones = db.session.query(
                Promocion,
                Producto.nombre.label('nombre_producto')
            ).join(Producto, Promocion.id_producto == Producto.id_producto)\
            .paginate(page=page, per_page=per_page, error_out=False)

    except Exception as e:
        print(f"Error al obtener promociones: {e}")
        flash('Error al cargar las promociones.', 'danger')
        lista_promociones = None
    return render_template('promociones/Promociones_Tabla.html', promociones_paginadas=lista_promociones)

@promociones_bp.route('/agregar', methods=['GET', 'POST'])
def agregar_promocion():
    """
    Muestra el formulario para agregar una nueva promoción y maneja su envío.
    """
    if request.method == 'POST':
        try:
            # Recoger datos del formulario
            id_producto = request.form.get('id_producto')
            nombre_promocion = request.form.get('nombre')
            descripcion = request.form.get('descripcion')
            precio_regular_str = request.form.get('precio_regular')
            porcentaje_descuento_str = request.form.get('porcentaje_descuento')
            cantidad_minima_str = request.form.get('cantidad_minima')
            precio_final_str = request.form.get('precio_final')
            fecha_inicio_str = request.form.get('inicio') # Corregido para coincidir con el name del input
            fecha_fin_str = request.form.get('fin')       # Corregido para coincidir con el name del input

            # Validaciones básicas (puedes expandirlas)
            if not all([id_producto, nombre_promocion, precio_regular_str, porcentaje_descuento_str, cantidad_minima_str, precio_final_str, fecha_inicio_str, fecha_fin_str]):
                flash('Todos los campos marcados con * son obligatorios.', 'warning')
                # Volver a cargar productos para el formulario
                productos_elegibles = Producto.query.filter_by(promocion=True).order_by(Producto.nombre).all()
                return render_template('promociones/Agregar_Promocion.html', productos=productos_elegibles, form_data=request.form)


            # Conversión de datos
            precio_regular = Decimal(precio_regular_str)
            porcentaje_descuento = Decimal(porcentaje_descuento_str)
            cantidad_minima = int(cantidad_minima_str)
            precio_final = Decimal(precio_final_str)
            # Convertir string de fecha (YYYY-MM-DD) a objeto date
            inicio = datetime.strptime(fecha_inicio_str, '%Y-%m-%d').date()
            fin = datetime.strptime(fecha_fin_str, '%Y-%m-%d').date()


            # Crear nueva promoción
            nueva_promocion = Promocion(
                id_producto=int(id_producto),
                nombre=nombre_promocion,
                descripcion=descripcion,
                precio_regular=precio_regular,
                porcentaje_descuento=porcentaje_descuento,
                cantidad_minima=cantidad_minima,
                precio_final=precio_final,
                inicio=inicio,
                fin=fin
            )

            db.session.add(nueva_promocion)
            db.session.commit()
            flash('Promoción agregada exitosamente!', 'success')
            return redirect(url_for('promociones.listar_promociones'))

        except ValueError as ve:
            flash(f'Error en la conversión de datos: {ve}. Por favor, verifica los formatos.', 'danger')
            # Volver a cargar productos para el formulario
            productos_elegibles = Producto.query.filter_by(promocion=True).order_by(Producto.nombre).all()
            return render_template('promociones/Agregar_Promocion.html', productos=productos_elegibles, form_data=request.form)
        except Exception as e:
            db.session.rollback()
            flash(f'Error al agregar la promoción: {e}', 'danger')
            # Volver a cargar productos para el formulario
            productos_elegibles = Producto.query.filter_by(promocion=True).order_by(Producto.nombre).all()
            return render_template('promociones/Agregar_Promocion.html', productos=productos_elegibles, form_data=request.form)


    # Método GET: Mostrar el formulario
    # Obtener productos cuya columna 'promocion' sea True (o 1)
    productos_elegibles = Producto.query.filter_by(promocion=True).order_by(Producto.nombre).all()
    return render_template('promociones/Agregar_Promocion.html', productos=productos_elegibles)

# Aquí podrías agregar rutas para editar y eliminar promociones en el futuro

@promociones_bp.route('/editar/<int:id_promocion>', methods=['GET', 'POST'])
def editar_promocion(id_promocion):
    """
    Muestra el formulario para editar una promoción existente y maneja su actualización.
    """
    promocion_a_editar = Promocion.query.get_or_404(id_promocion)
    form_data_edit = {} # Para repoblar en caso de error

    if request.method == 'POST':
        try:
            form_data_edit = request.form.to_dict()
            promocion_a_editar.id_producto = int(request.form.get('id_producto'))
            promocion_a_editar.nombre = request.form.get('nombre')
            promocion_a_editar.descripcion = request.form.get('descripcion')
            promocion_a_editar.precio_regular = Decimal(request.form.get('precio_regular'))
            promocion_a_editar.porcentaje_descuento = Decimal(request.form.get('porcentaje_descuento'))
            promocion_a_editar.cantidad_minima = int(request.form.get('cantidad_minima'))
            promocion_a_editar.precio_final = Decimal(request.form.get('precio_final'))
            
            fecha_inicio_str = request.form.get('inicio')
            fecha_fin_str = request.form.get('fin')

            if not all([promocion_a_editar.id_producto, promocion_a_editar.nombre, fecha_inicio_str, fecha_fin_str,
                        request.form.get('precio_regular'), request.form.get('porcentaje_descuento'),
                        request.form.get('cantidad_minima'), request.form.get('precio_final')]):
                flash('Todos los campos marcados con * son obligatorios.', 'warning')
                productos_elegibles = Producto.query.filter_by(promocion=True).order_by(Producto.nombre).all()
                # Pasamos la promoción original para los values, pero los datos del form para repoblar si hay error
                return render_template('promociones/Actualizar_promociones.html', promocion=promocion_a_editar, productos=productos_elegibles, form_data=form_data_edit)

            promocion_a_editar.inicio = datetime.strptime(fecha_inicio_str, '%Y-%m-%d').date()
            promocion_a_editar.fin = datetime.strptime(fecha_fin_str, '%Y-%m-%d').date()

            if promocion_a_editar.fin < promocion_a_editar.inicio:
                flash('La fecha de fin no puede ser anterior a la fecha de inicio.', 'warning')
                productos_elegibles = Producto.query.filter_by(promocion=True).order_by(Producto.nombre).all()
                return render_template('promociones/Actualizar_promociones.html', promocion=promocion_a_editar, productos=productos_elegibles, form_data=form_data_edit)

            db.session.commit()
            flash('Promoción actualizada exitosamente!', 'success')
            return redirect(url_for('promociones.listar_promociones'))

        except ValueError as ve:
            flash(f'Error en la conversión de datos: {ve}. Por favor, verifica los formatos.', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar la promoción: {e}', 'danger')
        
        productos_elegibles = Producto.query.filter_by(promocion=True).order_by(Producto.nombre).all()
        return render_template('promociones/Actualizar_promociones.html', promocion=promocion_a_editar, productos=productos_elegibles, form_data=form_data_edit)

    # Método GET: Mostrar el formulario con los datos de la promoción
    # `form_data` aquí se usa para pasar los datos actuales de la promoción al template para rellenar el form
    # Convertimos el objeto promocion_a_editar a un diccionario compatible con lo que espera el template
    form_data_get = {
        'id_producto': promocion_a_editar.id_producto,
        'nombre': promocion_a_editar.nombre,
        'descripcion': promocion_a_editar.descripcion,
        'precio_regular': str(promocion_a_editar.precio_regular), # Convertir Decimal a string
        'porcentaje_descuento': str(promocion_a_editar.porcentaje_descuento),
        'cantidad_minima': promocion_a_editar.cantidad_minima,
        'precio_final': str(promocion_a_editar.precio_final),
        'inicio': promocion_a_editar.inicio.strftime('%Y-%m-%d') if promocion_a_editar.inicio else '',
        'fin': promocion_a_editar.fin.strftime('%Y-%m-%d') if promocion_a_editar.fin else ''
    }
    productos_elegibles = Producto.query.filter_by(promocion=True).order_by(Producto.nombre).all()
    return render_template('promociones/Actualizar_promociones.html', promocion=promocion_a_editar, productos=productos_elegibles, form_data=form_data_get)


@promociones_bp.route('/eliminar/<int:id_promocion>', methods=['POST'])
def eliminar_promocion(id_promocion):
    """
    Elimina una promoción específica.
    """
    try:
        promocion_a_eliminar = Promocion.query.get_or_404(id_promocion)
        db.session.delete(promocion_a_eliminar)
        db.session.commit()
        flash('Promoción eliminada exitosamente!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar la promoción: {e}', 'danger')
    return redirect(url_for('promociones.listar_promociones'))