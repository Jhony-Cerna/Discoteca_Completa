function confirmarEliminacion(url) {
    if (confirm('¿Estás seguro?')) {
        fetch(url, {
            method: 'POST', 
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': '{{ csrf_token() }}'  // Si usas CSRF
            },
            body: JSON.stringify({ _method: 'DELETE' })  // Enviar como POST pero con DELETE oculto
        })
        .then(response => {
            if (response.ok) {
                window.location.reload(); 
            } else {
                response.json().then(data => {
                    alert(`Error: ${data.error || 'Desconocido'}`);
                });
            }
        })
        .catch(error => console.error('Error:', error));
    }
}
