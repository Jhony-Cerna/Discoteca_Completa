document.addEventListener('DOMContentLoaded', function() {
    const reservaCheckbox = document.getElementById('reserva_checkbox');
    const reservaField = document.getElementById('reserva_field');
    const reservaInput = document.getElementById('reserva');

    // Mostrar u ocultar el campo de reserva al cargar la página
    if (reservaCheckbox && reservaField && reservaInput) {
        // Si ya hay un valor de reserva, mostrar el campo y marcar el checkbox
        if (reservaInput.value > 0) {
            reservaCheckbox.checked = true;
            reservaField.style.display = 'block';
        }

        // Mostrar u ocultar el campo de reserva cuando cambie el estado del checkbox
        reservaCheckbox.addEventListener('change', function() {
            reservaField.style.display = this.checked ? 'block' : 'none';
            if (!this.checked) {
                reservaInput.value = ''; // Limpiar el campo si el checkbox se desactiva
            }
        });
    }
});