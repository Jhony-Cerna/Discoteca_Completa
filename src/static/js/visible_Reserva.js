console.log("JS cargado correctamente");
console.log("Checkbox:", document.getElementById('reserva_checkbox'));
console.log("Input Reserva:", document.getElementById('reserva'));

document.addEventListener('DOMContentLoaded', function() {
    const reservaCheckbox = document.getElementById('reserva_checkbox');
    const reservaField = document.getElementById('reserva_field');
    const reservaInput = document.getElementById('reserva');

    // Comprobamos si hay un valor de reserva al cargar la página
    if (reservaInput && parseFloat(reservaInput.value) > 0) {
        reservaCheckbox.checked = true;
        reservaField.style.display = 'block';
    }

    // Mostrar u ocultar el campo de reserva cuando cambie el checkbox
    reservaCheckbox.addEventListener('change', function() {
        if (this.checked) {
            reservaField.style.display = 'block';
        } else {
            reservaField.style.display = 'none';
            reservaInput.value = ''; // Limpiar el campo si se desactiva
        }
    });
});
