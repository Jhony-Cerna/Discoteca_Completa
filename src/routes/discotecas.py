from flask import Blueprint, render_template, request, redirect, url_for, flash
from src.database.db_mysql import db
from src.models.discoteca import Discoteca
from src.models.usuario import Usuario

discotecas_bp = Blueprint('discotecas', __name__, url_prefix='/discotecas')

@discotecas_bp.route('/')
def listar_discotecas():
    discotecas = Discoteca.query.options(
        db.joinedload(Discoteca.administrador).joinedload(Usuario.persona)
    ).all()
    
    return render_template('discotecas_Tabla.html', discotecas=discotecas)

@discotecas_bp.route('/crear', methods=['GET', 'POST'])
def crear_discoteca():
    if request.method == 'POST':
        try:
            estado_map = {
                'Pendiente': 0,
                'Aprobado': 1,
                'Rechazado': 2
            }
            
            nueva_discoteca = Discoteca(
                nombre=request.form['nombre'],
                direccion=request.form['direccion'],
                departamento=request.form['departamento'],
                provincia=request.form['provincia'],
                distrito=request.form['distrito'],
                telefono=request.form['telefono'],
                estado=estado_map[request.form['estado']],
                admin_id=int(request.form['administrador'])
            )
            
            db.session.add(nueva_discoteca)
            db.session.commit()
            flash('Discoteca creada exitosamente!', 'success')
            return redirect(url_for('discotecas.listar_discotecas'))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')
    
    administradores = Usuario.query.filter_by(rol='administrador').all()
    return render_template('Agregar_Discoteca.html', administradores=administradores)

@discotecas_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar_discoteca(id):
    discoteca = Discoteca.query.get_or_404(id)
    administradores = Usuario.query.filter_by(rol='administrador').all()
    
    if request.method == 'POST':
        try:
            estado_map = {'Pendiente': 0, 'Aprobado': 1, 'Rechazado': 2}
            
            discoteca.nombre = request.form['nombre']
            discoteca.direccion = request.form['direccion']
            discoteca.departamento = request.form['departamento']
            discoteca.provincia = request.form['provincia']
            discoteca.distrito = request.form['distrito']
            discoteca.telefono = request.form['telefono']
            discoteca.estado = estado_map[request.form['estado']]
            discoteca.admin_id = int(request.form['administrador'])
            
            db.session.commit()
            flash('Discoteca actualizada!', 'success')
            return redirect(url_for('discotecas.listar_discotecas'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')
    
    return render_template('Actualizar_Discoteca.html', 
                            discoteca=discoteca,
                            administradores=administradores)

@discotecas_bp.route('/eliminar/<int:id>', methods=['POST'])
def eliminar_discoteca(id):
    discoteca = Discoteca.query.get_or_404(id)
    try:
        db.session.delete(discoteca)
        db.session.commit()
        flash('Discoteca eliminada', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'danger')
    
    return redirect(url_for('discotecas.listar_discotecas'))