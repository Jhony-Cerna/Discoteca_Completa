document.addEventListener('DOMContentLoaded', function() {
    const reservaCheckbox = document.getElementById('reserva_checkbox');
    const reservaField = document.getElementById('reserva_field');
    const reservaInput = document.getElementById('reserva_precio');

    reservaCheckbox.addEventListener('change', function() {
        reservaField.style.display = this.checked ? 'block' : 'none';
        reservaInput.required = this.checked;
        if (!this.checked) reservaInput.value = ''; // Limpiar campo al desactivar
    });
});