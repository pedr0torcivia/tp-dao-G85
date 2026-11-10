# Guía para presentar EntreLibros

Grupo 85 · Tema 1 Biblioteca · Preparación de la defensa

El objetivo es demostrar una operación completa y comprobar su resultado en la base y en un reporte. Mostrá el dato antes, ejecutá el cambio, consultalo otra vez y abrí el reporte con Desde y Hasta definidos. El catálogo contiene obras reales; los socios, sedes, inventario y movimientos son ficticios para la exposición.

## Cómo entrar y orientarte

Abrí http://localhost:5173/ y entrá con **biblioteca / demo**. El acceso se valida en Django. En la cabecera elegí Biblioteca Central. Las cuentas de personal pueden trabajar sobre toda la red; el selector de sede es el contexto de atención.

**Catálogo** muestra obras o ediciones. **Ejemplares** son las copias físicas, cada una con un inventario único. Una misma obra puede tener varias copias. La sede propietaria expresa pertenencia; la ubicación actual puede cambiar por un traslado.

**Solicitud** es el pedido; **préstamo** es la entrega efectiva al lector; **reserva** espera disponibilidad o retiro; **remito** documenta el transporte entre sedes. Transportar un libro todavía no inicia el plazo de lectura.

## Escenario inicial que vas a encontrar

| Elemento | Preparado para mostrar |
|---|---|
| Catálogo | 30 títulos de Star Wars, Marvel y DC; 90 ejemplares |
| Disponibilidad | 83 disponibles, 2 prestados, 1 en tránsito, 1 listo para entrega, 2 en revisión y 1 de baja |
| Sedes | Biblioteca Central y Norte activas; Biblioteca Sur de baja |
| Socios | Ana, Bruno, Carla, Diego y Lucía habilitados; Tomás inhabilitado |
| Préstamos | Uno vencido, uno vigente y uno devuelto |
| Logística | ENV-2026-001 en tránsito; ENV-2026-002 y 003 recibidos |

## Orden recomendado para una exposición de 15 minutos

1. Explicar el problema y distinguir libro de ejemplar: 2 minutos.
2. Dar de alta, consultar, modificar y dar de baja una copia: 4 minutos.
3. Evidenciar esos cambios en RP04 y RP05, y abrir un documento del reporte: 3 minutos.
4. Mostrar un préstamo, una devolución y un remito con historial: 4 minutos.
5. Explicar State y Strategy y responder preguntas: 2 minutos.

Frase de apertura: “Nuestro sistema administra una red de bibliotecas. Separa la obra de sus copias físicas y controla cada préstamo y traslado para evitar prestar material ocupado, dañado o perteneciente a una sede incorrecta”.

<!-- page -->

# Demostración principal de ABMC

ABMC significa alta, baja, modificación y consulta. La baja es lógica: el registro se conserva con estado BAJA para no perder el historial. Usá una copia nueva para esta prueba; así no alterás los casos de préstamo preparados.

## 1 Alta y consulta

Entrá a **Ejemplares → Nuevo ejemplar**. Completá Código de inventario **DEFENSA-001**, Libro **Batman: Year One**, Sede propietaria **Biblioteca Central**, Condición física **Apto para préstamo**. Guardá y anotá el número de la ficha. Si ya usaste ese código en un ensayo, elegí DEFENSA-002.

Recargá la página. Mostrá que la copia sigue existiendo: el dato está en PostgreSQL. Abrí **Reportes → Disponibilidad por sede**, con Desde **01/10/2026**, Hasta **el día de la exposición** y sin filtro de sede. En un escenario intacto de octubre, el total sube de **90 a 91** y los disponibles de **83 a 84**. La fila Batman + Central pasa de 2 a 3 copias.

## 2 Modificación

Volvé a la ficha nueva y elegí **Editar**. Cambiá la condición a **No apto para préstamo** y guardá. La copia pasa a **EN_REVISION**. El total sigue en 91; los disponibles vuelven a **83**. En RP04, Batman + Central conserva 3 copias y aumenta la cantidad en revisión. Mostrá la ficha y el reporte: son dos vistas del mismo cambio.

