import os
from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for, current_app
from src.database.db_mysql import db
from sqlalchemy import text
import logging
from src.utils.file_handling import allowed_file, secure_filename_wrapper

logging.basicConfig(level=logging.DEBUG)

productos_bp = Blueprint("productos", __name__,url_prefix='/productos')

@productos_bp.route('/get_all_products')
def index():
    try:
        result = db.session.execute(
            text("""
                SELECT p.id_producto, p.tipo, p.nombre, p.descripcion, p.precio_regular, p.promocion, 
                    pc.tamanio, pc.insumos, pc.stock
                FROM productos p
                LEFT JOIN piqueos_cocteles pc ON p.id_producto = pc.id_producto
                WHERE p.tipo IN ('piqueo', 'coctel');
            """)
        )
        productos = result.fetchall()
    except Exception as e:
        logging.error(e)
        flash('Error al obtener los productos', 'error')
        return redirect(url_for('home.index'))
    finally:
        db.session.close()
    return render_template('productos/index.html', productos=productos)


@productos_bp.route('/add', methods=['GET', 'POST'])
def add_producto():
    if request.method == 'POST':
        tipo = request.form.get('tipo')
        nombre = request.form.get('nombre')
        descripcion = request.form.get('descripcion')
        precio_regular = request.form.get('precio_regular')
        promocion = 1 if request.form.get('promocion') == '1' else 0
        tamanio = request.form.get('tamanio')
        insumos = request.form.get('insumos')
        stock = request.form.get('stock')
        descripcion_media = request.form.get('descripcion_media', '')

        # --- Logging para depuración ---
        current_app.logger.debug(f"Request form: {request.form}")
        current_app.logger.debug(f"Request files: {request.files}")
        # --- Fin Logging ---

        if not all([tipo, nombre, descripcion, precio_regular]):
            flash('Faltan campos requeridos del producto.', 'danger')
            return render_template('productos/add.html') # Asegúrate que la ruta a la plantilla sea correcta

        try:
            sql_insert_producto = text("""
                INSERT INTO productos (tipo, nombre, descripcion, precio_regular, promocion)
                VALUES (:tipo, :nombre, :descripcion, :precio_regular, :promocion)
            """)
            result_producto = db.session.execute(sql_insert_producto, {
                'tipo': tipo, 'nombre': nombre, 'descripcion': descripcion, 
                'precio_regular': float(precio_regular), 'promocion': promocion
            })
            
            id_producto = result_producto.lastrowid
            if not id_producto:
                 query_last_id = db.session.execute(text("SELECT LAST_INSERT_ID()")).scalar_one_or_none()
                 id_producto = query_last_id

            if not id_producto:
                current_app.logger.error("CRÍTICO: No se pudo obtener el ID del producto insertado.")
                raise Exception("No se pudo obtener el ID del producto insertado.")

            current_app.logger.info(f"Producto '{nombre}' insertado con ID: {id_producto}")

            if tipo in ['piqueo', 'coctel']:
                sql_insert_detalle = text("""
                    INSERT INTO piqueos_cocteles (id_producto, tamanio, insumos, stock)
                    VALUES (:id_producto, :tamanio, :insumos, :stock)
                """)
                db.session.execute(sql_insert_detalle, {
                    'id_producto': id_producto, 'tamanio': tamanio, 
                    'insumos': insumos, 'stock': int(stock) if stock and stock.isdigit() else None
                })
                current_app.logger.info(f"Detalle piqueo_coctel para ID {id_producto} insertado.")

            # --- INICIO: Manejo de Multimedia ---
            id_discoteca = 1 # Placeholder

            # 1. Archivos subidos
            archivos_subidos = request.files.getlist('archivos')
            current_app.logger.debug(f"Archivos detectados en request.files.getlist('archivos'): {[f.filename for f in archivos_subidos if f]}")

            for file in archivos_subidos:
                if file and file.filename: # Solo procesar si hay un archivo con nombre
                    if allowed_file(file.filename, current_app.config.get('ALLOWED_EXTENSIONS', set())):
                        filename = secure_filename_wrapper(file.filename)
                        # Asegúrate que UPLOAD_FOLDER esté definido en tu config y la carpeta exista y tenga permisos de escritura
                        upload_folder = current_app.config.get('UPLOAD_FOLDER', os.path.join(current_app.static_folder, 'uploads'))
                        if not os.path.exists(upload_folder):
                            os.makedirs(upload_folder, exist_ok=True)
                        file_path = os.path.join(upload_folder, filename)
                        
                        try:
                            file.save(file_path)
                            current_app.logger.info(f"Archivo '{filename}' guardado en: {file_path}")

                            tipo_archivo_media = 'imagen' if file.content_type.startswith('image') else 'video_local'
                            
                            # -- CAMBIO IMPORTANTE AQUÍ --
                            tipo_tabla_para_media = 'piqueos_cocteles' # Según tu requerimiento

                            current_app.logger.debug(f"Intentando insertar ImagenVideo (archivo): id_prod={id_producto}, tipo_tabla='{tipo_tabla_para_media}', desc='{descripcion_media}', tipo_arch='{tipo_archivo_media}', arch_nombre='{filename}'")
                            
                            sql_insert_media = text("""
                                INSERT INTO imagenesvideos (Id_Discoteca, Tipo_Tabla, Id_referenciaTabla, Descripcion, Tipo_Archivo, Archivo)
                                VALUES (:id_discoteca, :tipo_tabla, :id_referencia_tabla, :descripcion, :tipo_archivo, :archivo_nombre)
                            """)
                            db.session.execute(sql_insert_media, {
                                'id_discoteca': id_discoteca,
                                'tipo_tabla': tipo_tabla_para_media, # Usar la variable definida
                                'id_referencia_tabla': id_producto,
                                'descripcion': descripcion_media,
                                'tipo_archivo': tipo_archivo_media,
                                'archivo_nombre': filename 
                            })
                            current_app.logger.info(f"Registro de media para archivo '{filename}' preparado para commit.")
                        except Exception as e_save_file:
                            current_app.logger.error(f"Error al procesar/guardar archivo '{filename}': {e_save_file}")
                            flash(f"Error al procesar archivo '{filename}'", "warning")
                    else:
                        current_app.logger.warning(f"Archivo no permitido: {file.filename} (tipo: {file.content_type})")
                        flash(f"Tipo de archivo no permitido: {file.filename}", "warning")
                elif file: # Si file existe pero file.filename está vacío
                     current_app.logger.debug("Se detectó un 'file' en 'archivos_subidos' pero sin 'filename'.")


            # 2. URLs de Video
            urls_video_str = request.form.get('urls_video')
            current_app.logger.debug(f"URLs de video recibidas (string): {urls_video_str}")
            if urls_video_str:
                lista_urls = [url.strip() for url in urls_video_str.split(',') if url.strip()]
                for video_url in lista_urls:
                    # -- CAMBIO IMPORTANTE AQUÍ --
                    tipo_tabla_para_media = 'piqueos_cocteles' # Según tu requerimiento

                    current_app.logger.debug(f"Intentando insertar ImagenVideo (URL): id_prod={id_producto}, tipo_tabla='{tipo_tabla_para_media}', desc='{descripcion_media}', url='{video_url}'")
                    
                    sql_insert_media_url = text("""
                        INSERT INTO imagenesvideos (Id_Discoteca, Tipo_Tabla, Id_referenciaTabla, Descripcion, Tipo_Archivo, Archivo)
                        VALUES (:id_discoteca, :tipo_tabla, :id_referencia_tabla, :descripcion, :tipo_archivo, :archivo_url)
                    """)
                    db.session.execute(sql_insert_media_url, {
                        'id_discoteca': id_discoteca,
                        'tipo_tabla': tipo_tabla_para_media, # Usar la variable definida
                        'id_referencia_tabla': id_producto,
                        'descripcion': descripcion_media,
                        'tipo_archivo': 'video', 
                        'archivo_url': video_url
                    })
                    current_app.logger.info(f"Registro de media para URL '{video_url}' preparado para commit.")
            # --- FIN: Manejo de Multimedia ---

            db.session.commit() 
            flash('Producto agregado correctamente con multimedia!', 'success')
            return redirect(url_for('productos.index')) # Asegúrate que 'productos.index' sea la ruta correcta

        except Exception as e:
            db.session.rollback() 
            # Usar current_app.logger para errores de la aplicación
            current_app.logger.error(f"Error general al agregar el producto: {e}", exc_info=True) # exc_info=True para el traceback
            flash(f'Error al agregar el producto: {str(e)}', 'danger')
            return redirect(url_for('productos.add_producto'))
        # finally: # No cierres la sesión aquí si usas el patrón de Flask-SQLAlchemy donde la sesión es manejada por la extensión
        #     db.session.close() 

    return render_template('productos/add.html') # Asegúrate que la ruta a la plantilla sea correcta



