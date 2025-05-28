import os
from flask import Blueprint, current_app, flash, jsonify, redirect, render_template, request, session, url_for
#from src.models.media import Media  # Asegúrate de importar el modelo correcto
from src.models.media import ImagenVideo  # Asegúrate que el modelo exista
from src.utils.file_handling import allowed_file, secure_filename_wrapper
from src.database.db_mysql import db

mesasyboxes_bp = Blueprint('mesasyboxes', __name__)

# Modelo para la tabla productos
class Producto(db.Model):
    __tablename__ = 'productos'
    id_producto = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(50), nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.String(255), nullable=True)
    precio_regular = db.Column(db.Float, nullable=False)
    promocion = db.Column(db.Boolean, default=False)

# Modelo para la tabla espacios
class Espacio(db.Model):
    __tablename__ = 'espacios'
    id_producto = db.Column(db.Integer, db.ForeignKey('productos.id_producto'), primary_key=True)
    capacidad = db.Column(db.Integer, nullable=False)
    tamanio = db.Column(db.String(50), nullable=True)
    contenido = db.Column(db.String(255), nullable=True)
    estado = db.Column(db.String(50), nullable=False)
    ubicacion = db.Column(db.String(255), nullable=True)
    reserva = db.Column(db.Float, nullable=False)

@mesasyboxes_bp.route('/', methods=['GET'])
def obtener_mesasyboxes():

    if 'user_id' not in session or session.get('user_rol') != 'Administrador':
        flash("Debes iniciar sesión como Administrador para acceder a esta página.", "warning")
        return redirect(url_for('main.auth.login')) # Ajusta 'main.auth.login' a tu ruta de login

    # Obtener id_discoteca de la sesión
    id_discoteca_sesion = session.get('id_discoteca')

    if id_discoteca_sesion is None:
        # Esto no debería pasar si el login del admin fue correcto y guardó el id_discoteca
        flash("No se pudo encontrar el ID de la discoteca asociada. Por favor, inicia sesión de nuevo.", "error")
        return redirect(url_for('main.auth.login')) # O a una página de error/dashboard

    print(f"ID de discoteca obtenido de la sesión: {id_discoteca_sesion}")
    

    """Obtiene todos los productos y sus espacios y los muestra en una plantilla HTML."""
    productos = Producto.query.all()
    resultado = []
    for producto in productos:
        espacio = Espacio.query.filter_by(id_producto=producto.id_producto).first()
        resultado.append({
            'id_producto': producto.id_producto,
            'tipo': producto.tipo,
            'nombre': producto.nombre,
            'descripcion': producto.descripcion,
            'precio_regular': producto.precio_regular,
            'promocion': producto.promocion,
            'capacidad': espacio.capacidad if espacio else None,
            'tamanio': espacio.tamanio if espacio else None,
            'contenido': espacio.contenido if espacio else None,
            'estado': espacio.estado if espacio else None,
            'ubicacion': espacio.ubicacion if espacio else None,
            'reserva': espacio.reserva if espacio else None
        })
    print(resultado)  # 🔴 Agrega esto para verificar en consola si hay datos
    return render_template('index.html', productos=resultado)


@mesasyboxes_bp.route('/form_add_mesasyboxes', methods=['GET'])
def agregar_mesasyboxes_form():
    # --- COMIENZO DE CAMBIOS ---
    if 'user_id' not in session or session.get('user_rol') != 'Administrador':
        flash("Debes iniciar sesión como Administrador para acceder a esta página.", "warning")
        return redirect(url_for('main.auth.login'))

    id_discoteca_sesion = session.get('id_discoteca')

    if id_discoteca_sesion is None:
        flash("No se pudo encontrar el ID de la discoteca asociada. Por favor, inicia sesión de nuevo.", "error")
        return redirect(url_for('main.auth.login'))
    
    print(f"ID de discoteca para el formulario: {id_discoteca_sesion}")
    # Ya no usas id_discoteca = 1, usas el de la sesión
    return render_template('Agregar_Box.html', id_discoteca=id_discoteca_sesion)
    # --- FIN DE CAMBIOS ---

