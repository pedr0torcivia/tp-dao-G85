# Reglas operativas de EntreLibros

## Alcance

El sistema administra sedes, socios, libros, copias físicas, solicitudes locales e interbibliotecarias, reservas, préstamos, devoluciones y remitos. Incluye cinco reportes y despliegue con Docker Compose. Notificaciones, recomendaciones, multas y códigos de barras quedan fuera de esta entrega.

## Catálogo y disponibilidad

Un libro contiene autor como texto. Un ejemplar representa una copia identificada por un código único, con sede propietaria y ubicación actual independientes. El ISBN es único cuando está informado. Sin ISBN, título, autor, editorial y edición identifican una edición sin distinguir mayúsculas; los servicios recortan espacios externos. La migración `catalogo/0003` impone esa unicidad en la base.

Solo se presta material apto y disponible de una sede activa a un socio habilitado. La sede propietaria debe coincidir con el origen de la solicitud. Una asignación toma bloqueos de fila para impedir adjudicar la misma copia a dos solicitudes simultáneas.

## Préstamos y devolución

La solicitud local tiene origen y destino iguales. La interbibliotecaria usa sedes diferentes y requiere un remito recibido antes de entregar. La entrega al socio inicia el préstamo; su vencimiento es posterior a la entrega. Un préstamo admite una devolución, cuya fecha no puede preceder a la entrega.

La devolución se registra en la sede donde se entregó el material. La copia conserva su ubicación y queda EN_REVISION con condición APTO o NO_APTO. Para recuperar disponibilidad requiere revisión, condición apta y presencia en su sede propietaria activa.

## Retorno entre sedes

Una copia devuelta fuera de su sede propietaria puede agregarse a un remito cuyo origen sea su ubicación actual y cuyo destino sea su propietaria. Este retorno requiere EN_REVISION y no crea otra solicitud ni otro préstamo. También admite material NO_APTO para devolverlo a su propietaria sin habilitarlo.

El remito de retorno sigue las mismas transiciones e historial que el de ida. Al recibirlo, la copia queda EN_REVISION. Si se cancela antes de despachar, vuelve a revisión en la sede actual; no queda disponible fuera de su sede propietaria.

## Reservas

Una reserva refiere a socio, libro y sede de retiro activos. No se duplica una reserva vigente del mismo socio, libro y sede. La asignación es manual, con ejemplar de la sede de retiro y fecha límite futura. No se promete prioridad automática. La asignación crea una solicitud local lista para entrega; la entrega cumple la reserva.

Cancelar o expirar una reserva libera la copia y cancela su solicitud pendiente. `python manage.py expirar_reservas` procesa las vencidas. El programador del entorno puede ejecutar ese comando periódicamente; no hay un servicio de tareas obligatorio para esta entrega.

## Remitos

EN_PREPARACION permite agregar y quitar copias; no se empaqueta un remito vacío. La secuencia es EN_PREPARACION, EMPAQUETADO, EN_TRANSITO y RECIBIDO (o RECIBIDO_CON_INCIDENCIAS). Un remito empaquetado puede reabrirse. Solo se cancela antes del despacho. No se modifican sedes o número de un remito con copias asignadas; si no se indica número, se genera REM-año-número. Se recibe el conjunto completo indicando responsable y el resultado de cada copia: conforme, dañada (queda no apta y en revisión) o extraviada (se da de baja). Una solicitud cuya copia llega dañada o no llega vuelve a PENDIENTE para asignar otra.

Un préstamo no puede superar 60 días. Un socio con préstamos vencidos sin devolver no inicia solicitudes ni reservas, no recibe copias asignadas y no retira material nuevo. Cada día de atraso genera una multa de $ 150, visible en el préstamo, en la ficha del socio y en el reporte de vencidos.

La recepción o devolución de operaciones iniciadas sigue permitida si una sede se da de baja; no se inician nuevas solicitudes, reservas o envíos desde o hacia una sede de baja. La recepción conserva ubicación, condición e historial. Los cambios de estados y disponibilidad de cada comando se confirman en una transacción.

## Reportes

Todos los endpoints de reportes exigen Desde y Hasta inclusivos, válidos y en orden. RP01 selecciona entregas del período y muestra préstamos abiertos al cierre de la fecha de corte y vencidos antes de ese día, con días calendario de atraso y filtro por sede de entrega. Una devolución posterior al corte no elimina el préstamo de un informe histórico.

RP02 cuenta solicitudes interbibliotecarias por libro y sede solicitante dentro de un rango; excluye rechazadas y canceladas. RP03 cuenta despachos por trayecto y calcula el promedio despacho-recepción solo para recibidos. RP04 selecciona los ejemplares por fecha de alta dentro del rango y refleja su estado actual por libro y sede propietaria; no reconstruye el stock histórico; solo cuenta como disponible una copia apta, en su propietaria activa y con estado DISPONIBLE.

## Acceso de la entrega

El formulario valida usuario y contraseña en Django. Solo ingresa personal activo (is_staff); la API exige autenticación y ese permiso para todas las operaciones de negocio. La sesión dura hasta ocho horas, se conserva al recargar y se invalida en el servidor al cerrar sesión. Las escrituras y el inicio de sesión requieren protección CSRF. Las pantallas internas redirigen al acceso sin una sesión válida.

La sede de trabajo organiza la atención y no restringe permisos sobre la red. No hay cuentas públicas de socios ni roles separados para biblioteca y logística. Un superusuario administra las cuentas desde Django Admin. La carga de demostración crea biblioteca / demo si esa cuenta no existe, sin restablecer claves ni permisos existentes. Consultar `acceso.md` para la administración y configuración.


RP05 comprueba las escrituras exitosas de la API: fecha real de operación, usuario, entidad, identificador y cambios antes/después. Su registro y la operación de negocio se confirman en la misma transacción. Lecturas e intentos fallidos no se cuentan como cambios. Los cambios directos por SQL o Django Admin no se auditan por este mecanismo. El filtro de sede aplica a registros asociados a esa sede; libros y socios globales se consultan sin ese filtro.

El catálogo de exposición se prepara con `preparar_exposicion`. Repetirlo conserva el escenario existente. `--reiniciar` reemplaza los datos de biblioteca y bitácora y conserva cuentas y sesiones; es una acción explícita para volver a los casos iniciales.