## 3 Baja

En esa ficha, pulsá **Dar de baja** y confirmá. La copia queda **BAJA**. No desaparece de la consulta ni del total: eso es deliberado. RP04 sigue mostrando **91 copias, 83 disponibles**, pero cambia la distribución de estados: una copia sale de revisión y entra a BAJA. No prometas que todo indicador debe cambiar: lo que cambia aquí es el estado, no la existencia.

## 4 Comprobación documental

Abrí **Reportes → Comprobación de operaciones ABMC**. Desde y Hasta deben incluir el día en que hiciste los cambios; para aislar el ensayo, usá ese mismo día en ambos campos. Dejá Todas las sedes o elegí Central para las copias.

Buscá la entidad **ejemplares** y el mismo número de ficha. Aparecerán **ALTA, MODIFICACION y BAJA**, con fecha, usuario y cambios. La modificación muestra condición/estado anteriores y nuevos; la baja muestra el paso a BAJA. Las consultas no producen un evento de escritura.

Elegí **Imprimir / Guardar PDF**, guardá el documento y abrilo por pantalla. También podés usar **Exportar CSV**. Explicá: “Este reporte comprueba las operaciones realizadas; no es un listado sin relación con el ABMC”.

Los números 90/83 son la base de referencia. Si ya hiciste préstamos u otros cambios, compará contra el valor previo de tu ensayo y comprobá las mismas diferencias: +1 copia, +1 disponible, luego −1 disponible y finalmente cambio a BAJA.

<!-- page -->

# Préstamo local y devolución

Este recorrido muestra por qué una solicitud y un préstamo son objetos diferentes. Usá **EXPO-001**, Star Wars Vol. 1: Skywalker Strikes, que comienza disponible en Biblioteca Central. No uses EXPO-002: es el caso vencido ya preparado.

## Pasos en pantalla

1. En **Solicitudes → Nueva solicitud**, elegí a Maretto Agustin, Skywalker Strikes, origen Central y retiro Central. Guardá. El sistema determina que el trámite es local porque ambas sedes coinciden.
2. En la ficha de solicitud, elegí **Asignar ejemplar** y seleccioná EXPO-001. Se compromete esa copia y deja de estar disponible para otros pedidos.
3. Elegí **Preparar entrega local**. La solicitud y la copia quedan listas para entregar; todavía no hay un nuevo préstamo.
4. Elegí **Registrar entrega**. Usá la fecha del día y un vencimiento posterior, por ejemplo dentro de 14 días. Guardá. Se crea un préstamo y el ejemplar queda PRESTADO.
5. Abrí la ficha del préstamo y **Registrar devolución**. Indicá una fecha posterior o igual a la entrega y condición Apto. La devolución cierra el préstamo, pero deja la copia EN_REVISION.
6. En la ficha de EXPO-001, elegí **Aprobar disponibilidad** después de revisarla. La copia vuelve a DISPONIBLE porque está apta y en su sede propietaria activa.

## Cómo comprobar el resultado

RP04 usa las altas del período y muestra el estado actual. Con Desde 01/10/2026 y Hasta el día de la exposición, la disponibilidad baja en uno al asignar EXPO-001 y se recupera al aprobar su revisión. Los estados intermedios se ven en Por estado.

RP05 muestra las operaciones de solicitud, entrega, devolución y aprobación, con sus fechas y usuario. El préstamo conserva las fechas de entrega, vencimiento y devolución. Un préstamo con vencimiento futuro no debe aparecer en vencidos: eso también es una comprobación correcta.

## Rechazos que conviene poder mostrar

Inhabilitá a **Dalmazzo Francisco Gaston** desde su ficha e intentá iniciarle una solicitud: el sistema la rechaza (después volvé a habilitarlo). Intentá operar desde o hacia **Biblioteca Sur**: está de baja. Intentá asignar **EXPO-002**: ya está prestado. Intentá aprobar **EXPO-014** sin reparar su condición: está NO_APTO. La API debe rechazar el cambio y conservar el estado anterior.

