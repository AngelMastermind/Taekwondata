document.addEventListener('DOMContentLoaded', () => {
    const themeToggle = document.getElementById('theme-toggle');
    const htmlElement = document.documentElement;
    const sidebarToggle = document.getElementById('sidebar-toggle');
    const sidebar = document.querySelector('.sidebar');
    const themeText = document.querySelector('.theme-text');
    const themeIcon = themeToggle.querySelector('i');

    // Cargar el tema guardado en localStorage o usar 'dark' por defecto
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'light') {
        htmlElement.classList.add('light-theme');
        themeIcon.classList.remove('fa-sun');
        themeIcon.classList.add('fa-moon');
        if (themeText) themeText.textContent = 'Cambiar a Tema Oscuro';
    } else {
        htmlElement.classList.remove('light-theme');
        themeIcon.classList.remove('fa-moon');
        themeIcon.classList.add('fa-sun');
        if (themeText) themeText.textContent = 'Cambiar a Tema Claro';
    }

    // Actualiza el texto y el icono del botón al cargar la página
    function updateThemeToggleButton() {
        if (htmlElement.classList.contains('light-theme')) {
            themeIcon.classList.remove('fa-sun');
            themeIcon.classList.add('fa-moon');
            if (themeText) themeText.textContent = 'Cambiar a Tema Oscuro';
        } else {
            themeIcon.classList.remove('fa-moon');
            themeIcon.classList.add('fa-sun');
            if (themeText) themeText.textContent = 'Cambiar a Tema Claro';
        }
    }

    // Ejecutar al cargar la página (para el valor inicial)
    updateThemeToggleButton();

    themeToggle.addEventListener('click', () => {
        if (htmlElement.classList.contains('light-theme')) {
            htmlElement.classList.remove('light-theme');
            localStorage.setItem('theme', 'dark');
        } else {
            htmlElement.classList.add('light-theme');
            localStorage.setItem('theme', 'light');
        }
        updateThemeToggleButton(); // Actualizar texto e icono después del cambio
    });

    // Lógica para mostrar/ocultar el campo de grado según el rol
    const rolSelect = document.getElementById('rol_select'); // ID del select en el formulario de registro
    const gradoFieldGroup = document.getElementById('grado-field-group'); // Contenedor del campo de grado

    function toggleGradoField() {
        if (rolSelect && gradoFieldGroup) {
            if (rolSelect.value === 'Estudiante') {
                gradoFieldGroup.style.display = 'block';
            } else {
                gradoFieldGroup.style.display = 'none';
            }
        }
    }

    // Ejecutar al cargar la página (para el valor inicial)
    toggleGradoField();
    if (rolSelect) {
        rolSelect.addEventListener('change', toggleGradoField);
    }

    // Lógica para colapsar/expandir el sidebar
    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', () => {
            sidebar.classList.toggle('collapsed');
        });
    }
});
