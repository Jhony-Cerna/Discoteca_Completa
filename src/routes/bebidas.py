import os
from flask import Blueprint, render_template, request, redirect, url_for, flash,current_app
from src.database.db_mysql import db
from src.models.producto import Producto
from src.models.bebida import Bebida
from src.models.categoria_bebida import CategoriaBebida
from src.models.media import ImagenVideo  # Asegúrate que el modelo exista
from src.utils.file_handling import allowed_file, secure_filename_wrapper


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
            precio = float(request.form['precio'])
            tamanio = float(request.form['tamano']) # Asumo que 'tamano' es tamaño numérico, no string como en mesas/boxes
            stock = int(request.form['stock'])
            
            if precio <= 0 or tamanio <= 0 or stock < 0:
                raise ValueError("Valores numéricos deben ser positivos y stock no negativo.")

            nuevo_producto = Producto(
                tipo='bebida',
                nombre=request.form['nombre'].strip(),
                descripcion=request.form['descripcion'].strip(),
                precio_regular=precio,
                promocion=request.form.get('promocion') == 'on' # Checkbox
            )
            db.session.add(nuevo_producto)
            db.session.flush()  # Obtener ID del producto para asociar la bebida y media

            nueva_bebida = Bebida(
                id_producto=nuevo_producto.id_producto,
                marca=request.form['marca'].strip(),
                tamanio=tamanio,
                stock=stock,
                id_categoria=int(request.form['categoria'])
            )
            db.session.add(nueva_bebida)

            # --- INICIO: Manejo de Multimedia ---
            id_discoteca = 1 # Placeholder, ajusta según tu lógica

            # 1. Archivos subidos
            archivos_subidos = request.files.getlist('archivos') # name="archivos" en tu input file
            for file in archivos_subidos:
                if file and file.filename and allowed_file(file.filename, current_app.config['ALLOWED_EXTENSIONS']):
                    filename = secure_filename_wrapper(file.filename)
                    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                    file.save(file_path)

                    tipo_archivo_media = 'imagen' if file.content_type.startswith('image') else 'video'
                    
                    media_archivo = ImagenVideo(
                        Id_Discoteca=id_discoteca,
                        Tipo_Tabla='bebidas', # Asociado al producto genérico
                        Id_referenciaTabla=nuevo_producto.id_producto,
                        Descripcion=request.form.get('descripcion_media_archivos', ''), # Si tienes un campo para esto
                        Tipo_Archivo=tipo_archivo_media,
                        Archivo=filename
                    )
                    db.session.add(media_archivo)

            # 2. URLs de Video
            urls_video_str = request.form.get('urls_video') # name="urls_video" en tu input hidden
            if urls_video_str:
                lista_urls = [url.strip() for url in urls_video_str.split(',') if url.strip()]
                for video_url in lista_urls:
                    media_url = ImagenVideo(
                        Id_Discoteca=id_discoteca,
                        Tipo_Tabla='bebidas', # Asociado al producto genérico
                        Id_referenciaTabla=nuevo_producto.id_producto,
                        Descripcion=request.form.get('descripcion_media_urls', ''), # Si tienes un campo para esto
                        Tipo_Archivo='video',
                        Archivo=video_url
                    )
                    db.session.add(media_url)
            # --- FIN: Manejo de Multimedia ---

            db.session.commit()
            flash('Bebida creada exitosamente con multimedia!', 'success')
            return redirect(url_for('bebidas.listar_bebidas'))

        except ValueError as ve:
            db.session.rollback()
            flash(f'Error de validación: {str(ve)}', 'danger')
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error al crear bebida: {str(e)}")
            flash(f'Error al crear bebida: {str(e)}', 'danger')
    
    categorias = CategoriaBebida.query.order_by(CategoriaBebida.nombre_categoria).all()
    # Pasar un id_discoteca si tu HTML lo necesita para el modal de media, etc.
    return render_template('Agregar_bebidas.html', categorias=categorias, id_discoteca=1)




