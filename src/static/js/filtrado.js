function filtrarProductos(tipo) {
    fetch(`/filtrar/${tipo}`)
        .then(response => response.json())
        .then(data => {
            let tabla = document.querySelector("tbody");
            tabla.innerHTML = ""; // Limpiar la tabla antes de agregar los nuevos datos

            data.forEach(producto => {
                let fila = `
                    <tr>
                        <td>${producto.tipo}</td>
                        <td>${producto.nombre}</td>
                        <td>${producto.descripcion}</td>
                        <td>$${producto.precio_regular}</td>
                        <td>${producto.promocion ? 'Sí' : 'No'}</td>
                        <td>${producto.capacidad || 'N/A'}</td>
                        <td>${producto.contenido || 'N/A'}</td>
                        <td>${producto.estado}</td>
                        <td>
                            ${producto.ubicacion ? `<img src="${producto.ubicacion}" alt="Imagen de ubicación">` : 'Sin ubicación'}
                        </td>
                        <td>
                            <a href="/edit/${producto.id_producto}">Editar</a> |
                            <a href="#" onclick="confirmarEliminacion('${producto.id_producto}')">Eliminar</a>
                        </td>
                    </tr>
                `;
                tabla.innerHTML += fila;
            });
        })
        .catch(error => console.error("Error en la petición:", error));
}
