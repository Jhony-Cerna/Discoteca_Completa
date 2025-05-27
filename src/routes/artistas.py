import os
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
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
    # Obtener todos los artistas con paginación
    page = request.args.get('page', 1, type=int)
    per_page = 10
    artistas = Artista.query.order_by(Artista.nombre.asc()).paginate(page=page, per_page=per_page)
    return render_template('Tabla_Artistas.html', artistas=artistas)



@artistas_bp.route('/crear', methods=['GET', 'POST'])
def crear_artista():
    form_data = {} # Para retener datos en caso de error GET o validación
    next_url = request.args.get('next') or url_for('artistas.artistas') # Asegurar que 'next' sea seguro si es de usuario
    print("probando si entra en crear artista")

    if request.method == 'POST':
            # --- INICIO DE BLOQUE DE DEPURACIÓN ---
        print("-----------------------------------------------")
        print(f"FORMULARIO RECIBIDO (request.form): {request.form}")
        print(f"ARCHIVOS RECIBIDOS (request.files): {request.files}")
        
        archivos_procesar = request.files.getlist('archivos')
        print(f"RESULTADO DE request.files.getlist('archivos'): {archivos_procesar}")
        if archivos_procesar:
            for f in archivos_procesar:
                print(f"-> Archivo en lista: name='{f.name}', filename='{f.filename}', content_type='{f.content_type}'")
        
        urls_video_str = request.form.get('urls_video', 'NO_URLS_VIDEO_FIELD')
        print(f"CAMPO 'urls_video' (raw string): '{urls_video_str}'")
        print("-----------------------------------------------")
        # --- FIN DE BLOQUE DE DEPURACIÓN ---
        try:
            nombre_artistico = request.form.get('nombreArtistico', '').strip()
            genero_musical = request.form.get('generoMusical', '').strip()
            descripcion_artista = request.form.get('descripcion', '').strip()
            
            # Guardar datos del formulario para re-poblar en caso de error
            form_data = request.form 

            if not all([nombre_artistico, genero_musical, descripcion_artista]):
                flash('Todos los campos obligatorios del artista deben estar completos.', 'warning')
                # No se usa 'artistas/artistas_form.html', debe ser la ruta del template actual
                return render_template(current_app.config.get('ARTISTAS_FORM_TEMPLATE', 'artistas/artistas_form.html'), form_data=form_data, next_url=next_url)


            # Verificar si el artista ya existe (si el nombre es único)
            if Artista.query.filter_by(nombre=nombre_artistico).first():
                flash(f'El artista "{nombre_artistico}" ya existe.', 'warning')
                return render_template(current_app.config.get('ARTISTAS_FORM_TEMPLATE', 'artistas/artistas_form.html'), form_data=form_data, next_url=next_url)

            nuevo_artista = Artista(
                nombre=nombre_artistico,
                genero_musical=genero_musical,
                descripcion=descripcion_artista
            )
            db.session.add(nuevo_artista)
            db.session.flush()  # Obtener ID del artista antes del commit final

            # Procesar multimedia
            id_discoteca = 1  # ATENCIÓN: Hardcodeado. Asegúrate que Discoteca con ID=1 exista.
                            # Considera hacerlo dinámico o configurable.
            
            # Descripciones para multimedia (una por tipo si se suben varios items a la vez)
            descripcion_media_archivos = request.form.get('descripcion_media_archivos', '').strip()
            descripcion_media_urls = request.form.get('descripcion_media_urls', '').strip()

            # Procesar archivos subidos (imágenes)
            archivos_subidos = request.files.getlist('archivos')
            if archivos_subidos:
                for file_storage in archivos_subidos:
                    if file_storage and file_storage.filename != '' and allowed_file(file_storage.filename, current_app.config.get('ALLOWED_IMAGE_EXTENSIONS', {'png', 'jpg', 'jpeg', 'gif'})):
                        filename = secure_filename_wrapper(file_storage.filename)
                        upload_folder = current_app.config.get('UPLOAD_FOLDER')
                        if not upload_folder:
                            current_app.logger.error("UPLOAD_FOLDER no está configurado.")
                            flash('Error de configuración del servidor al guardar archivo.', 'danger')
                            db.session.rollback()
                            return render_template(current_app.config.get('ARTISTAS_FORM_TEMPLATE', 'artistas/artistas_form.html'), form_data=form_data, next_url=next_url)
                        
                        try:
                            file_path = os.path.join(upload_folder, filename)
                            file_storage.save(file_path)

                            media_item = ImagenVideo(
                                Id_Discoteca=id_discoteca,
                                Tipo_Tabla='artistas',
                                Id_referenciaTabla=nuevo_artista.id_artista,
                                Descripcion=descripcion_media_archivos, # Usa la descripción general para archivos
                                Tipo_Archivo='imagen',
                                Archivo=filename # Guardar solo el nombre del archivo, no la ruta completa
                            )
                            db.session.add(media_item)
                        except Exception as e_file:
                            current_app.logger.error(f"Error al guardar archivo {filename}: {str(e_file)}")
                            flash(f'Error al procesar el archivo {filename}.', 'warning')
                            # Decide si continuar sin este archivo o rollback todo.
                            # Por ahora, continuamos pero no se guarda este archivo específico.

            # Procesar URLs de video
            urls_video_str = request.form.get('urls_video', '')
            if urls_video_str:
                lista_urls_video = [url.strip() for url in urls_video_str.split(',') if url.strip()]
                for video_url in lista_urls_video:
                    media_item = ImagenVideo(
                        Id_Discoteca=id_discoteca,
                        Tipo_Tabla='artistas',
                        Id_referenciaTabla=nuevo_artista.id_artista,
                        Descripcion=descripcion_media_urls, # Usa la descripción general para URLs
                        Tipo_Archivo='video',
                        Archivo=video_url
                    )
                    db.session.add(media_item)

            db.session.commit()
            flash(f'Artista "{nombre_artistico}" creado exitosamente!', 'success')
            
            # Redirigir a next_url si es seguro, de lo contrario a la lista de artistas
            # from src.utils.security import is_safe_url # Necesitarías esta utilidad
            # if next_url and is_safe_url(next_url, request.host_url):
            #    return redirect(next_url)
            return redirect(url_for('artistas.artistas'))


        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error al crear artista: {str(e)}", exc_info=True)
            flash(f'Error al guardar el artista: {str(e)}', 'danger')
            # Re-renderizar el formulario con los datos que el usuario ya había ingresado
            form_data = request.form # Asegurarse que form_data tiene los últimos datos intentados

    # Para el método GET o si hubo un error POST y se re-renderiza
    return render_template(current_app.config.get('ARTISTAS_FORM_TEMPLATE', 'artistas.html'), form_data=form_data, next_url=next_url)

    


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