from flask import Blueprint, render_template, redirect, url_for, flash, request
from src.models.red_social import RedSocial, DetalleRedSocial
from src.database.db_mysql import db
from src.utils.security import is_safe_url

redes_bp = Blueprint('redes', __name__, url_prefix='/redes')

@redes_bp.route('/agregar/<int:id_artista>', methods=['GET', 'POST'])
def agregar_red_social(id_artista):
    if request.method == 'POST':
        try:
            # Crear red social
            nueva_red = RedSocial(
                nombre_referencia=request.form['nombre_referencia'],
                id_referencia=id_artista,
                id_discoteca=1  # Asumiendo que tienes un ID fijo para la discoteca
            )
            db.session.add(nueva_red)
            db.session.flush()  # Para obtener el ID generado
            
            # Crear detalle
            detalle = DetalleRedSocial(
                tipo_link=request.form['tipo_link'],
                descripcion=request.form['descripcion'],
                url=request.form['url'],
                id_link=nueva_red.id_link
            )
            db.session.add(detalle)
            
            db.session.commit()
            flash('Red social agregada exitosamente', 'success')
            
            next_page = request.form.get('next')
            if next_page and is_safe_url(next_page):
                return redirect(next_page)
            return redirect(url_for('artistas.actualizar_artista', id_artista=id_artista))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error al guardar: {str(e)}', 'danger')

    return render_template('Red_social.html', 
                            id_artista=id_artista,
                            next=request.args.get('next'))

@redes_bp.route('/eliminar/<int:id_red>')
def eliminar_red_social(id_red):
    try:
        red = RedSocial.query.get_or_404(id_red)
        db.session.delete(red)
        db.session.commit()
        flash('Red social eliminada', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar: {str(e)}', 'danger')
    
    return redirect(request.referrer or url_for('artistas.artistas'))