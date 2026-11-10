# Guion de demostración del grupo 85

La guía principal, con pasos de pantalla y respuestas para la defensa, está en [Guía de exposición](guia-exposicion.md) y [PDF de siete páginas](Guia-exposicion-grupo-85.pdf).

## Preparación

Con Docker Desktop abierto, ejecutar `docker compose up -d --build --wait` y `docker compose exec backend python manage.py preparar_exposicion`. El comando conserva un escenario ya preparado. Para reemplazarlo de forma explícita después de un ensayo, agregar `--reiniciar`; se borran los datos de biblioteca y bitácora, conservando las cuentas.

Ingresar en http://localhost:5173 con **biblioteca / demo**. El catálogo contiene 44 títulos y 132 copias, con sus portadas. Ver [Catálogo y casos](catalogo-exposicion.md).

## Demostración de 15 minutos

1. Distinguir obra de ejemplar y explicar el problema de la red.
2. Alta de DEFENSA-001 sobre Batman: Year One en Central; consultar y recargar.
3. Editar su condición a NO_APTO y darlo de baja. Explicar la baja lógica.
4. Mostrar las diferencias en disponibilidad y los tres eventos de la bitácora ABMC.
5. Aplicar Desde y Hasta, imprimir/guardar PDF del reporte y abrirlo por pantalla.
6. Recorrer un préstamo, una devolución y el historial de un remito.
7. Explicar State y Strategy con las operaciones permitidas y el circuito local/interbibliotecario.

## Referencia previa a los cambios

Rango 01/10/2026–31/10/2026, todas las sedes: RP01 dos vencidos (19 y 7 días de atraso); RP02 cuatro pedidos válidos; RP03 tres despachos y dos recibidos, con promedio de dos días por trayecto; RP04 116 de 132 copias disponibles. RP05 filtra fecha real de operación: para el ensayo usar el día actual, no solamente octubre.

Los documentos en [Reportes de referencia](reportes-referencia/) son fotografías de los datos al generarlos. RP05 incluye un ejemplo real de alta, modificación y baja de una copia adicional. El escenario se restableció después de generar ese ejemplo para entregar una base limpia.
