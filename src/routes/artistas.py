from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from src.models.artistas import Artista
from src.utils.security import is_safe_url  # Nueva importación
from src.database.db_mysql import db
from src.models.evento import artistas_evento  # Importar tabla de asociación si es necesario
from urllib.parse import unquote


# Configurar Blueprint
artistas_bp = Blueprint('artistas', __name__, url_prefix='/artistas')

@artistas_bp.route('/')
def artistas():
    # Obtener todos los artistas con paginación
    page = request.args.get('page', 1, type=int)
    per_page = 10
    artistas = Artista.query.order_by(Artista.nombre.asc()).paginate(page=page, per_page=per_page)
    return render_template('Tabla_Artistas.html', artistas=artistas)

@artistas_bp.route('/crear', methods=['GET', 'POST'])
def crear_artista():
    if request.method == 'POST':
        try:
            nuevo_artista = Artista(
                nombre=request.form['nombre'],
                genero_musical=request.form['genero_musical'],
                descripcion=request.form['descripcion']
            )
            db.session.add(nuevo_artista)
            db.session.commit()
            flash('Artista creado exitosamente', 'success')
            return redirect(url_for('artistas.artistas'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear artista: {str(e)}', 'danger')
    return render_template('crear_artista.html')

@artistas_bp.route('/actualizar/<int:id_artista>', methods=['GET', 'POST'])
def actualizar_artista(id_artista):
    artista = Artista.query.get_or_404(id_artista)
    
    if request.method == 'POST':
        try:
            # Actualización de campos
            artista.nombre = request.form['nombre']
            artista.genero_musical = request.form['genero_musical']
            artista.descripcion = request.form['descripcion']
            
            db.session.commit()
            flash('Artista actualizado exitosamente', 'success')
            
            # Manejo del parámetro next
            next_page = unquote(request.form.get('next', ''))
            if not is_safe_url(next_page):
                next_page = url_for('artistas.artistas')
                
            return redirect(next_page)
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar artista: {str(e)}', 'danger')

    # GET request
    next_page = unquote(request.args.get('next', url_for('artistas.artistas')))
    
    generos = ['Cumbia', 'Pop', 'Reggaeton', 'Merengue', 'Salsa']
    return render_template('Actualizar_artista.html',
                            artista=artista,
                            generos=generos,
                            next=next_page)

@artistas_bp.route('/eliminar/<int:id_artista>', methods=['POST'])
def eliminar_artista(id_artista):
    artista = Artista.query.get_or_404(id_artista)
    try:
        db.session.delete(artista)
        db.session.commit()
        flash('Artista eliminado exitosamente', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar artista: {str(e)}', 'danger')
    return redirect(url_for('artistas.artistas'))

@artistas_bp.route('/obtener_datos_completos/<int:id_artista>')
def obtener_datos_completos_artista(id_artista):
    artista = Artista.query.get_or_404(id_artista)
    return jsonify({
        'id_artista': artista.id_artista,
        'nombre': artista.nombre,
        'genero_musical': artista.genero_musical,
        'descripcion': artista.descripcion,
        'redes_sociales': [{
            'id': red.id_red_social,
            'nombre': red.nombre,
            'url': red.url
        } for red in artista.redes_sociales]
    })

# Relación con redes sociales (si es necesario)
@artistas_bp.route('/<int:id_artista>/redes', methods=['GET'])
def redes_sociales(id_artista):
    artista = Artista.query.get_or_404(id_artista)
    return render_template('redes_sociales.html', artista=artista)