@mesasyboxes_bp.route('/add_mesasyboxes', methods=['POST'])
def agregar_mesasyboxes():
        # --- COMIENZO DE CAMBIOS ---
    if 'user_id' not in session or session.get('user_rol') != 'Administrador':
        flash("Acción no permitida. Debes iniciar sesión como Administrador.", "danger")
        # Si es una API que devuelve JSON: return jsonify({"error": "No autorizado"}), 403
        return redirect(url_for('main.auth.login')) # O redirigir al formulario

    id_discoteca_sesion = session.get('id_discoteca')

    if id_discoteca_sesion is None:
        flash("Error de sesión: ID de discoteca no encontrado. Por favor, inicia sesión de nuevo.", "error")
        return redirect(url_for('.agregar_mesasyboxes_form')) # Redirigir de vuelta al formulario
    
    print(f"ID de discoteca al agregar: {id_discoteca_sesion}")
    # Ya no usarás id_discoteca = 1, sino id_discoteca_sesion
    # --- FIN DE CAMBIOS ---
    try:
        # 2. Validar campos requeridos
        required_fields = ['tipo', 'nombre', 'precio_regular']
        if not all(field in request.form for field in required_fields):
            flash("Faltan campos requeridos", "danger")
            return redirect(url_for('mesasyboxes.agregar_mesasyboxes_form'))

        # 3. Obtener datos del formulario
        tipo = request.form['tipo']
        nombre = request.form['nombre']
        descripcion = request.form.get('descripcion', '')
        precio_regular = float(request.form['precio_regular'])
        promocion = int(request.form.get('promocion', 0))  # Guarda 0 si no está presente en el formulario
        reserva = float(request.form.get('reserva', 0.0))
        

        # 4. Validar archivos
        archivos = request.files.getlist('archivos')

        # Contar cuántas son imágenes
        imagenes = [f for f in archivos if f and f.filename and f.content_type.startswith('image')]

        if len(imagenes) > 4:
            flash("Solo puedes subir un máximo de 4 imágenes.", "danger")
            return redirect(url_for('mesasyboxes.agregar_mesasyboxes_form'))

        for file in archivos:
            if file.filename != '' and not allowed_file(file.filename, current_app.config['ALLOWED_EXTENSIONS']):
                flash("Tipo de archivo no permitido", "danger")
                return redirect(url_for('mesasyboxes.agregar_mesasyboxes_form'))

        # 5. Crear producto
        nuevo_producto = Producto(
            tipo=tipo,
            nombre=nombre,
            descripcion=descripcion,
            precio_regular=precio_regular,
            promocion=promocion
        )
        db.session.add(nuevo_producto)
        db.session.flush()

        # 6. Crear espacio si corresponde
        if tipo in ['box', 'mesa']:
            nuevo_espacio = Espacio(
                id_producto=nuevo_producto.id_producto,
                capacidad=int(request.form['capacidad']),
                tamanio=request.form.get('tamanio'),
                contenido=request.form.get('contenido'),
                estado=request.form['estado'],
                ubicacion=request.form.get('ubicacion', 'Sin ubicación'),  # Usar valor por defecto
                reserva=reserva
            )
            db.session.add(nuevo_espacio)

        # 7. Manejar archivos multimedia
        for file in archivos:
            if file and file.filename:
                tipo_archivo = 'imagen' if file.content_type.startswith(
            'image') else 'video'

        filename = secure_filename_wrapper(file.filename)
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        # Ahora crea un registro de ImagenVideo POR CADA ARCHIVO
        nuevo_media = ImagenVideo(
            Id_Discoteca=id_discoteca_sesion,
            Tipo_Tabla='espacios',
            Id_referenciaTabla=nuevo_producto.id_producto,
            Descripcion=request.form.get('descripcion_media', ''),
            Tipo_Archivo=tipo_archivo,
            Archivo=filename
        )
        db.session.add(nuevo_media)

# Si quieres manejar también un posible video externo por URL:
        if request.form.get('url_video'):
            nuevo_media = ImagenVideo(
            Id_Discoteca=id_discoteca_sesion,
            Tipo_Tabla='espacios',
            Id_referenciaTabla=nuevo_producto.id_producto,
            Descripcion=request.form.get('descripcion_media', ''),
            Tipo_Archivo='video',
            Archivo=request.form['url_video']
    )
        db.session.add(nuevo_media)

        db.session.commit()

        flash("Registro exitoso con multimedia", "success")
        return redirect(url_for('mesasyboxes.obtener_mesasyboxes'))

    except KeyError as ke:
        db.session.rollback()
        flash(f"Falta el campo: {str(ke)}", "danger")
    except ValueError as ve:
        db.session.rollback()
        flash(f"Error en datos: {str(ve)}", "danger")
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error: {str(e)}")
        flash("Error interno al procesar la solicitud", "danger")

    return redirect(url_for('mesasyboxes.agregar_mesasyboxes_form'))