@productos_bp.route('/update/<int:id>', methods=['GET', 'POST'])
def update_producto(id):
    producto_data = None
    detalle_piqueo_coctel = None
    archivos_multimedia = []

    if request.method == 'GET':
        try:
            sql_select_producto = text("""
                SELECT id_producto, tipo, nombre, descripcion, precio_regular, promocion 
                FROM productos WHERE id_producto = :id
            """)
            producto_data = db.session.execute(sql_select_producto, {'id': id}).mappings().fetchone()

            if not producto_data:
                flash('Producto no encontrado.', 'danger')
                return redirect(url_for('productos.index'))

            if producto_data.tipo in ['piqueo', 'coctel']:
                sql_select_detalle = text("""
                    SELECT tamanio, insumos, stock 
                    FROM piqueos_cocteles WHERE id_producto = :id
                """)
                detalle_piqueo_coctel = db.session.execute(sql_select_detalle, {'id': id}).mappings().fetchone()

            sql_select_media = text("""
                SELECT Id_imgV, Archivo, Tipo_Archivo, Descripcion 
                FROM imagenesvideos 
                WHERE Id_referenciaTabla = :id_producto AND Tipo_Tabla = :tipo_tabla
            """)
            # Asumiendo que 'piqueos_cocteles' es el Tipo_Tabla correcto para estos productos
            # Si el Tipo_Tabla puede variar, necesitarás una lógica más compleja o almacenarlo en la tabla productos.
            tipo_tabla_para_media = 'piqueos_cocteles' # Ajusta si es necesario
            media_items = db.session.execute(sql_select_media, {'id_producto': id, 'tipo_tabla': tipo_tabla_para_media}).mappings().all()
            archivos_multimedia = media_items

            return render_template('productos/edit.html', producto=producto_data, detalle=detalle_piqueo_coctel, archivos_multimedia=archivos_multimedia)

        except Exception as e:
            logging.error(f"Error al cargar el producto para editar {id}: {e}", exc_info=True)
            flash('Error al cargar la información del producto.', 'danger')
            return redirect(url_for('productos.index'))

    elif request.method == 'POST':
        try:
            # Recuperar datos del formulario
            tipo = request.form.get('tipo')
            nombre = request.form.get('nombre')
            descripcion = request.form.get('descripcion')
            precio_regular_str = request.form.get('precio_regular')
            promocion = 1 if request.form.get('promocion') == '1' else 0
            
            tamanio = request.form.get('tamanio')
            insumos = request.form.get('insumos')
            stock_str = request.form.get('stock')

            descripcion_media_general = request.form.get('descripcion_media_modal', '') # Desc general para nueva media
            
            deleted_media_ids_str = request.form.get('deleted_media_ids', '')
            deleted_media_ids = [int(mid) for mid in deleted_media_ids_str.split(',') if mid.strip().isdigit()]

            if not all([tipo, nombre, descripcion, precio_regular_str]):
                flash('Faltan campos requeridos del producto.', 'danger')
                # Recargar datos para el template si la validación falla
                # (Este bloque es similar al GET, podrías refactorizarlo en una función)
                sql_select_producto_reload = text("SELECT id_producto, tipo, nombre, descripcion, precio_regular, promocion FROM productos WHERE id_producto = :id")
                producto_data_reload = db.session.execute(sql_select_producto_reload, {'id': id}).mappings().fetchone()
                detalle_piqueo_coctel_reload = None
                if producto_data_reload and producto_data_reload.tipo in ['piqueo', 'coctel']:
                    sql_select_detalle_reload = text("SELECT tamanio, insumos, stock FROM piqueos_cocteles WHERE id_producto = :id")
                    detalle_piqueo_coctel_reload = db.session.execute(sql_select_detalle_reload, {'id': id}).mappings().fetchone()
                sql_select_media_reload = text("SELECT Id_imgV, Archivo, Tipo_Archivo, Descripcion FROM imagenesvideos WHERE Id_referenciaTabla = :id_producto AND Tipo_Tabla = 'piqueos_cocteles'")
                media_items_reload = db.session.execute(sql_select_media_reload, {'id_producto': id, 'tipo_tabla': 'piqueos_cocteles'}).mappings().all()
                return render_template('productos/edit.html', producto=producto_data_reload, detalle=detalle_piqueo_coctel_reload, archivos_multimedia=media_items_reload)


            precio_regular = float(precio_regular_str)
            stock = int(stock_str) if stock_str and stock_str.isdigit() else None

            # 1. Actualizar la tabla de productos
            sql_update_producto = text("""
                UPDATE productos
                SET tipo = :tipo, nombre = :nombre, descripcion = :descripcion,
                    precio_regular = :precio_regular, promocion = :promocion
                WHERE id_producto = :id
            """)
            db.session.execute(sql_update_producto, {
                'tipo': tipo, 'nombre': nombre, 'descripcion': descripcion,
                'precio_regular': precio_regular, 'promocion': promocion, 'id': id
            })

            # 2. Actualizar o insertar en piqueos_cocteles
            if tipo in ['piqueo', 'coctel']:
                sql_check_detalle = text("SELECT id_producto FROM piqueos_cocteles WHERE id_producto = :id")
                detalle_exists = db.session.execute(sql_check_detalle, {'id': id}).fetchone()

                if detalle_exists:
                    sql_update_detalle = text("""
                        UPDATE piqueos_cocteles
                        SET tamanio = :tamanio, insumos = :insumos, stock = :stock
                        WHERE id_producto = :id
                    """)
                    db.session.execute(sql_update_detalle, {
                        'tamanio': tamanio, 'insumos': insumos, 'stock': stock, 'id': id
                    })
                else:
                    sql_insert_detalle = text("""
                        INSERT INTO piqueos_cocteles (id_producto, tamanio, insumos, stock)
                        VALUES (:id_producto, :tamanio, :insumos, :stock)
                    """)
                    db.session.execute(sql_insert_detalle, {
                        'id_producto': id, 'tamanio': tamanio, 'insumos': insumos, 'stock': stock
                    })
            else: # Si el tipo cambió y ya no es piqueo/coctel, podrías querer eliminar la entrada de piqueos_cocteles
                sql_delete_if_not_piqueo_coctel = text("DELETE FROM piqueos_cocteles WHERE id_producto = :id")
                db.session.execute(sql_delete_if_not_piqueo_coctel, {'id': id})


            # 3. Eliminar multimedia marcada para eliminación
            upload_folder = current_app.config.get('UPLOAD_FOLDER', os.path.join(current_app.static_folder, 'uploads'))
            for media_id_to_delete in deleted_media_ids:
                sql_select_media_to_delete = text("SELECT Archivo, Tipo_Archivo FROM imagenesvideos WHERE Id_imgV = :id_imgV")
                media_to_delete = db.session.execute(sql_select_media_to_delete, {'id_imgV': media_id_to_delete}).mappings().fetchone()

                if media_to_delete:
                    if media_to_delete.Tipo_Archivo in ['imagen', 'video_local'] and media_to_delete.Archivo:
                        file_path_to_delete = os.path.join(upload_folder, media_to_delete.Archivo)
                        try:
                            if os.path.exists(file_path_to_delete):
                                os.remove(file_path_to_delete)
                                logging.info(f"Archivo físico eliminado (update): {file_path_to_delete}")
                        except Exception as e_file_delete:
                            logging.error(f"Error eliminando archivo físico (update) {media_to_delete.Archivo}: {str(e_file_delete)}")
                    
                    sql_delete_media_db = text("DELETE FROM imagenesvideos WHERE Id_imgV = :id_imgV")
                    db.session.execute(sql_delete_media_db, {'id_imgV': media_id_to_delete})
                    logging.info(f"Registro de multimedia ID {media_id_to_delete} eliminado (update).")

            # 4. Manejar nueva multimedia
            id_discoteca = 1 # Placeholder, ajustar según tu lógica
            tipo_tabla_para_media = 'piqueos_cocteles' # Asumiendo para estos productos

            # Archivos subidos
            archivos_subidos_nuevos = request.files.getlist('archivos') # 'archivos' es el name del input oculto
            allowed_extensions_config = current_app.config.get('ALLOWED_EXTENSIONS', {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'mov', 'avi'})
            
            for file in archivos_subidos_nuevos:
                if file and file.filename and allowed_file(file.filename, allowed_extensions_config):
                    filename = secure_filename_wrapper(file.filename)
                    os.makedirs(upload_folder, exist_ok=True)
                    file_path = os.path.join(upload_folder, filename)
                    try:
                        file.save(file_path)
                        tipo_archivo_media = 'imagen' if file.content_type.startswith('image') else 'video_local'
                        
                        sql_insert_media_file = text("""
                            INSERT INTO imagenesvideos (Id_Discoteca, Tipo_Tabla, Id_referenciaTabla, Descripcion, Tipo_Archivo, Archivo)
                            VALUES (:id_discoteca, :tipo_tabla, :id_referencia_tabla, :descripcion, :tipo_archivo, :archivo_nombre)
                        """)
                        db.session.execute(sql_insert_media_file, {
                            'id_discoteca': id_discoteca, 'tipo_tabla': tipo_tabla_para_media,
                            'id_referencia_tabla': id, 'descripcion': descripcion_media_general,
                            'tipo_archivo': tipo_archivo_media, 'archivo_nombre': filename
                        })
                        logging.info(f"Nuevo archivo '{filename}' guardado y registrado para producto ID {id}.")
                    except Exception as e_save:
                        logging.error(f"Error al guardar nuevo archivo '{filename}' para producto ID {id}: {e_save}")
                        flash(f"Error al guardar el archivo '{filename}'", "warning")
                elif file and file.filename:
                    flash(f"Tipo de archivo no permitido: {file.filename}", "warning")
            
            # URLs de Video
            urls_video_str_nuevas = request.form.get('urls_video') # name del input oculto de URLs
            if urls_video_str_nuevas:
                lista_urls_nuevas = [url.strip() for url in urls_video_str_nuevas.split(',') if url.strip()]
                for video_url in lista_urls_nuevas:
                    sql_insert_media_url = text("""
                        INSERT INTO imagenesvideos (Id_Discoteca, Tipo_Tabla, Id_referenciaTabla, Descripcion, Tipo_Archivo, Archivo)
                        VALUES (:id_discoteca, :tipo_tabla, :id_referencia_tabla, :descripcion, :tipo_archivo, :archivo_url)
                    """)
                    db.session.execute(sql_insert_media_url, {
                        'id_discoteca': id_discoteca, 'tipo_tabla': tipo_tabla_para_media,
                        'id_referencia_tabla': id, 'descripcion': descripcion_media_general,
                        'tipo_archivo': 'video', 'archivo_url': video_url # 'video' para URLs externas
                    })
                    logging.info(f"Nueva URL de video '{video_url}' registrada para producto ID {id}.")

            db.session.commit()
            flash('Producto actualizado correctamente!', 'success')
            return redirect(url_for('productos.index'))

        except Exception as e:
            db.session.rollback()
            logging.error(f"Error general al actualizar el producto {id}: {e}", exc_info=True)
            flash(f'Error al actualizar el producto: {str(e)}', 'danger')
            # Es importante redirigir de nuevo al formulario de edición con los datos actuales si hay un error
            # Para simplificar, redirigimos al index, pero idealmente se debería repoblar el formulario.
            return redirect(url_for('productos.update_producto', id=id))

    return redirect(url_for('productos.index')) # Fallback por si no es GET ni POST


