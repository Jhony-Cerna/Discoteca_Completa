// Función para mostrar la vista previa de la imagen
function setupImagePreview(inputId, previewId, initialImageUrl = null) {
    const input = document.getElementById(inputId);
    const preview = document.getElementById(previewId);

    if (input && preview) {
        // Mostrar la imagen actual (si existe) al cargar la página
        if (initialImageUrl) {
            preview.innerHTML = `<img src="${initialImageUrl}" alt="Imagen actual">`;
        }

        // Actualizar la vista previa cuando el usuario seleccione una nueva imagen
        input.addEventListener('change', function(event) {
            const file = event.target.files[0]; // Obtener el archivo seleccionado

            if (file) {
                const reader = new FileReader(); // Crear un FileReader para leer la imagen

                reader.onload = function(e) {
                    // Crear una imagen y establecer su src como la URL del archivo
                    preview.innerHTML = `<img src="${e.target.result}" alt="Vista previa de la imagen">`;
                };

                reader.readAsDataURL(file); // Leer el archivo como una URL
            } else {
                // Si no se selecciona una imagen, mostrar la imagen actual (si existe)
                preview.innerHTML = initialImageUrl
                    ? `<img src="${initialImageUrl}" alt="Imagen actual">`
                    : '<span>Vista previa de la imagen</span>';
            }
        });
    }
}

// Configurar la vista previa para el formulario de actualizar
document.addEventListener('DOMContentLoaded', function() {
    // Obtener la URL de la imagen actual (si existe)
    const initialImageUrl = document.getElementById('image-preview').querySelector('img')?.src;

    // Configurar la vista previa
    setupImagePreview('ubicacion', 'image-preview', initialImageUrl);
});