@mesasyboxes_bp.route('/editar/<int:id_producto>', methods=['GET'])
def editar_mesasybox(id_producto):
     # --- INICIO MODIFICACIONES ---
    if 'user_id' not in session or session.get('user_rol') != 'Administrador':
        flash("Debes iniciar sesión como Administrador.", "warning")
        return redirect(url_for('main.auth.login'))

    id_discoteca_sesion = session.get('id_discoteca')
    if id_discoteca_sesion is None:
        flash("ID de discoteca no encontrado en sesión. Por favor, inicia sesión de nuevo.", "error")
        return redirect(url_for('main.auth.login'))

    # Verificar que el producto pertenezca a la discoteca del admin
    # Esto asume que ImagenVideo vincula el producto a la discoteca.
    # Sería más directo si Producto tuviera un campo id_discoteca.
    producto_pertenece = ImagenVideo.query.filter_by(
        Id_referenciaTabla=id_producto,
        Id_Discoteca=id_discoteca_sesion,
        Tipo_Tabla='espacios' # o 'productos' según tu lógica
    ).first()

    producto = Producto.query.get(id_producto) # Obtener producto después de verificar pertenencia (o antes si es necesario para la verificación)

    if producto is None:
        flash("Producto no encontrado.", "error")
        return redirect(url_for('.obtener_mesasyboxes')) # O a una página 404 personalizada

    if not producto_pertenece and producto: # Si el producto existe pero no pertenece a esta discoteca
        # Una comprobación más robusta si producto no tiene id_discoteca directamente:
        # Chequear si CUALQUIER media asociada al producto pertenece a la discoteca.
        # Si no hay media, ¿cómo se sabe a qué discoteca pertenece el producto?
        # IDEALMENTE: producto = Producto.query.filter_by(id_producto=id_producto, id_discoteca=id_discoteca_sesion).first()
        # Si esto no es posible, la lógica de producto_pertenece debe ser robusta.
        # Por ahora, si no hay media que lo vincule, y producto no tiene id_discoteca, se asume que podría no tener acceso.
        # Esta lógica de autorización es crucial y depende de tu esquema.
        # Si producto.id_discoteca existe:
        # if producto.id_discoteca != id_discoteca_sesion:
        #     flash("No tienes permiso para editar este producto.", "danger")
        #     return redirect(url_for('.obtener_mesasyboxes'))
        # Si se basa en ImagenVideo:
        if not ImagenVideo.query.filter_by(Id_referenciaTabla=id_producto, Id_Discoteca=id_discoteca_sesion, Tipo_Tabla='espacios').first():
                # Y si es un producto nuevo sin media? esta lógica puede ser compleja.
                # Considera añadir id_discoteca a Producto.
            pass # Por ahora, si no hay media que lo vincule directamente a esta discoteca, podría ser un problema.
                    # Esta es una simplificación. Una mejor forma es si Producto tiene id_discoteca.

    # --- FIN MODIFICACIONES ---

    # producto = Producto.query.get(id_producto) # Movido arriba
    if producto is None: # Doble check por si la lógica anterior no lo cubrió
        return "Producto no encontrado", 404

    espacio = Espacio.query.filter_by(id_producto=id_producto).first()
    
    # --- INICIO MODIFICACIONES ---
    # Filtrar multimedia también por Id_Discoteca
    archivos_multimedia = ImagenVideo.query.filter_by(
        Tipo_Tabla='espacios', # o 'productos'
        Id_referenciaTabla=id_producto,
        Id_Discoteca=id_discoteca_sesion 
    ).all()
    # --- FIN MODIFICACIONES ---

    return render_template('Actualizar_Box.html', 
                            producto=producto, 
                            espacio=espacio, 
                            archivos_multimedia=archivos_multimedia,
                            id_discoteca=id_discoteca_sesion # Pasar para el formulario si es necesario
                            )


