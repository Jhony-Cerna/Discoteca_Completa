function confirmarEliminacion(id) {
    if (confirm('¿Estás seguro de que deseas eliminar este registro?')) {
        // Si el usuario confirma, redirige a la ruta de eliminación
        window.location.href = `/delete/${id}`;
    }
}