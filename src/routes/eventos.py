# src/routes/eventos.py
import datetime
import json # Para json.loads y json.JSONDecodeError
import os # Para manejo de archivos
from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, current_app
from datetime import datetime, date, time # Asegúrate que datetime.datetime sea usado o solo datetime
from src.database.db_mysql import db
from src.models.evento import Evento # artistas_evento no se usa directamente aquí, sino a través de la relación
from src.models.artistas import Artista
# Asegúrate que estos modelos y utilidades existan y estén en la ruta correcta
from src.models.media import ImagenVideo # Modelo para imágenes/videos
from src.utils.file_handling import allowed_file, secure_filename_wrapper 
# from src.utils.security import is_safe_url # No se usa en este fragmento
# from urllib.parse import urlencode # No se usa en este fragmento
# from src.models.red_social import RedSocial, DetalleRedSocial # No se usan en este fragmento

eventos_bp = Blueprint('eventos', __name__, url_prefix='/eventos') # Añadido url_prefix para consistencia

@eventos_bp.route('/') # Ruta para listar eventos, ej: /eventos/
def eventos_tabla():
    try:
        eventos = Evento.query.all()
        # Aquí también podrías querer cargar la media asociada a cada evento para mostrarla en la tabla
        # Por ejemplo, un thumbnail por evento.
    except Exception as e:
        current_app.logger.error(f"Error al listar eventos: {str(e)}")
        flash('Error al cargar la lista de eventos.', 'danger')
        eventos = []
    return render_template('Eventos_Tabla.html', eventos=eventos)