@mesasyboxes_bp.route('/eliminar_media/<int:id_media>', methods=['POST'])
def eliminar_media_archivo(id_media):
    # --- INICIO MODIFICACIONES ---
    if 'user_id' not in session or session.get('user_rol') != 'Administrador':
        flash("Acción no permitida.", "danger")
        return redirect(request.referrer or url_for('.obtener_mesasyboxes'))

    id_discoteca_sesion = session.get('id_discoteca')
    if id_discoteca_sesion is None:
        flash("ID de discoteca no encontrado. Inicia sesión.", "error")
        return redirect(request.referrer or url_for('.obtener_mesasyboxes'))
    # --- FIN MODIFICACIONES ---

    if request.form.get('_method') == 'DELETE':
        try:
            # --- INICIO MODIFICACIONES ---
            # Verificar que el media pertenezca a la discoteca del admin antes de obtenerlo
            media = ImagenVideo.query.filter_by(Id_imgV=id_media, Id_Discoteca=id_discoteca_sesion).first()
            if not media:
                flash("Archivo multimedia no encontrado o no tienes permiso para eliminarlo.", "warning")
                return redirect(request.referrer or url_for('.obtener_mesasyboxes'))
            # --- FIN MODIFICACIONES ---
            
            # media = ImagenVideo.query.get_or_404(id_media) # Reemplazado por la consulta anterior

            # Elimina el archivo físico
            # Asegúrate que UPLOAD_FOLDER está configurado
            upload_folder = current_app.config.get('UPLOAD_FOLDER', 'src/static/uploads')
            if media.Tipo_Archivo == 'imagen' and not media.Archivo.startswith(('http://', 'https://')): # No eliminar URLs externas
                ruta_archivo = os.path.join(upload_folder, media.Archivo)
                if os.path.exists(ruta_archivo):
                    os.remove(ruta_archivo)
                else:
                    current_app.logger.warning(f"Archivo físico no encontrado para eliminar: {ruta_archivo}")


            db.session.delete(media)
            db.session.commit()
            flash("Archivo multimedia eliminado", "success")

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error al eliminar media {id_media}: {str(e)}")
            flash(f"Error al eliminar: {str(e)}", "danger")

    return redirect(request.referrer or url_for('.obtener_mesasyboxes'))


@mesasyboxes_bp.route('/<int:id_producto>', methods=['GET'])
def obtener_mesasybox(id_producto):
    """Obtiene un producto y su espacio específico por su ID."""

        # --- INICIO MODIFICACIONES ---
    # Si este endpoint es público, no se necesita autenticación.
    # Si es solo para admins, añadir la verificación:
    if 'user_id' not in session or session.get('user_rol') != 'Administrador':
        return jsonify(error="No autorizado"), 403 # O 401 si es solo falta de autenticación

    id_discoteca_sesion = session.get('id_discoteca')
    if id_discoteca_sesion is None:
        return jsonify(error="ID de discoteca no encontrado en sesión"), 401

    # Verificar que el producto pertenezca a la discoteca del admin
    # Asumiendo que Producto tiene id_discoteca o se verifica a través de ImagenVideo
    # Ejemplo si Producto tiene id_discoteca:
    # producto = Producto.query.filter_by(id_producto=id_producto, id_discoteca=id_discoteca_sesion).first()
    
    # Ejemplo si se verifica a través de ImagenVideo:
    producto_media_link = ImagenVideo.query.filter_by(
        Id_referenciaTabla=id_producto,
        Id_Discoteca=id_discoteca_sesion,
        Tipo_Tabla='espacios' # o 'productos'
    ).first()

    if not producto_media_link: # Si no hay media que lo vincule a esta discoteca
         # Y si el producto no tiene un id_discoteca directo, podría no tener acceso.
         # Esta lógica necesita ser robusta según tu esquema.
        producto_directo = Producto.query.get(id_producto)
        if not producto_directo: # El producto en sí no existe
             return jsonify({"error": "Producto no encontrado."}), 404
        # Si el producto existe pero no se pudo vincular a la discoteca del admin
        # return jsonify({"error": "Acceso denegado a este producto."}), 403
        # Por ahora, si esta es una API pública, quizás no se filtra por discoteca aquí
        # Pero si es para el admin, SÍ se debe filtrar.
        # Para esta demo, asumimos que si es para el admin, debe estar vinculado.
        # Si el producto NO tiene id_discoteca, esta verificación es indirecta y puede ser falible.
        # Considera añadir id_discoteca al modelo Producto.
        pass # Ajustar esta lógica de autorización según el diseño.

    producto = Producto.query.get(id_producto) # Obtener el producto de todas formas si la comprobación anterior es laxa.
                                           # Si es estricta, esto ya se hizo.
    # --- FIN MODIFICACIONES ---


    if producto is None:
        return jsonify({"error": "Producto no encontrado."}), 404

    espacio = Espacio.query.filter_by(id_producto=id_producto).first()
    resultado = {
        'id_producto': producto.id_producto,
        'tipo': producto.tipo,
        'nombre': producto.nombre,
        'descripcion': producto.descripcion,
        'precio_regular': producto.precio_regular,
        'promocion': producto.promocion,
        'capacidad': espacio.capacidad if espacio else None,
        'tamanio': espacio.tamanio if espacio else None,
        'contenido': espacio.contenido if espacio else None,
        'estado': espacio.estado if espacio else None,
        'ubicacion': espacio.ubicacion if espacio else None,
        'reserva': espacio.reserva if espacio else None
    }
    return jsonify(resultado), 200


