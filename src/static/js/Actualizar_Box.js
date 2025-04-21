document.addEventListener('DOMContentLoaded', () => {
    const form = document.querySelector('#form-actualizar');

    form.addEventListener('submit', function(event) {
        event.preventDefault(); // Evita el envío tradicional del formulario
        
        const formData = new FormData(form);
        const data = {};

        // Convertir los datos del formulario a JSON
        formData.forEach((value, key) => {
            data[key] = value;
        });

        // Asegúrate de que `id_producto` está en el formulario
        const idProducto = data.id_producto || data.id;

        // Aquí agregamos el console.log para verificar que se está capturando el ID
        console.log('ID Producto:', idProducto);

        fetch(`/mesas_y_cajas/${idProducto}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        })
        .then(response => {
            if (response.ok) {
                alert('Producto actualizado con éxito');
                window.location.href = '/'; // Redirige a la página principal o donde desees
            } else {
                response.json().then(errorData => {
                    console.error('Error en la actualización:', errorData);
                    alert('Error al actualizar: ' + (errorData.error || 'Error desconocido'));
                });
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error en la solicitud');
        });
    });
});