@productos_bp.route('/delete/<int:id>', methods=['POST']) # Es buena práctica usar POST para eliminar
def delete_producto(id):
    try:
        # 0. Verificar si el producto existe
        producto_a_eliminar = db.session.execute(text("SELECT tipo FROM productos WHERE id_producto = :id"), {'id': id}).mappings().fetchone()
        if not producto_a_eliminar:
            flash('Producto no encontrado para eliminar.', 'warning')
            return redirect(url_for('productos.index'))

        tipo_tabla_para_media = 'piqueos_cocteles' # Ajustar si la lógica de Tipo_Tabla es más compleja

        # 1. Obtener información de multimedia para eliminar archivos físicos
        sql_select_media = text("""
            SELECT Id_imgV, Archivo, Tipo_Archivo 
            FROM imagenesvideos 
            WHERE Id_referenciaTabla = :id AND Tipo_Tabla = :tipo_tabla
        """)
        media_files_to_delete = db.session.execute(sql_select_media, {'id': id, 'tipo_tabla': tipo_tabla_para_media}).mappings().all()

        # 2. Eliminar registros de la tabla imagenesvideos
        sql_delete_media_db = text("DELETE FROM imagenesvideos WHERE Id_referenciaTabla = :id AND Tipo_Tabla = :tipo_tabla")
        db.session.execute(sql_delete_media_db, {'id': id, 'tipo_tabla': tipo_tabla_para_media})

        # 3. Eliminar registros de la tabla piqueos_cocteles (si aplica)
        if producto_a_eliminar.tipo in ['piqueo', 'coctel']:
            sql_delete_detalle = text("DELETE FROM piqueos_cocteles WHERE id_producto = :id")
            db.session.execute(sql_delete_detalle, {'id': id})

        # 4. Eliminar el producto de la tabla productos
        sql_delete_producto = text("DELETE FROM productos WHERE id_producto = :id")
        result = db.session.execute(sql_delete_producto, {'id': id})

        if result.rowcount == 0: # Doble chequeo, aunque ya se hizo arriba
            flash('No se pudo eliminar el producto (quizás ya fue eliminado).', 'warning')
            db.session.rollback() # Revertir si la eliminación principal falló
            return redirect(url_for('productos.index'))

        # 5. Eliminar archivos físicos del servidor
        upload_folder = current_app.config.get('UPLOAD_FOLDER', os.path.join(current_app.static_folder, 'uploads'))
        for media in media_files_to_delete:
            if media.Tipo_Archivo in ['imagen', 'video_local'] and media.Archivo:
                try:
                    file_path = os.path.join(upload_folder, media.Archivo)
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        logging.info(f"Archivo físico eliminado (delete): {file_path}")
                except Exception as e_file:
                    logging.error(f"Error eliminando archivo físico {media.Archivo} (delete): {str(e_file)}")
        
        db.session.commit()
        flash('Producto eliminado correctamente.', 'success')

    except Exception as e:
        db.session.rollback()
        logging.error(f"Error al eliminar el producto ID {id}: {e}", exc_info=True)
        flash('Error al eliminar el producto.', 'danger')
    
    return redirect(url_for('productos.index'))

# Aquí deberías tener tu ruta add_producto y cualquier otra que necesites.
# El código de add_producto que proporcionaste parece mayormente bien,
# solo asegúrate que el UPLOAD_FOLDER y ALLOWED_EXTENSIONS estén bien configurados en tu app.
# from .routes_add import add_producto_bp # Si la tienes en otro archivo
# productos_bp.register_blueprint(add_producto_bp)