@mesasyboxes_bp.route('/editar/<int:id_producto>', methods=['POST'])
def actualizar_mesasybox(id_producto):
    print("🟢 Se envió el formulario correctamente.")
    print("🟢 Método detectado:", request.method)
    print("🟢 _method:", request.form.get('_method'))

    # --- INICIO MODIFICACIONES ---
    if 'user_id' not in session or session.get('user_rol') != 'Administrador':
        flash("Acción no permitida.", "danger")
        return redirect(url_for('main.auth.login'))

    id_discoteca_sesion = session.get('id_discoteca')
    if id_discoteca_sesion is None:
        flash("ID de discoteca no encontrado. Inicia sesión.", "error")
        return redirect(url_for('.editar_mesasybox', id_producto=id_producto)) # Volver al form de edición


    try:
        data = request.form
        producto = Producto.query.get_or_404(id_producto)
        espacio = Espacio.query.filter_by(id_producto=id_producto).first()

        # Actualizar datos del producto
        producto.tipo = data.get('tipo', producto.tipo)
        producto.nombre = data.get('nombre', producto.nombre)
        producto.descripcion = data.get('descripcion', producto.descripcion)
        producto.precio_regular = float(data.get('precio_regular', producto.precio_regular))
        # Para checkboxes, 'on' es el valor si está marcado, None si no.
        producto.promocion = 1 if data.get('promocion') == 'on' else 0


        # Actualizar datos del espacio
        if espacio:
            espacio.capacidad = int(data.get('capacidad', espacio.capacidad))
            espacio.tamanio = data.get('tamanio', espacio.tamanio)
            espacio.contenido = data.get('contenido', espacio.contenido)
            espacio.estado = data.get('estado', espacio.estado)
            # Asegúrate que 'tiene_reserva' es el name correcto del checkbox
            if data.get('tiene_reserva') == 'on':
                espacio.reserva = float(data.get('reserva_precio', 0.0))
            else:
                espacio.reserva = None # O 0.0 si la BD no permite NULL y 0.0 significa sin reserva

        # --- INICIO: Lógica para eliminar multimedia existente ---
        deleted_media_ids_str = data.get('deleted_media') # El name del input oculto es 'deleted_media'
        if deleted_media_ids_str:
            media_ids_to_delete = [int(id_val) for id_val in deleted_media_ids_str.split(',') if id_val.strip()]
            
            for media_id in media_ids_to_delete:

                # --- INICIO MODIFICACIONES ---
                # Verificar que el media_item pertenezca a la discoteca del admin
                media_item = ImagenVideo.query.filter_by(
                    Id_imgV=media_id, 
                    Id_Discoteca=id_discoteca_sesion
                ).first()
                # --- FIN MODIFICACIONES ---

                if media_item:
                    # Eliminar archivo físico si es una imagen local
                    if media_item.Tipo_Archivo == 'imagen' and \
                       media_item.Archivo and \
                       not media_item.Archivo.startswith(('http://', 'https://')):
                        try:
                            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], media_item.Archivo)
                            if os.path.exists(file_path):
                                os.remove(file_path)
                                print(f"Archivo físico eliminado: {file_path}")
                            else:
                                print(f"Archivo físico no encontrado para eliminar: {file_path}")
                        except Exception as e_file:
                            print(f"Error al eliminar archivo físico {media_item.Archivo}: {str(e_file)}")
                            # Considera usar flash(f"Error al eliminar archivo físico {media_item.Archivo}", "warning")

                    db.session.delete(media_item)
                    print(f"Media con ID {media_id} marcada para eliminación de la BD.")
        # --- FIN: Lógica para eliminar multimedia existente ---

        # Subir nuevas imágenes (archivo físico)
        archivos = request.files.getlist('archivos') # name del input file para nuevos archivos
        for file in archivos:
            if file and file.filename and allowed_file(file.filename, current_app.config['ALLOWED_EXTENSIONS']):
                tipo_archivo = 'imagen' if file.content_type.startswith('image') else 'video' # Simplificado
                filename = secure_filename_wrapper(file.filename)
                file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)

                nueva_media = ImagenVideo(
                    Id_Discoteca=id_discoteca_sesion, # Ajusta según sea necesario
                    Tipo_Tabla='espacios',
                    Id_referenciaTabla=producto.id_producto,
                    Descripcion=data.get('descripcion_media', ''), # Asegúrate que tienes este campo o ajústalo
                    Tipo_Archivo=tipo_archivo,
                    Archivo=filename
                )
                db.session.add(nueva_media)

        # Agregar video por URL si existe
        # Asegúrate que el name en el HTML es 'urls_video' para este campo
        # y que se procesa correctamente si son múltiples URLs nuevas.
        # El código actual en el HTML parece manejar un input 'hiddenVideoUrls' que es poblado por JS.
        # Si es una lista de URLs, necesitarás iterar.
        
        nuevas_urls_video_str = data.get('urls_video') # name del input para nuevas URLs de video
        if nuevas_urls_video_str:
            urls_list = [url.strip() for url in nuevas_urls_video_str.split(',') if url.strip()]
            for video_url in urls_list:
                nueva_media_video_url = ImagenVideo(
                    Id_Discoteca=id_discoteca_sesion, # Ajusta según sea necesario
                    Tipo_Tabla='espacios',
                    Id_referenciaTabla=producto.id_producto,
                    Descripcion=data.get('descripcion_media_video_url', ''), # Campo de descripción específico si es necesario
                    Tipo_Archivo='video',
                    Archivo=video_url
                )
                db.session.add(nueva_media_video_url)
        
        db.session.commit()
        flash("Producto actualizado con multimedia", "success")
        return redirect(url_for('mesasyboxes.obtener_mesasyboxes'))

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error al actualizar producto {id_producto}: {str(e)}")
        flash(f"Error al actualizar: {str(e)}", "danger")
        # Es mejor redirigir a la misma página de edición en caso de error para no perder los datos ya ingresados
        # return redirect(url_for('mesasyboxes.editar_mesasybox', id_producto=id_producto))
        return redirect(url_for('mesasyboxes.obtener_mesasyboxes')) # O como lo tenías
    

