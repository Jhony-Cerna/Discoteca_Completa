import os
from flask import Blueprint, render_template, redirect, session, url_for, flash, request, jsonify, current_app
from sqlalchemy import text
from src.models.artistas import Artista
from src.models.media import ImagenVideo
from src.utils.file_handling import allowed_file, secure_filename_wrapper
from src.utils.security import is_safe_url  # Nueva importación
from src.database.db_mysql import db
from src.models.evento import artistas_evento  # Importar tabla de asociación si es necesario
from werkzeug.utils import secure_filename
from urllib.parse import unquote

def allowed_file(filename, allowed_extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def secure_filename_wrapper(filename):
    return secure_filename(filename)  # usa el de werkzeug como base

# Configurar Blueprint
artistas_bp = Blueprint('artistas', __name__, url_prefix='/artistas')

@artistas_bp.route('/')
def artistas():
    # --- INICIO MODIFICACIONES ---
    if 'user_id' not in session or session.get('user_rol') != 'Administrador':
        flash("Debes iniciar sesión como Administrador para acceder a esta página.", "warning")
        return redirect(url_for('main.auth.login'))

    id_discoteca_sesion = session.get('id_discoteca')
    if id_discoteca_sesion is None:
        flash("ID de discoteca no encontrado en sesión. Por favor, inicia sesión de nuevo.", "error")
        return redirect(url_for('main.auth.login'))
    
    current_app.logger.info(f"Admin de discoteca {id_discoteca_sesion} accediendo a la lista de artistas.")
    # --- FIN MODIFICACIONES ---

    page = request.args.get('page', 1, type=int)
    per_page = 10

    # --- INICIO MODIFICACIONES ---
    # IMPORTANTE: Si los artistas son específicos de una discoteca, debes filtrar aquí.
    # Actualmente, Artista no tiene id_discoteca. Se vinculan a través de ImagenVideo.
    # Mostrar artistas que tienen al menos una ImagenVideo asociada a id_discoteca_sesion:
    artistas_query = Artista.query.join(
        ImagenVideo, Artista.id_artista == ImagenVideo.Id_referenciaTabla
    ).filter(
        ImagenVideo.Id_Discoteca == id_discoteca_sesion,
        ImagenVideo.Tipo_Tabla == 'artistas' # Asegurar que el tipo de tabla sea correcto
    ).distinct().order_by(Artista.nombre.asc())
    
    # Si los artistas son globales y no se filtran por discoteca, pero la página es solo para admins:
    # artistas_query = Artista.query.order_by(Artista.nombre.asc())
    # En este caso, el log de arriba y las verificaciones de sesión son suficientes para el acceso.
    # Por seguridad y consistencia, es mejor filtrar si los artistas se crean "bajo" una discoteca.
    # --- FIN MODIFICACIONES ---

    artistas_paginados = artistas_query.paginate(page=page, per_page=per_page, error_out=False)
    return render_template('Tabla_Artistas.html', artistas=artistas_paginados, id_discoteca=id_discoteca_sesion)


@artistas_bp.route('/crear', methods=['GET', 'POST'])
def crear_artista():
    # --- INICIO MODIFICACIONES ---
    if 'user_id' not in session or session.get('user_rol') != 'Administrador':
        flash("Debes iniciar sesión como Administrador para crear artistas.", "warning")
        return redirect(url_for('main.auth.login'))

    id_discoteca_sesion = session.get('id_discoteca')
    if id_discoteca_sesion is None:
        flash("ID de discoteca no encontrado. No se puede crear el artista. Inicia sesión.", "error")
        return redirect(url_for('main.auth.login')) # O a la lista de artistas
    
    current_app.logger.info(f"Admin de discoteca {id_discoteca_sesion} intentando crear artista.")
    # --- FIN MODIFICACIONES ---

    form_data = {} 
    # next_url = request.args.get('next') # Ya no parece usarse consistentemente
    # if next_url and not is_safe_url(next_url, request.host_url): # Necesitarías is_safe_url
    # next_url = url_for('artistas.artistas')
    
    # Usar una variable de configuración para el nombre del template es buena idea
    template_name = current_app.config.get('ARTISTAS_FORM_TEMPLATE', 'artistas.html') # Asegúrate que este template exista

    if request.method == 'POST':
        # ... (tus bloques de depuración pueden permanecer si los necesitas) ...
        try:
            nombre_artistico = request.form.get('nombreArtistico', '').strip()
            genero_musical = request.form.get('generoMusical', '').strip()
            descripcion_artista = request.form.get('descripcion', '').strip()
            
            form_data = request.form 

            if not all([nombre_artistico, genero_musical, descripcion_artista]):
                flash('Todos los campos obligatorios del artista deben estar completos.', 'warning')
                return render_template(template_name, form_data=form_data, id_discoteca=id_discoteca_sesion) # Pasar id_discoteca

            if Artista.query.filter(Artista.nombre.ilike(nombre_artistico)).first(): # Usar ilike para case-insensitive
                flash(f'El artista "{nombre_artistico}" ya existe.', 'warning')
                return render_template(template_name, form_data=form_data, id_discoteca=id_discoteca_sesion) # Pasar id_discoteca

            nuevo_artista = Artista(
                nombre=nombre_artistico,
                genero_musical=genero_musical,
                descripcion=descripcion_artista
                # Si Artista tuviera id_discoteca, lo asignarías aquí:
                # id_discoteca = id_discoteca_sesion 
            )
            db.session.add(nuevo_artista)
            db.session.flush()

            # --- INICIO MODIFICACIONES ---
            # id_discoteca = 1  # ELIMINADO - Ya tenemos id_discoteca_sesion
            # --- FIN MODIFICACIONES ---
            
            descripcion_media_archivos = request.form.get('descripcion_media_archivos', '').strip()
            descripcion_media_urls = request.form.get('descripcion_media_urls', '').strip()

            archivos_subidos = request.files.getlist('archivos')
            allowed_img_extensions = current_app.config.get('ALLOWED_IMAGE_EXTENSIONS', {'png', 'jpg', 'jpeg', 'gif'})
            upload_folder = current_app.config.get('UPLOAD_FOLDER')

            if not upload_folder:
                current_app.logger.error("UPLOAD_FOLDER no está configurado.")
                flash('Error de configuración del servidor al guardar archivo.', 'danger')
                db.session.rollback()
                return render_template(template_name, form_data=form_data, id_discoteca=id_discoteca_sesion)

            if archivos_subidos:
                for file_storage in archivos_subidos:
                    if file_storage and file_storage.filename != '' and allowed_file(file_storage.filename, allowed_img_extensions):
                        filename = secure_filename_wrapper(file_storage.filename)
                        try:
                            file_path = os.path.join(upload_folder, filename)
                            file_storage.save(file_path)

                            media_item = ImagenVideo(
                                Id_Discoteca=id_discoteca_sesion, # <--- USANDO ID DE SESIÓN
                                Tipo_Tabla='artistas',
                                Id_referenciaTabla=nuevo_artista.id_artista,
                                Descripcion=descripcion_media_archivos or f"Imagen para {nombre_artistico}",
                                Tipo_Archivo='imagen',
                                Archivo=filename
                            )
                            db.session.add(media_item)
                        except Exception as e_file:
                            current_app.logger.error(f"Error al guardar archivo {filename}: {str(e_file)}")
                            flash(f'Error al procesar el archivo {filename}. No se guardó.', 'warning')
                            # No hacer rollback aquí necesariamente, podría continuar con otros archivos u URLs

            urls_video_str = request.form.get('urls_video', '')
            if urls_video_str:
                lista_urls_video = [url.strip() for url in urls_video_str.split(',') if url.strip()]
                for video_url in lista_urls_video:
                    # Aquí podrías añadir una validación de la URL si es necesario
                    media_item_video = ImagenVideo( # Nombre de variable diferente
                        Id_Discoteca=id_discoteca_sesion, # <--- USANDO ID DE SESIÓN
                        Tipo_Tabla='artistas',
                        Id_referenciaTabla=nuevo_artista.id_artista,
                        Descripcion=descripcion_media_urls or f"Video para {nombre_artistico}",
                        Tipo_Archivo='video_url', # Usar 'video_url' para diferenciar de archivos de video subidos
                        Archivo=video_url
                    )
                    db.session.add(media_item_video)

            db.session.commit()
            flash(f'Artista "{nombre_artistico}" creado exitosamente para la discoteca!', 'success')
            return redirect(url_for('artistas.artistas')) # Redirigir a la lista

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error al crear artista para discoteca {id_discoteca_sesion}: {str(e)}", exc_info=True)
            flash(f'Error al guardar el artista: {str(e)}', 'danger')
            form_data = request.form 

    # Para GET o si hubo error en POST
    return render_template(template_name, form_data=form_data, id_discoteca=id_discoteca_sesion) # Pasar id_discoteca

    


# --- Configuración de Logging (Ejemplo, idealmente en tu __init__.py o config) ---
# Debes configurar el logger de Flask en tu aplicación principal (app.py o create_app)
# para que estos mensajes se muestren. Por ejemplo:
#
# import logging
# from logging.handlers import RotatingFileHandler
#
# if not app.debug:
#     # En producción, puedes loguear a un archivo
#     file_handler = RotatingFileHandler('flask_app.log', maxBytes=10240, backupCount=10)
#     file_handler.setFormatter(logging.Formatter(
#         '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
#     ))
#     file_handler.setLevel(logging.INFO) # o logging.WARNING
#     app.logger.addHandler(file_handler)
#     app.logger.setLevel(logging.INFO)
# else:
#     # En desarrollo, la consola puede ser suficiente
#     logging.basicConfig(level=logging.DEBUG) # Muestra logs de INFO y DEBUG en consola
#     app.logger.setLevel(logging.DEBUG)


@artistas_bp.route('/actualizar/<int:id_artista>', methods=['GET', 'POST'])
def actualizar_artista(id_artista):
    # --- INICIO MODIFICACIONES: Autenticación y Contexto de Discoteca ---
    if 'user_id' not in session or session.get('user_rol') != 'Administrador':
        flash("Debes iniciar sesión como Administrador para acceder a esta página.", "warning")
        return redirect(url_for('main.auth.login'))

    id_discoteca_sesion = session.get('id_discoteca')
    if id_discoteca_sesion is None:
        flash("ID de discoteca no encontrado en sesión. Por favor, inicia sesión de nuevo.", "error")
        return redirect(url_for('main.auth.login'))
    
    current_app.logger.info(f"Admin de discoteca {id_discoteca_sesion} intentando actualizar artista ID: {id_artista}.")
    # --- FIN MODIFICACIONES ---

    artista = Artista.query.join(
        ImagenVideo, Artista.id_artista == ImagenVideo.Id_referenciaTabla
    ).filter(
        Artista.id_artista == id_artista,
        ImagenVideo.Id_Discoteca == id_discoteca_sesion,
        ImagenVideo.Tipo_Tabla == 'artistas'
    ).first()

    if not artista:
        original_artista = Artista.query.get(id_artista) 
        if original_artista:
            flash(f"No tiene permiso para modificar el artista '{original_artista.nombre}' o no está directamente asociado a su discoteca.", "danger")
        else:
            flash(f"Artista con ID {id_artista} no encontrado.", "error")
        return redirect(url_for('artistas.artistas'))

    generos_disponibles = ['Cumbia','Pop','Reggaeton','Merengue','Salsa','Rock','Electrónica','Bachata','Otro']

    if request.method == 'POST':
        current_app.logger.info(f"Procesando POST para actualizar artista ID: {id_artista} por discoteca {id_discoteca_sesion}")
        try:
            artista.nombre = request.form['nombre']
            artista.genero_musical = request.form['genero_musical']
            artista.descripcion = request.form['descripcion']
            
            media_ids_a_eliminar_str = request.form.get('media_a_eliminar_ids', '')
            if media_ids_a_eliminar_str:
                media_ids_a_eliminar = [int(id_str) for id_str in media_ids_a_eliminar_str.split(',') if id_str.strip().isdigit()]
                for media_id in media_ids_a_eliminar:
                    media_item_a_eliminar = ImagenVideo.query.get(media_id)
                    if media_item_a_eliminar and \
                       media_item_a_eliminar.Id_referenciaTabla == artista.id_artista and \
                       media_item_a_eliminar.Tipo_Tabla == 'artistas' and \
                       media_item_a_eliminar.Id_Discoteca == id_discoteca_sesion: 
                        
                        if media_item_a_eliminar.Tipo_Archivo == 'imagen' and media_item_a_eliminar.Archivo:
                            upload_folder = current_app.config.get('UPLOAD_FOLDER')
                            if upload_folder:
                                file_path = os.path.join(upload_folder, media_item_a_eliminar.Archivo)
                                try:
                                    if os.path.exists(file_path):
                                        os.remove(file_path)
                                        current_app.logger.info(f"Archivo físico eliminado: {file_path} por discoteca {id_discoteca_sesion}")
                                except OSError as e_rm:
                                    current_app.logger.error(f"Error eliminando archivo físico {file_path}: {e_rm}")
                        db.session.delete(media_item_a_eliminar)
                        current_app.logger.info(f"Ítem multimedia ID {media_id} eliminado de BD por discoteca {id_discoteca_sesion}.")

            descripcion_media_archivos_nuevos = request.form.get('descripcion_media_archivos_nuevos', '').strip()
            descripcion_media_urls_nuevas = request.form.get('descripcion_media_urls_nuevas', '').strip()
            archivos_nuevos_subidos = request.files.getlist('archivos_nuevos')
            
            allowed_extensions_img = current_app.config.get('ALLOWED_IMAGE_EXTENSIONS', {'png', 'jpg', 'jpeg', 'gif'})
            upload_folder_path = current_app.config.get('UPLOAD_FOLDER')

            if not upload_folder_path:
                flash('Error de configuración del servidor (UPLOAD_FOLDER no definido).', 'danger')
            else:
                if not os.path.exists(upload_folder_path):
                    try:
                        os.makedirs(upload_folder_path)
                    except OSError as e_mkdir:
                        current_app.logger.error(f"No se pudo crear UPLOAD_FOLDER '{upload_folder_path}': {e_mkdir}")
                        flash('Error crítico: no se puede crear la carpeta de subidas.', 'danger')
                
                for file_storage in archivos_nuevos_subidos:
                    if file_storage and file_storage.filename != '': 
                        if allowed_file(file_storage.filename, allowed_extensions_img):
                            filename = secure_filename_wrapper(file_storage.filename)
                            if not filename: 
                                flash(f"Nombre de archivo '{file_storage.filename}' inválido tras sanitizar. Omitido.", 'warning')
                                continue
                            try:
                                file_path_save = os.path.join(upload_folder_path, filename)
                                file_storage.save(file_path_save)
                                media_item = ImagenVideo(
                                    Id_Discoteca=id_discoteca_sesion, 
                                    Tipo_Tabla='artistas',
                                    Id_referenciaTabla=artista.id_artista,
                                    Descripcion=descripcion_media_archivos_nuevos or f"Imagen para {artista.nombre}",
                                    Tipo_Archivo='imagen', 
                                    Archivo=filename)
                                db.session.add(media_item)
                                current_app.logger.info(f"Nuevo archivo multimedia '{filename}' añadido para artista {artista.id_artista} por discoteca {id_discoteca_sesion}.")
                            except Exception as e_file_save:
                                current_app.logger.error(f"Error guardando archivo {filename} para artista {artista.id_artista}, discoteca {id_discoteca_sesion}: {e_file_save}", exc_info=True)
                                flash(f'Error procesando archivo {filename}.', 'warning')
                        else:
                            flash(f"Tipo de archivo no permitido para '{file_storage.filename}'.", 'warning')
            
            urls_video_nuevas_str = request.form.get('urls_video_nuevas', '')
            if urls_video_nuevas_str:
                urls_video_nuevas_lista = [url.strip() for url in urls_video_nuevas_str.splitlines() if url.strip()]
                for url_video in urls_video_nuevas_lista:
                    if url_video: 
                        media_item_video = ImagenVideo(
                            Id_Discoteca=id_discoteca_sesion, 
                            Tipo_Tabla='artistas',
                            Id_referenciaTabla=artista.id_artista,
                            Descripcion=descripcion_media_urls_nuevas or f"Video para {artista.nombre}",
                            Tipo_Archivo='video_url', 
                            Archivo=url_video)
                        db.session.add(media_item_video)
                        current_app.logger.info(f"Nueva URL de video añadida para artista {artista.id_artista} por discoteca {id_discoteca_sesion}.")

            db.session.commit()
            flash('Artista actualizado exitosamente!', 'success')
            
            next_page_str = request.form.get('next', '')
            next_page_redirect = unquote(next_page_str) if next_page_str else url_for('artistas.artistas') 
            
            # --- CORRECCIÓN AQUÍ ---
            if not is_safe_url(next_page_redirect): # Solo un argumento
                next_page_redirect = url_for('artistas.artistas') 
            return redirect(next_page_redirect)
            
        except Exception as e:
            db.session.rollback()
            # Aquí es donde se produce el error según tu traceback.
            # Si el error es en is_safe_url, la excepción se captura aquí.
            current_app.logger.error(f"Error al actualizar artista ID {id_artista} para discoteca {id_discoteca_sesion}: {str(e)}", exc_info=True)
            flash(f'Error al actualizar artista: {str(e)}', 'danger')

    # Para GET request o si hubo error en POST
    _next_intermediate = request.args.get('next', '') if request.method == 'GET' else request.form.get('next', '')
    _unquoted_next = unquote(_next_intermediate) if _next_intermediate else ''
    next_val_final = ''
    
    # --- CORRECCIÓN AQUÍ ---
    if _unquoted_next and is_safe_url(_unquoted_next): # Solo un argumento
        next_val_final = _unquoted_next

    media_items_db = ImagenVideo.query.filter_by(
        Tipo_Tabla='artistas', 
        Id_referenciaTabla=id_artista,
        Id_Discoteca=id_discoteca_sesion 
    ).all()
    
    media_items_preparados = []
    for item_db in media_items_db:
        display_url = None
        if item_db.Tipo_Archivo == 'imagen':
            try:
                static_uploads_path_segment = 'uploads' 
                clean_filename = os.path.basename(item_db.Archivo) if item_db.Archivo else ''
                if clean_filename:
                    filename_in_static = os.path.join(static_uploads_path_segment, clean_filename).replace('\\', '/')
                    display_url = url_for('static', filename=filename_in_static) 
                else:
                    display_url = "#error-empty-filename"
            except Exception as e_url:
                current_app.logger.error(f"Error generando URL para imagen {item_db.Archivo}: {e_url}")
                display_url = "#error-img-url"
        elif item_db.Tipo_Archivo == 'video_url': 
            display_url = item_db.Archivo 
        
        media_items_preparados.append({
            'id_imagen_video': item_db.Id_imgV, 
            'tipo_archivo': item_db.Tipo_Archivo,
            'archivo': item_db.Archivo,
            'descripcion': item_db.Descripcion,
            'display_url': display_url 
        })

    return render_template('Actualizar_artista.html',
                           artista=artista,
                           generos=generos_disponibles, 
                           media_items=media_items_preparados,
                           next=next_val_final,
                           id_discoteca=id_discoteca_sesion)


@artistas_bp.route('/eliminar/<int:id_artista>', methods=['POST'])
def eliminar_artista(id_artista):
    # --- INICIO MODIFICACIONES: Autenticación y Contexto de Discoteca ---
    if 'user_id' not in session or session.get('user_rol') != 'Administrador':
        flash("Debes iniciar sesión como Administrador para realizar esta acción.", "warning")
        return redirect(url_for('main.auth.login'))

    id_discoteca_sesion = session.get('id_discoteca')
    if id_discoteca_sesion is None:
        flash("ID de discoteca no encontrado en sesión. No se puede eliminar el artista.", "error")
        return redirect(url_for('main.auth.login'))
    
    current_app.logger.info(f"Admin de discoteca {id_discoteca_sesion} intentando eliminar artista ID: {id_artista}.")
    # --- FIN MODIFICACIONES ---

    artista = Artista.query.get_or_404(id_artista)

    # --- INICIO MODIFICACIONES: Verificación y eliminación contextualizada ---
    # Verificar que el artista está asociado a la discoteca del admin actual
    # antes de permitir la eliminación de sus ImagenVideo y potencialmente del artista.
    is_associated_with_admin_discoteca = ImagenVideo.query.filter_by(
        Id_referenciaTabla=artista.id_artista,
        Tipo_Tabla='artistas',
        Id_Discoteca=id_discoteca_sesion
    ).first()

    if not is_associated_with_admin_discoteca:
        flash(f"No tiene permiso para eliminar el artista '{artista.nombre}' o no está asociado a su discoteca.", "danger")
        return redirect(url_for('artistas.artistas'))

    try:
        # 1. Eliminar ImagenVideo asociados a este artista Y a esta discoteca
        media_a_eliminar = ImagenVideo.query.filter_by(
            Id_referenciaTabla=artista.id_artista,
            Tipo_Tabla='artistas',
            Id_Discoteca=id_discoteca_sesion
        ).all()

        upload_folder = current_app.config.get('UPLOAD_FOLDER')
        for media_item in media_a_eliminar:
            if media_item.Tipo_Archivo == 'imagen' and media_item.Archivo and upload_folder:
                file_path = os.path.join(upload_folder, media_item.Archivo)
                try:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        current_app.logger.info(f"Archivo físico eliminado: {file_path} durante eliminación de artista por discoteca {id_discoteca_sesion}")
                except OSError as e_rm:
                    current_app.logger.error(f"Error eliminando archivo físico {file_path} durante eliminación: {e_rm}")
            db.session.delete(media_item)
        
        # 2. (Opcional Avanzado) Verificar si el artista sigue asociado a OTRAS discotecas
        # otros_media = ImagenVideo.query.filter(
        # ImagenVideo.Id_referenciaTabla == artista.id_artista,
        # ImagenVideo.Tipo_Tabla == 'artistas',
        # ImagenVideo.Id_Discoteca != id_discoteca_sesion
        # ).first()
        #
        # if not otros_media:
        # # Si no hay más media de OTRAS discotecas, es seguro eliminar el artista global
        # # Aquí también se deberían eliminar las redes sociales si no hay cascade delete
        # # for red_social in artista.redes_sociales:
        # # db.session.delete(red_social)
        # db.session.delete(artista)
        # flash(f'Artista "{artista.nombre}" y toda su media asociada eliminados globalmente.', 'success')
        # else:
        # flash(f'Media del artista "{artista.nombre}" asociada a su discoteca eliminada. El artista permanece globalmente por otras asociaciones.', 'info')
        
        # Implementación actual simplificada: Elimina el artista globalmente si el admin tiene asociación.
        # Esto podría ser destructivo si el artista es compartido.
        # La lógica comentada arriba es más segura para un sistema multi-discoteca con artistas compartidos.
        # Por ahora, procedemos con la eliminación global del artista si el admin tiene permiso (asociación).
        
        # Si hay relaciones como RedSocial que no usan cascade delete, hay que borrarlas manualmente.
        # Ejemplo, si RedSocial tiene artista_id y no hay cascade:
        # from src.models.redes_sociales import RedSocial # Suponiendo el modelo
        # RedSocial.query.filter_by(artista_id=artista.id_artista).delete()

        db.session.delete(artista) # Esto eliminará el artista globalmente.
        # --- FIN MODIFICACIONES ---

        db.session.commit()
        flash(f'Artista "{artista.nombre}" eliminado exitosamente (junto con su media asociada a esta discoteca).', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error al eliminar artista ID {id_artista} para discoteca {id_discoteca_sesion}: {str(e)}", exc_info=True)
        flash(f'Error al eliminar artista: {str(e)}', 'danger')
    return redirect(url_for('artistas.artistas'))


@artistas_bp.route('/obtener_datos_completos/<int:id_artista>')
def obtener_datos_completos_artista(id_artista):
    # --- INICIO MODIFICACIONES: Autenticación y Contexto de Discoteca ---
    # Decidir si esta ruta es pública o requiere admin. Por consistencia, la protejo.
    if 'user_id' not in session or session.get('user_rol') != 'Administrador':
        # Si fuera pública, se podría retornar jsonify de error o abort(403)
        flash("Debes iniciar sesión como Administrador para acceder a estos datos.", "warning")
        # Para una API, podrías retornar un JSON de error en lugar de flash/redirect
        return jsonify({"error": "Acceso no autorizado"}), 403


    id_discoteca_sesion = session.get('id_discoteca')
    if id_discoteca_sesion is None:
        flash("ID de discoteca no encontrado en sesión.", "error")
        return jsonify({"error": "ID de discoteca no encontrado en sesión"}), 403
    # --- FIN MODIFICACIONES ---

    # --- INICIO MODIFICACIONES: Verificar acceso al artista ---
    # Solo permitir obtener datos si el artista está asociado a la discoteca del admin.
    artista = Artista.query.join(
        ImagenVideo, Artista.id_artista == ImagenVideo.Id_referenciaTabla
    ).filter(
        Artista.id_artista == id_artista,
        ImagenVideo.Id_Discoteca == id_discoteca_sesion,
        ImagenVideo.Tipo_Tabla == 'artistas'
    ).first() # Usar first() para verificar

    if not artista:
        # Artista no encontrado con get_or_404 o no asociado a la discoteca
        original_artista = Artista.query.get(id_artista)
        if original_artista:
             return jsonify({"error": f"No tiene permiso para acceder a los datos del artista '{original_artista.nombre}' o no está asociado a su discoteca."}), 403
        return jsonify({"error": f"Artista con ID {id_artista} no encontrado."}), 404
    # --- FIN MODIFICACIONES ---
    
    # Las redes sociales son globales del artista, una vez verificado el acceso al artista, se pueden mostrar.
    # Si las redes sociales también fueran específicas por discoteca, se necesitaría un modelo más complejo.
    return jsonify({
        'id_artista': artista.id_artista,
        'nombre': artista.nombre,
        'genero_musical': artista.genero_musical,
        'descripcion': artista.descripcion,
        'redes_sociales': [{
            'id': red.id_red_social, # Asumiendo que el modelo RedSocial tiene estos campos
            'nombre': red.nombre,
            'url': red.url
        } for red in artista.redes_sociales] # Asumiendo que artista.redes_sociales es la relación
    })


# Relación con redes sociales (si es necesario)
@artistas_bp.route('/<int:id_artista>/redes', methods=['GET'])
def redes_sociales(id_artista): # Vista para mostrar/gestionar redes de un artista
    # --- INICIO MODIFICACIONES: Autenticación y Contexto de Discoteca ---
    if 'user_id' not in session or session.get('user_rol') != 'Administrador':
        flash("Debes iniciar sesión como Administrador para acceder a esta página.", "warning")
        return redirect(url_for('main.auth.login'))

    id_discoteca_sesion = session.get('id_discoteca')
    if id_discoteca_sesion is None:
        flash("ID de discoteca no encontrado en sesión.", "error")
        return redirect(url_for('main.auth.login'))
    # --- FIN MODIFICACIONES ---

    # --- INICIO MODIFICACIONES: Verificar acceso al artista ---
    artista = Artista.query.join(
        ImagenVideo, Artista.id_artista == ImagenVideo.Id_referenciaTabla
    ).filter(
        Artista.id_artista == id_artista,
        ImagenVideo.Id_Discoteca == id_discoteca_sesion,
        ImagenVideo.Tipo_Tabla == 'artistas'
    ).first()

    if not artista:
        original_artista = Artista.query.get(id_artista)
        if original_artista:
            flash(f"No tiene permiso para ver las redes sociales del artista '{original_artista.nombre}' o no está asociado a su discoteca.", "danger")
        else:
            flash(f"Artista con ID {id_artista} no encontrado.", "error")
        return redirect(url_for('artistas.artistas'))
    # --- FIN MODIFICACIONES ---

    # Asume que 'redes_sociales.html' existe y está preparado para mostrar las redes del artista.
    # artista.redes_sociales sería la relación SQLAlchemy.
    return render_template('redes_sociales.html', artista=artista, id_discoteca=id_discoteca_sesion)