@bebidas_bp.route('/editar/<int:id>', methods=['GET', 'POST']) # id aquí es id_producto
def editar_bebida(id):
    # El 'id' de la ruta es el id_producto
    producto = Producto.query.get_or_404(id)
    # Buscamos la bebida específica usando el id_producto
    bebida = Bebida.query.filter_by(id_producto=id).first_or_404()
    categorias = CategoriaBebida.query.all()

    if request.method == 'POST':
        try:
            # Actualizar Producto
            producto.nombre = request.form['nombre'].strip()
            producto.descripcion = request.form['descripcion'].strip()
            producto.precio_regular = float(request.form['precio'])
            producto.promocion = request.form.get('promocion') == 'on' # Checkbox

            # Actualizar Bebida
            bebida.marca = request.form['marca'].strip()
            bebida.tamanio = float(request.form['tamano'])
            bebida.stock = int(request.form['stock'])
            bebida.id_categoria = int(request.form['categoria'])

            # --- INICIO: Manejo de Multimedia para Edición ---
            id_discoteca = 1 # Placeholder

            # 1. Eliminar multimedia marcada
            deleted_media_ids_str = request.form.get('deleted_media')
            if deleted_media_ids_str:
                media_ids_to_delete = [int(media_id) for media_id in deleted_media_ids_str.split(',') if media_id.strip()]
                for media_id_val in media_ids_to_delete:
                    media_item = ImagenVideo.query.get(media_id_val)
                    if media_item:
                        if media_item.Tipo_Archivo == 'imagen' and \
                            media_item.Archivo and \
                            not media_item.Archivo.startswith(('http://', 'https://')):
                            try:
                                file_path_to_delete = os.path.join(current_app.config['UPLOAD_FOLDER'], media_item.Archivo)
                                if os.path.exists(file_path_to_delete):
                                    os.remove(file_path_to_delete)
                            except Exception as e_file_delete:
                                current_app.logger.error(f"Error eliminando archivo físico {media_item.Archivo}: {str(e_file_delete)}")
                                flash(f"Advertencia: No se pudo eliminar el archivo {media_item.Archivo} del servidor.", "warning")
                        db.session.delete(media_item)
            
            # 2. Agregar nuevos archivos subidos
            archivos_subidos = request.files.getlist('archivos')
            for file in archivos_subidos:
                if file and file.filename and allowed_file(file.filename, current_app.config['ALLOWED_EXTENSIONS']):
                    filename = secure_filename_wrapper(file.filename)
                    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                    file.save(file_path)
                    tipo_archivo_media = 'imagen' if file.content_type.startswith('image') else 'video'
                    media_archivo = ImagenVideo(
                        Id_Discoteca=id_discoteca,
                        Tipo_Tabla='bebidas',
                        Id_referenciaTabla=producto.id_producto,
                        Descripcion=request.form.get('descripcion_media_archivos', ''),
                        Tipo_Archivo=tipo_archivo_media,
                        Archivo=filename
                    )
                    db.session.add(media_archivo)

            # 3. Agregar nuevas URLs de Video
            urls_video_str = request.form.get('urls_video')
            if urls_video_str:
                lista_urls = [url.strip() for url in urls_video_str.split(',') if url.strip()]
                for video_url in lista_urls:
                    media_url = ImagenVideo(
                        Id_Discoteca=id_discoteca,
                        Tipo_Tabla='bebidas',
                        Id_referenciaTabla=producto.id_producto,
                        Descripcion=request.form.get('descripcion_media_urls', ''),
                        Tipo_Archivo='video',
                        Archivo=video_url
                    )
                    db.session.add(media_url)
            # --- FIN: Manejo de Multimedia para Edición ---

            db.session.commit()
            flash('Bebida actualizada correctamente con multimedia!', 'success')
            return redirect(url_for('bebidas.listar_bebidas'))

        except ValueError as ve:
            db.session.rollback()
            flash(f'Error de validación al actualizar: {str(ve)}', 'danger')
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error al actualizar bebida {id}: {str(e)}")
            flash(f'Error al actualizar: {str(e)}', 'danger')
            # Re-renderizar el formulario con los datos actuales y errores
            archivos_multimedia_existentes = ImagenVideo.query.filter_by(
                Tipo_Tabla='bebidas', # CAMBIE decia espacios
                Id_referenciaTabla=id
            ).all()
            return render_template('Actualizar_bebida.html', 
                                    bebida=bebida, 
                                    producto=producto, 
                                    categorias=categorias, 
                                    archivos_multimedia=archivos_multimedia_existentes,
                                    id_discoteca=1) # Asegúrate que el id de la ruta sea el correcto para producto

    # GET Request: Cargar datos existentes para el formulario de edición
    archivos_multimedia_existentes = ImagenVideo.query.filter_by(
        Tipo_Tabla='bebidas', # Coherente con cómo se guarda
        Id_referenciaTabla=id # id es id_producto
    ).all()
    
    return render_template('Actualizar_bebida.html', 
                            bebida=bebida, 
                            producto=producto, 
                            categorias=categorias, 
                            archivos_multimedia=archivos_multimedia_existentes,
                            id_discoteca=1) # Para el modal de media



@bebidas_bp.route('/eliminar/<int:id>', methods=['POST']) # id aquí es id_producto
def eliminar_bebida(id):
    producto = Producto.query.get_or_404(id)
    bebida = Bebida.query.filter_by(id_producto=id).first_or_404() # Asegurar que la bebida existe
    
    try:
        # --- INICIO: Eliminar Multimedia Asociada ---
        media_items_a_eliminar = ImagenVideo.query.filter_by(
            Tipo_Tabla='productos', 
            Id_referenciaTabla=id
        ).all()

        for media_item in media_items_a_eliminar:
            if media_item.Tipo_Archivo == 'imagen' and \
               media_item.Archivo and \
               not media_item.Archivo.startswith(('http://', 'https://')):
                try:
                    file_path_to_delete = os.path.join(current_app.config['UPLOAD_FOLDER'], media_item.Archivo)
                    if os.path.exists(file_path_to_delete):
                        os.remove(file_path_to_delete)
                except Exception as e_file_delete_final:
                    current_app.logger.error(f"Error eliminando archivo físico {media_item.Archivo} durante borrado de bebida: {str(e_file_delete_final)}")
                    flash(f"Advertencia: No se pudo eliminar el archivo {media_item.Archivo} del servidor.", "warning")
            db.session.delete(media_item)
        # --- FIN: Eliminar Multimedia Asociada ---

        db.session.delete(bebida)
        db.session.delete(producto) # El producto se elimina después de su media y la bebida específica
        db.session.commit()
        flash('Bebida y su multimedia asociada eliminadas exitosamente.', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error al eliminar bebida {id}: {str(e)}")
        flash(f'Error al eliminar: {str(e)}', 'danger')
    
    return redirect(url_for('bebidas.listar_bebidas'))