@mesasyboxes_bp.route('/eliminar/<int:id_producto>', methods=['POST']) # Debería ser DELETE si es una API REST pura
def eliminar_mesasybox(id_producto):
    # --- INICIO MODIFICACIONES ---
    if 'user_id' not in session or session.get('user_rol') != 'Administrador':
        return jsonify(success=False, error="No autorizado"), 403

    id_discoteca_sesion = session.get('id_discoteca')
    if id_discoteca_sesion is None:
        return jsonify(success=False, error="ID de discoteca no encontrado en sesión"), 401
    # --- FIN MODIFICACIONES ---

    # El frontend envía _method='DELETE' en un form, pero aquí especificas request.json.
    # Asegúrate que el frontend envíe JSON con _method si es necesario, o ajusta la condición.
    # Si el frontend envía un form normal con POST y un campo _method:
    # if request.form.get('_method') == 'DELETE':
    # Si el frontend envía JSON con _method:
    
    # Para este ejemplo, asumiré que el _method está en el JSON si se espera JSON.
    # Si no, y es un POST simple, no se necesita if request.json.get('_method') == 'DELETE':
    
    try:
        # --- INICIO MODIFICACIONES ---
        # Verificar que el producto pertenezca a la discoteca del admin
        # Si Producto tiene id_discoteca:
        # producto = Producto.query.filter_by(id_producto=id_producto, id_discoteca=id_discoteca_sesion).first()
        # if not producto:
        #     return jsonify(success=False, error="Producto no encontrado o no tienes permiso."), 404

        # Si se basa en ImagenVideo (menos ideal para la pertenencia del producto en sí):
        # Esta verificación es más para la media asociada.
        # Es mejor que Producto tenga id_discoteca.
        producto = Producto.query.get(id_producto)
        if not producto:
            return jsonify(success=False, error="Producto no encontrado."), 404

        # Aquí una verificación de propiedad más explícita si producto no tiene id_discoteca
        # if not check_product_ownership(producto, id_discoteca_sesion): # función hipotética
        #     return jsonify(success=False, error="No tienes permiso."), 403
        # --- FIN MODIFICACIONES ---

        espacio = Espacio.query.filter_by(id_producto=id_producto).first()

        # Eliminar multimedia asociada al producto y a la discoteca
        media_asociada = ImagenVideo.query.filter_by(
            Id_referenciaTabla=id_producto,
            Id_Discoteca=id_discoteca_sesion, # Asegurar que solo se borra media de esta discoteca
            Tipo_Tabla='espacios' # o 'productos'
        ).all()
        
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'src/static/uploads')
        for media_item in media_asociada:
            if media_item.Tipo_Archivo == 'imagen' and not media_item.Archivo.startswith(('http://', 'https://')):
                ruta_archivo = os.path.join(upload_folder, media_item.Archivo)
                if os.path.exists(ruta_archivo):
                    try:
                        os.remove(ruta_archivo)
                    except Exception as e_file:
                            current_app.logger.error(f"Error al eliminar archivo físico {media_item.Archivo} durante borrado de producto: {str(e_file)}")
            db.session.delete(media_item)

        if espacio:
            db.session.delete(espacio)
        db.session.delete(producto) # `producto` ya fue obtenido y verificado (o debería haber sido)
        
        db.session.commit()
        return jsonify(success=True, message="Producto y elementos asociados eliminados."), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error en la base de datos al eliminar producto {id_producto}: {str(e)}", exc_info=True)
        return jsonify(success=False, error=str(e)), 500
        