@eventos_bp.route('/agregar', methods=['GET', 'POST']) # Cambiado a /agregar para consistencia con url_for
def agregar_evento():
    if request.method == 'POST':
        try:
            # Validación de campos básicos (nombre, descripcion, direccion, fecha, hora)
            # El campo 'artistas' se valida después de procesar JSON
            required_fields_text = ['nombre', 'descripcion', 'direccion', 'fecha', 'hora']
            if not all(field in request.form and request.form[field].strip() for field in required_fields_text):
                flash('Todos los campos de texto del evento son requeridos (nombre, descripción, etc.).', 'danger')
                # Es mejor renderizar de nuevo el template con los datos ya ingresados que solo redirigir
                # return redirect(url_for('eventos.agregar_evento')) 
                # Para renderizar de nuevo, necesitarías cargar los artistas de nuevo
                artistas_list = Artista.query.order_by(Artista.nombre).all()
                return render_template('Agregar_evento.html', artistas=artistas_list, 
                                       min_date=datetime.now().strftime('%Y-%m-%d'),
                                       form_data=request.form)


            # Procesar artistas seleccionados
            artistas_data = request.form.get('artistas') # Usar .get() para evitar KeyError si no está
            if not artistas_data:
                flash('Debe seleccionar al menos un artista.', 'warning')
                artistas_list = Artista.query.order_by(Artista.nombre).all()
                return render_template('Agregar_evento.html', artistas=artistas_list, 
                                       min_date=datetime.now().strftime('%Y-%m-%d'),
                                       form_data=request.form)
            
            artistas_ids = json.loads(artistas_data)

            if not isinstance(artistas_ids, list) or len(artistas_ids) == 0:
                flash('Debe seleccionar al menos un artista (lista vacía o formato incorrecto).', 'warning')
                artistas_list = Artista.query.order_by(Artista.nombre).all()
                return render_template('Agregar_evento.html', artistas=artistas_list, 
                                       min_date=datetime.now().strftime('%Y-%m-%d'),
                                       form_data=request.form)

            # Convertir fecha y hora
            # Usar datetime.strptime directamente ya que datetime fue importado así.
            fecha_evento = datetime.strptime(request.form['fecha'], '%Y-%m-%d').date()
            hora_evento = datetime.strptime(request.form['hora'], '%H:%M').time()

            # Crear el evento
            nuevo_evento = Evento(
                nombre_evento=request.form['nombre'].strip(),
                descripcion=request.form['descripcion'].strip(),
                lugar=request.form['direccion'].strip(),
                fecha=fecha_evento,
                hora=hora_evento,
                id_discoteca=1 # Placeholder, ajustar según tu lógica (igual que en bebidas)
            )

            # Asociar artistas al evento
            artistas_obj = Artista.query.filter(Artista.id_artista.in_(artistas_ids)).all()
            if len(artistas_obj) != len(artistas_ids):
                 flash('Alguno de los artistas seleccionados no fue encontrado.', 'warning')
                 # Continuar o detener? Por ahora continuamos.
            nuevo_evento.artistas = artistas_obj

            db.session.add(nuevo_evento)
            db.session.flush()  # Obtener ID del evento para asociar la multimedia

            # --- INICIO: Manejo de Multimedia ---
            # Asegúrate que estas configuraciones existen en tu app Flask
            # ej. app.config['UPLOAD_FOLDER'] = 'static/uploads/eventos'
            # ej. app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'mov'}
            
            # 1. Archivos subidos (imágenes para eventos)
            archivos_subidos = request.files.getlist('archivos')
            descripciones_archivos = request.form.getlist('descripciones_archivos') # Lista de descripciones para archivos

            for i, file_storage in enumerate(archivos_subidos):
                if file_storage and file_storage.filename:
                    # Define extensiones permitidas para imágenes de eventos
                    allowed_img_extensions = current_app.config.get('ALLOWED_IMAGE_EXTENSIONS', {'png', 'jpg', 'jpeg', 'gif'})
                    if allowed_file(file_storage.filename, allowed_img_extensions):
                        filename = secure_filename_wrapper(file_storage.filename)
                        # Considera un subdirectorio para eventos si UPLOAD_FOLDER es genérico
                        upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                        
                        # Crear directorio si no existe
                        os.makedirs(os.path.dirname(upload_path), exist_ok=True)
                        
                        file_storage.save(upload_path)

                        descripcion = descripciones_archivos[i] if i < len(descripciones_archivos) else request.form.get('descripcion_media', '') # Fallback a una general si falta

                        media_archivo = ImagenVideo(
                            Id_Discoteca=nuevo_evento.id_discoteca, # Usar el de nuevo_evento
                            Tipo_Tabla='eventos',
                            Id_referenciaTabla=nuevo_evento.id_evento,
                            Descripcion=descripcion,
                            Tipo_Archivo='imagen', # Asumimos que 'archivos' son imágenes
                            Archivo=filename # Guardar solo el nombre o ruta relativa desde UPLOAD_FOLDER
                        )
                        db.session.add(media_archivo)
                    else:
                        flash(f"Archivo '{file_storage.filename}' tiene una extensión no permitida para imágenes.", 'warning')
            
            # 2. URLs de Video
            urls_video_list = request.form.getlist('urls_video') # Lista de URLs
            descripciones_urls = request.form.getlist('descripciones_urls') # Lista de descripciones para URLs

            for i, video_url_str in enumerate(urls_video_list):
                if video_url_str.strip(): # Asegurar que la URL no esté vacía
                    descripcion = descripciones_urls[i] if i < len(descripciones_urls) else request.form.get('descripcion_media', '') # Fallback

                    media_url = ImagenVideo(
                        Id_Discoteca=nuevo_evento.id_discoteca, # Usar el de nuevo_evento
                        Tipo_Tabla='eventos',
                        Id_referenciaTabla=nuevo_evento.id_evento,
                        Descripcion=descripcion,
                        Tipo_Archivo='video',
                        Archivo=video_url_str.strip() # Guardar la URL completa
                    )
                    db.session.add(media_url)
            # --- FIN: Manejo de Multimedia ---

            db.session.commit()
            flash('Evento creado exitosamente con multimedia!', 'success')
            return redirect(url_for('eventos.eventos_tabla'))

        except json.JSONDecodeError:
            db.session.rollback()
            flash('Error en el formato de datos de los artistas seleccionados (JSON).', 'danger')
        except ValueError as ve: # ej. error en strptime
            db.session.rollback()
            flash(f'Error en el formato de los datos ingresados (ej. fecha/hora): {str(ve)}', 'danger')
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error al crear evento: {str(e)}")
            flash(f'Ocurrió un error inesperado al crear el evento: {str(e)}', 'danger')
        
        # Si hubo error, recargar formulario con datos previos si es posible
        artistas_list = Artista.query.order_by(Artista.nombre).all()
        return render_template('Agregar_evento.html', artistas=artistas_list, 
                                min_date=datetime.now().strftime('%Y-%m-%d'),
                                form_data=request.form) # Re-enviar datos del form

    # GET: Mostrar formulario
    try:
        artistas = Artista.query.order_by(Artista.nombre).all()
        min_date_str = datetime.now().strftime('%Y-%m-%d')
        return render_template('Agregar_evento.html', artistas=artistas, min_date=min_date_str)
    except Exception as e:
        current_app.logger.error(f"Error al cargar formulario de agregar evento: {str(e)}")
        flash('Error al cargar el formulario para agregar evento.', 'danger')
        return redirect(url_for('eventos.eventos_tabla')) # Redirigir a la tabla si falla la carga




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