# Integración de la entrega

La base integrada es `main` en `da48d34`. Contiene las cuatro ramas funcionales y la actualización final de circulación. El cierre se desarrolla en `integration/cierre-tp`.

Cambios del cierre:

- Autenticación de personal con sesiones, protección CSRF, rutas privadas y cierre de sesión.
- Contrato único de Libro con `autor` de texto; no existen tablas adicionales de autores.
- Frontend conectado a la API por defecto; errores del servidor visibles en los formularios.
- Cinco reportes con rango Desde/Hasta, CSV e impresión/PDF; bitácora transaccional para comprobar ABMC.
- Catálogo de exposición con 30 obras reales y 90 ejemplares, portadas locales y guía de defensa en PDF.
- Retorno de material desde la sede de entrega a la propietaria, conservando revisión e historial.
- Datos de demostración idempotentes y referencias de cálculo independientes.
- Pruebas de circuito completo y pruebas del navegador contra una API real.
- Comprobaciones de salud en Compose, script de arranque/reinicio y verificación continua.

Consultar `verificacion-entrega.md` para los resultados efectivamente ejecutados y las limitaciones del entorno. Los antiguos pendientes RP02, RP04, reservas y baja de ejemplares ya están implementados; no deben abrirse como funcionalidades faltantes.

Antes de entregar, revisar los cambios de esta rama y fusionarla a `main` mediante el procedimiento del grupo. Confirmar la fecha y el mecanismo de entrega de la cátedra.
