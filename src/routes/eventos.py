# src/routes/eventos.py
import datetime
import json
from flask import Blueprint, json, render_template, request, flash, redirect, url_for, jsonify
from datetime import datetime, date,time  # Agregar importación correcta
from src.database.db_mysql import db
from src.models.evento import Evento, artistas_evento
from src.models.artistas import Artista
from src.utils.security import is_safe_url
from urllib.parse import urlencode
from src.models.red_social import RedSocial, DetalleRedSocial

eventos_bp = Blueprint('eventos', __name__)

@eventos_bp.route('/eventos')
def eventos_tabla():
    eventos = Evento.query.all()  # Usando SQLAlchemy
    return render_template('Eventos_Tabla.html', eventos=eventos)




#Nuevas Rutas:

@eventos_bp.route('/agregar_evento', methods=['GET', 'POST'])
def agregar_evento():
    if request.method == 'POST':
        try:
            # Validación de campos básicos
            required_fields = ['nombre', 'descripcion', 'direccion', 'fecha', 'hora', 'artistas']
            if not all(field in request.form and request.form[field].strip() for field in required_fields):
                flash('Todos los campos son requeridos', 'danger')
                return redirect(url_for('eventos.agregar_evento'))

            # Procesar artistas seleccionados
            artistas_data = request.form['artistas']
            artistas_ids = json.loads(artistas_data) if artistas_data else []

            if not isinstance(artistas_ids, list) or len(artistas_ids) == 0:
                flash('Debe seleccionar al menos un artista', 'warning')
                return redirect(url_for('eventos.agregar_evento'))

            # Convertir fecha y hora
            fecha = datetime.strptime(request.form['fecha'], '%Y-%m-%d').date()
            hora = datetime.strptime(request.form['hora'], '%H:%M').time()

            # Crear el evento
            nuevo_evento = Evento(
                nombre_evento=request.form['nombre'],
                descripcion=request.form['descripcion'],
                lugar=request.form['direccion'],
                fecha=fecha,
                hora=hora,
                id_discoteca=1
            )

            # Asociar artistas al evento
            artistas = Artista.query.filter(Artista.id_artista.in_(artistas_ids)).all()
            nuevo_evento.artistas = artistas

            # Guardar en la base de datos
            db.session.add(nuevo_evento)
            db.session.commit()

            flash('Evento creado exitosamente', 'success')
            return redirect(url_for('eventos.eventos_tabla'))

        except json.JSONDecodeError:
            flash('Error en el formato de datos de los artistas', 'danger')
        except ValueError as e:
            flash(f'Error en formato de fecha/hora: {str(e)}', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear evento: {str(e)}', 'danger')

        return redirect(url_for('eventos.agregar_evento'))

    # GET: Mostrar formulario
    try:
        artistas = Artista.query.order_by(Artista.nombre).all()
        return render_template('Agregar_evento.html', artistas=artistas, min_date=datetime.now().strftime('%Y-%m-%d'))
    except Exception as e:
        flash(f'Error al cargar formulario: {str(e)}', 'danger')
        return redirect(url_for('eventos.eventos_tabla'))




#editar event:

@eventos_bp.route('/editar_evento/<string:nombre_evento>', methods=['GET', 'POST'])
def editar_evento(nombre_evento):
    try:
        evento = Evento.query.filter_by(nombre_evento=nombre_evento).first_or_404()
        
        if request.method == 'POST':
            # Actualizar datos básicos
            evento.nombre_evento = request.form['nombre']
            evento.descripcion = request.form['descripcion']
            evento.lugar = request.form['direccion']
            evento.fecha = datetime.strptime(request.form['fecha'], '%Y-%m-%d').date()
            evento.hora = datetime.strptime(request.form['hora'], '%H:%M').time()
            
            # Validar y actualizar artistas
            try:
                nuevos_artistas_ids = [int(id) for id in json.loads(request.form.get('artistas', '[]'))]
            except (json.JSONDecodeError, ValueError) as e:
                nuevos_artistas_ids = []
                flash('Formato inválido en la lista de artistas', 'danger')

            # Filtrar solo IDs válidos y asegurar que sean únicos
            artistas_validos = Artista.query.filter(
                Artista.id_artista.in_(nuevos_artistas_ids)
            ).all()
            
            # Verificar si todos los IDs existen
            if len(artistas_validos) != len(set(nuevos_artistas_ids)):
                ids_faltantes = set(nuevos_artistas_ids) - {a.id_artista for a in artistas_validos}
                flash(f'Se eliminaron artistas no válidos: IDs {ids_faltantes}', 'warning')
            
            # Actualizar relación many-to-many
            evento.artistas = artistas_validos
            
            db.session.commit()
            flash('Evento actualizado correctamente', 'success')
            
            # Redirección segura
            next_page = request.form.get('next')
            if next_page and is_safe_url(next_page):
                return redirect(next_page)
            return redirect(url_for('eventos.eventos_tabla'))

        # GET: Mostrar formulario
        artistas = Artista.query.order_by(Artista.nombre).all()
        return render_template('Actualizar_evento.html',
                            evento=evento,
                            artistas=artistas,
                            artistas_asignados=evento.artistas,
                            min_date=date.today().strftime('%Y-%m-%d'),
                            next=request.args.get('next'))

    except ValueError as e:
        db.session.rollback()
        flash(f'Error en formato de datos: {str(e)}', 'danger')
        return redirect(url_for('eventos.eventos_tabla'))
    
    except Exception as e:
        db.session.rollback()
        flash(f'Error al editar el evento: {str(e)}', 'danger')
        return redirect(url_for('eventos.eventos_tabla'))

@eventos_bp.route('/obtener_datos_artista/<int:id_artista>')
def obtener_datos_artista(id_artista):
    try:
        artista = Artista.query.get_or_404(id_artista)
        return jsonify({
            'id_artista': artista.id_artista,
            'nombre': artista.nombre,
            'genero': artista.genero_musical,
            'descripcion': artista.descripcion
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 404





# --------------------------
# RUTAS DE ARTISTAS
# --------------------------

@eventos_bp.route('/artistas', methods=['GET', 'POST'])
def artistas():
    if request.method == 'POST':
        try:
            nuevo_artista = Artista(
                nombre=request.form['nombreArtistico'],
                genero_musical=request.form['generoMusical'],
                descripcion=request.form['descripcion']
            )
            db.session.add(nuevo_artista)
            db.session.commit()
            flash('Artista registrado exitosamente', 'success')
            return redirect(request.args.get('next', url_for('eventos.agregar_evento')))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')
    
    return render_template('artistas.html')

@eventos_bp.route('/obtener_artistas')
def obtener_artistas():
    artistas = Artista.query.all()
    return jsonify([{
        'id_artista': a.id_artista,
        'nombre': a.nombre
    } for a in artistas])



#Nuevas Rutas

# Añade estas rutas al blueprint de eventos
@eventos_bp.route('/artistas/crear', methods=['GET', 'POST'])
def crear_artista():
    next_url = request.args.get('next', url_for('eventos.agregar_evento'))
    
    if request.method == 'POST':
        try:
            nuevo_artista = Artista(
                nombre=request.form['nombreArtistico'],
                genero_musical=request.form['generoMusical'],
                descripcion=request.form['descripcion']
            )
            db.session.add(nuevo_artista)
            db.session.commit()
            flash('Artista creado exitosamente', 'success')
            return redirect(next_url)
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear artista: {str(e)}', 'danger')
    
    return render_template('artistas.html', 
                        next_url=next_url,
                        form_data=request.form if request.method == 'POST' else None)

# Ruta para editar artista
@eventos_bp.route('/editar_artista/<int:id_artista>', methods=['GET', 'POST'])
def editar_artista(id_artista):
    artista = Artista.query.get_or_404(id_artista)
    next_url = request.args.get('next', url_for('eventos.eventos_tabla'))
    
    if request.method == 'POST':
        try:
            artista.nombre = request.form['nombreArtistico']
            artista.genero_musical = request.form['generoMusical']
            artista.descripcion = request.form['descripcion']
            
            db.session.commit()
            flash('Artista actualizado correctamente', 'success')
            return redirect(next_url)
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar artista: {str(e)}', 'danger')
    
    return render_template('Actualizar_artista.html',
                        artista=artista,
                        next_url=next_url)

# Ruta para obtener datos de artista (usada en los selects)
# Ruta extendida (nueva)
@eventos_bp.route('/obtener_datos_completos_artista/<int:id_artista>')
def obtener_datos_completos_artista(id_artista):  # <- Nombre único
    artista = Artista.query.get_or_404(id_artista)
    return jsonify({
        'nombre': artista.nombre,
        'genero': artista.genero_musical,
        'descripcion': artista.descripcion
    })






# --------------------------
# RUTAS DE REDES SOCIALES
# --------------------------

@eventos_bp.route('/redes_sociales/<int:id_artista>')
def redes_sociales(id_artista):
    artista = Artista.query.get_or_404(id_artista)
    return render_template('Tabla_RedSocial.html', 
                        id_artista=id_artista,
                        redes=artista.redes)  # Cambiado de 'redes_sociales' a 'redes'

@eventos_bp.route('/guardar_red_social', methods=['POST'])
def guardar_red_social():
    try:
        nueva_red = RedSocial(
            nombre_referencia=request.form['nombre_referencia'],
            id_artista=request.form['id_artista'],
            detalle=DetalleRedSocial(
                tipo_link=request.form['tipo_link'],
                url=request.form['url'],
                descripcion=request.form.get('descripcion', '')
            )
        )
        db.session.add(nueva_red)
        db.session.commit()
        flash('Red social guardada con éxito', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'danger')
    
    return redirect(url_for('eventos.redes_sociales', 
                        id_artista=request.form['id_artista']))