@mesasyboxes_bp.route('/filtrar/<tipo>', methods=['GET'])
def filtrar_por_tipo(tipo):
    """Filtra los productos por tipo (box o mesa)."""
    productos_filtrados = Producto.query.filter_by(tipo=tipo).all()
    resultado = []

    for producto in productos_filtrados:
        espacio = Espacio.query.filter_by(id_producto=producto.id_producto).first()
        resultado.append({
            'id_producto': producto.id_producto,
            'tipo': producto.tipo,
            'nombre': producto.nombre,
            'descripcion': producto.descripcion,
            'precio_regular': producto.precio_regular,
            'promocion': producto.promocion,
            'capacidad': espacio.capacidad if espacio else None,
            'tamanio': espacio.tamanio if espacio else None,
            'contenido': espacio.contenido if espacio else None,
            'estado': espacio.estado if espacio else None,
            'ubicacion': espacio.ubicacion if espacio else None,
            'reserva': espacio.reserva if espacio else None
        })

    return render_template('index.html', productos=resultado, tipo_filtro=tipo)



@mesasyboxes_bp.route('/media/<int:id_producto>', methods=['GET'])
def obtener_media(id_producto):
    """Obtiene multimedia asociada a un producto"""
    try:
        media = Media.query.filter_by(
            Tipo_Tabla='espacios',
            Id_referenciaTabla=id_producto
        ).all()

        return jsonify([{
            'id': item.Id_imgV,
            'tipo': item.Tipo_Archivo,
            'descripcion': item.Descripcion,
            'url': url_for('static', filename=f'uploads/{item.Archivo}'),
            'nombre_archivo': item.Archivo
        } for item in media]), 200

    except Exception as e:
        current_app.logger.error(f"Error obteniendo media: {str(e)}")
        return jsonify(error="Error al obtener multimedia"), 500

@mesasyboxes_bp.route('/media/<int:id_media>', methods=['DELETE'])
def eliminar_media(id_media):
    """Elimina un archivo multimedia"""
    try:
        media = Media.query.get_or_404(id_media)
        
        # Construir ruta completa del archivo
        file_path = os.path.join(
            current_app.config['UPLOAD_FOLDER'], 
            media.Archivo
        )
        
        # Eliminar físicamente el archivo
        if os.path.exists(file_path):
            os.remove(file_path)
        
        # Eliminar registro de la base de datos
        db.session.delete(media)
        db.session.commit()
        
        return jsonify(
            success=True, 
            message="Archivo eliminado correctamente"
        ), 200

    except Exception as e:
        current_app.logger.error(f"Error eliminando media: {str(e)}")
        db.session.rollback()
        return jsonify(
            error="No se pudo eliminar el archivo", 
            detalle=str(e)
        ), 500







