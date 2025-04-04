from flask import Blueprint, render_template, request, redirect, url_for, flash
from src.database.db_mysql import db
from src.models.producto import Producto
from src.models.bebida import Bebida
from src.models.categoria_bebida import CategoriaBebida

bebidas_bp = Blueprint('bebidas', __name__, url_prefix='/bebidas')

@bebidas_bp.route('/')
def listar_bebidas():
    bebidas = Bebida.query.join(Producto).all()
    categorias = CategoriaBebida.query.all()
    return render_template('Listado_bebidas.html', bebidas=bebidas, categorias=categorias)

@bebidas_bp.route('/crear', methods=['GET', 'POST'])
def crear_bebida():
    if request.method == 'POST':
        try:
            # Validar datos numéricos
            precio = float(request.form['precio'])
            tamanio = float(request.form['tamano'])
            stock = int(request.form['stock'])
            
            if precio <= 0 or tamanio <= 0 or stock < 0:
                raise ValueError("Valores numéricos deben ser positivos")

            # Crear producto
            nuevo_producto = Producto(
                tipo='bebida',
                nombre=request.form['nombre'].strip(),
                descripcion=request.form['descripcion'].strip(),
                precio_regular=precio,
                promocion=request.form.get('promocion', 'off') == 'on'
            )

            db.session.add(nuevo_producto)
            db.session.flush()  # Obtener ID sin commit

            # Crear bebida
            nueva_bebida = Bebida(
                id_producto=nuevo_producto.id_producto,
                marca=request.form['marca'].strip(),
                tamanio=tamanio,
                stock=stock,
                id_categoria=int(request.form['categoria'])
            )

            db.session.add(nueva_bebida)
            db.session.commit()
            
            flash('Bebida creada exitosamente!', 'success')
            return redirect(url_for('bebidas.listar_bebidas'))

        except ValueError as ve:
            db.session.rollback()
            flash(f'Error de validación: {str(ve)}', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear bebida: {str(e)}', 'danger')

    # GET: Mostrar formulario con categorías
    categorias = CategoriaBebida.query.order_by(CategoriaBebida.nombre_categoria).all()
    return render_template('Agregar_bebidas.html', categorias=categorias)


@bebidas_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar_bebida(id):
    bebida = Bebida.query.get_or_404(id)
    producto = Producto.query.get_or_404(id)
    categorias = CategoriaBebida.query.all()

    if request.method == 'POST':
        try:
            # Actualizar Producto
            producto.nombre = request.form['nombre']
            producto.descripcion = request.form['descripcion']
            producto.precio_regular = float(request.form['precio'])
            producto.promocion = 'promocion' in request.form

            # Actualizar Bebida
            bebida.marca = request.form['marca']
            bebida.tamanio = float(request.form['tamano'])
            bebida.stock = int(request.form['stock'])
            bebida.id_categoria = int(request.form['categoria'])

            db.session.commit()
            flash('Bebida actualizada correctamente!', 'success')
            return redirect(url_for('bebidas.listar_bebidas'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar: {str(e)}', 'danger')

    return render_template('Actualizar_bebida.html', 
                            bebida=bebida, 
                            producto=producto,
                            categorias=categorias)



@bebidas_bp.route('/eliminar/<int:id>', methods=['POST'])
def eliminar_bebida(id):
    bebida = Bebida.query.get_or_404(id)
    producto = Producto.query.get_or_404(id)
    
    try:
        db.session.delete(bebida)
        db.session.delete(producto)
        db.session.commit()
        flash('Bebida eliminada exitosamente', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar: {str(e)}', 'danger')
    
    return redirect(url_for('bebidas.listar_bebidas'))