Frase útil: “Las validaciones viven en el backend. Aunque otra pantalla o cliente llame a la API, se siguen aplicando las mismas reglas y restricciones de base de datos”.

<!-- page -->

# Préstamo entre sedes y reservas

## Traslado completo entre sedes

Usá la solicitud pendiente de **Carla Suárez por Skywalker Strikes**, origen Norte y retiro Central. Asigná **EXPO-003**, que pertenece a Norte. Desde la solicitud, prepará un remito con número nuevo, por ejemplo **DEF-ENV-001**, y agregá esa copia.

Seguí **Empaquetar → Despachar → Recibir envío**. En la recepción marcá el resultado de cada copia (llegó bien, dañada o no llegó) e indicá responsable. La solicitud queda lista para entrega en Central. Recién al registrar la entrega al lector nace el préstamo.

Mostrá el **historial del remito**: preparación, empaquetado, despacho, tránsito y recepción, con fecha y responsable. Es una prueba de la operación, además de la bitácora general. El remito no admite empaquetado vacío ni cancelación después de despachar.

Al devolver el préstamo en Central, la copia queda en revisión allí, pero sigue siendo propiedad de Norte. En la ficha del ejemplar elegí **Preparar retorno a sede propietaria**. Completá un nuevo remito Central → Norte. Al recibirlo en Norte queda en revisión; luego se aprueba disponibilidad si está apta. El retorno no crea un segundo préstamo.

Para una exposición más breve, abrí **ENV-2026-002**, ya recibido, y **ENV-2026-001**, en tránsito. Compará sus eventos. **EXPO-023**, Thrawn, ya fue devuelto en Norte y permite mostrar directamente la preparación de retorno a Central.

## Reserva preparada

Abrí la reserva pendiente de **Lucía Campos por Civil War** con retiro en Central. Elegí **Asignar ejemplar**, usá **EXPO-007** y una fecha límite futura. La asignación genera una solicitud local lista para entrega. Registrá la entrega desde esa solicitud y volvé a la reserva: debe estar **CUMPLIDA**.

También se puede cancelar una reserva antes de cumplirla. Cancelar o expirar libera la copia y cancela su solicitud pendiente. La expiración se procesa con el comando expirar_reservas; no se promete prioridad automática ni notificaciones.

## Los dos patrones que deben poder explicar

**State:** cada estado de Remito es una clase que admite sólo sus operaciones y ejecuta sus efectos; el servicio delega en `remito.comportamiento`. La ficha del remito muestra la clase activa y las operaciones admitidas/rechazadas. Ejemplo: un remito en tránsito no puede cancelarse. Código: apps/logistica/states.py. Ver docs/patrones.md.

**Strategy:** las estrategias local e interbibliotecaria comparten un contrato. La fábrica elige según el tipo de solicitud. La estrategia local prepara la entrega; la interbibliotecaria exige el traslado por remito. Código: apps/circulacion/strategies/.

<!-- page -->

# Cómo explicar los reportes de circulación

Todos los reportes piden **Desde y Hasta**, inclusive. La pantalla envía estos parámetros a la API; el backend filtra la base y calcula el resultado. El frontend presenta la respuesta y permite exportarla. No se computan los indicadores leyendo solamente las filas visibles del navegador.

## RP01 Préstamos vencidos

**Para qué sirve:** identificar préstamos que requieren seguimiento y la sede que entregó el material.

**Cómo se realiza:** se consultan Prestamo y sus relaciones con SolicitudPrestamo, Socio, Libro y Sede. Se seleccionan entregas entre Desde y Hasta, vencidas antes de Hasta y todavía abiertas al cierre de Hasta. Una devolución posterior al corte no elimina un atraso que existía ese día.

**Qué muestra:** detalle del préstamo, socio/libro, sede de entrega y días de atraso. Atraso = fecha Hasta − fecha de vencimiento, en días calendario. Con **01/10/2026–31/10/2026**, el escenario inicial muestra **1 préstamo**, de Ana por Skywalker Strikes, vencido el 12/10: **19 días** de atraso. Con Hasta 01/11 son 20; no es un error.

**Comprobación:** registrar su devolución después del corte mantiene el informe histórico. Para verificar el estado luego de devolver, usar un Hasta que incluya esa devolución. Mover Desde al 06/10 excluye ese préstamo porque se entregó el 05/10.

## RP02 Demanda interbibliotecaria

**Para qué sirve:** detectar qué materiales pide una sede a otra y orientar la distribución de ejemplares.

**Cómo se realiza:** filtra SolicitudPrestamo por fecha de solicitud y tipo INTERBIBLIOTECARIO; excluye CANCELADA y RECHAZADA; agrupa por libro y sede solicitante, es decir, el destino, y ordena por cantidad.

**Qué muestra:** libro, cantidad de solicitudes válidas y sede solicitante. Con octubre completo hay **4 solicitudes válidas**, una para Skywalker Strikes, Civil War, Infinity Gauntlet y Thrawn. Una solicitud Civil War cancelada no se cuenta.

**Comprobación:** crear una nueva solicitud interbibliotecaria y ampliar Hasta al día actual suma una unidad. Una local no aumenta este reporte. Cancelar o rechazar la nueva solicitud la excluye del conteo; RP05 conserva evidencia de la operación.

## RP03 Movimientos entre sedes

**Para qué sirve:** medir despachos y tiempo de transporte por trayecto.

**Cómo se realiza:** filtra Remito por fecha de despacho y agrupa por origen/destino. Cuenta todos los despachados. El promedio usa solamente los recibidos: suma de recepción − despacho dividida por cantidad recibida.

**Qué muestra:** Norte → Central: **2 despachos, 1 recibido, 2 días** de promedio; Central → Norte: **1 despacho, 1 recibido, 2 días**. Los datos se obtienen con octubre completo.

**Comprobación:** preparar o empaquetar no suma un despacho. Despachar un nuevo remito lo suma si su fecha está en rango. Recibirlo incrementa los recibidos y modifica el promedio; uno sin recibir no se trata como cero días.

<!-- page -->

# Reportes de disponibilidad y comprobación

## RP04 Disponibilidad por sede

**Para qué sirve:** saber cuántas copias de los ingresos del período se pueden prestar hoy, por obra y sede propietaria.

**Cómo se realiza:** filtra Ejemplar por **fecha de alta** entre Desde y Hasta y lo relaciona con Libro y Sede. Agrupa por libro y propietaria; cuenta total, disponibles y estados. Disponible exige estado DISPONIBLE, condición APTO, ubicación en su propietaria y sede activa. Proporción = disponibles / total × 100, redondeada para mostrarla.

**Qué muestra:** en el escenario inicial, las altas del 01/10/2026 reúnen **90 copias y 83 disponibles**. Si usás Desde 02/10 y Hasta 31/10, no aparecen: no hubo altas en ese período.

**Advertencia que debés explicar:** el rango selecciona las copias ingresadas; su estado es **actual**. No es una reconstrucción del stock en una fecha pasada. Por eso una baja realizada hoy afecta la disponibilidad de una copia ingresada en octubre. La fecha exacta de ese cambio se prueba en RP05.

**Comprobación ABMC:** agregar una copia suma total y disponible; cambiarla a NO_APTO mantiene el total y reduce disponible; darla de baja mantiene el total y cambia la distribución a BAJA. Editar el título de la obra cambia la etiqueta agrupada; la bitácora conserva el antes/después.

## RP05 Comprobación de operaciones ABMC

**Para qué sirve:** demostrar que las altas, modificaciones, bajas y comandos fueron realmente ejecutados y por qué cambió el sistema.

**Cómo se realiza:** cada escritura exitosa de la API guarda una Operacion con usuario, fecha, entidad, número de registro y valores antes/después, en la misma transacción. La consulta filtra por fecha de operación, ordena los eventos y cuenta cada tipo de acción. Las consultas y los intentos fallidos no se registran como cambios exitosos.

**Qué muestra:** una fila por operación con cambios y un resumen de altas, modificaciones, bajas y comandos. La preparación inicial se identifica como un único evento de escenario; no se inventan eventos históricos de usuario para los datos cargados. Durante el ABMC de una copia nueva aparecen tres eventos: ALTA, MODIFICACION, BAJA.

**Filtro de sede:** las copias, solicitudes y remitos tienen sedes asociadas. Libros y socios son globales: para ver sus eventos elegí Todas las sedes. La bitácora registra la API de negocio; no audita cambios directos por SQL o Django Admin.

## Mostrar un documento por pantalla

En el reporte, completá fechas y sede, pulsá Aplicar y esperá el resultado. Elegí **Imprimir / Guardar PDF**, seleccioná Guardar como PDF y abrí el archivo. El documento incluye título, período, sede, criterio, tabla y fecha de generación. También tenés CSV para revisar las cifras en una hoja de cálculo.

Para la defensa priorizá un documento generado después de tu propia operación. Los PDF de referencia sirven para estudiar y comparar; son una fotografía de los datos al generarlos y no cambian solos.

<!-- page -->

# Preguntas frecuentes y ensayo

## Respuestas que conviene practicar

**¿Por qué no se borra físicamente la copia?** Porque los préstamos y remitos deben seguir apuntando al material usado. La baja lógica impide nuevas operaciones y conserva el historial. En el reporte se ve BAJA; el total de copias registradas no disminuye.

**¿Qué diferencia hay entre disponible y no prestado?** Una copia sin préstamo puede estar asignada, en tránsito, en revisión, dañada o fuera de su propietaria. Solo se ofrece cuando cumple todas las condiciones de disponibilidad.

**¿Dónde se calculan los reportes?** En Django: vistas validan parámetros, selectors/services filtran con el ORM y agrupan/calculan. PostgreSQL almacena las filas. React recibe la respuesta y arma la tabla, el CSV y la impresión. Ejemplos: apps/reportes/views.py, services.py y selectors.py.

**¿Cómo demuestran que el reporte no está armado a mano?** Ejecutamos el ABMC, recargamos la ficha y volvemos a consultar el reporte con el rango correcto. Además, las pruebas automatizadas comparan resultados contra un conjunto de datos conocido y verifican transacciones, límites de fechas y rechazo de operaciones inválidas.

**¿Se puede prestar dos veces la misma copia al mismo tiempo?** Los servicios validan estado y toman bloqueos de fila dentro de una transacción. Hay pruebas específicas con PostgreSQL para esa concurrencia.

**¿Cuáles son las limitaciones?** Los socios no tienen cuentas públicas; el personal opera toda la red. No hay multas, notificaciones, prioridad automática de reservas ni tratamiento especial de extravío/destrucción. Sí se registra condición física en la devolución. RP04 no reconstruye estados históricos.

## Antes de exponer

Comprobá Docker, acceso, DER y credenciales. Ensayá DEFENSA-001, anotá su número de ficha y generá el PDF después del cambio. Los cuatro integrantes deben poder explicar ambos patrones y una validación rechazada.

## Volver al escenario inicial

El comando siguiente **elimina las operaciones de biblioteca y la bitácora actuales**, y vuelve a cargar los casos de esta guía. Conserva usuarios y sesiones. Usalo antes de un ensayo si querés empezar de cero; guardá un respaldo si necesitás conservar el ensayo anterior.

`docker compose exec backend python manage.py preparar_exposicion --reiniciar`

El catálogo y sus fuentes están en docs/catalogo-exposicion.md. Las fechas históricas del escenario son de octubre de 2026; las operaciones realizadas durante la defensa llevan su fecha real. En RP05 y al comprobar altas nuevas, Hasta debe incluir el día de la exposición.
