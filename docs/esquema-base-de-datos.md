# Esquema de la base de datos

Versión documentada del [DER limpio en FigJam](https://www.figma.com/board/aYOy4RyT0MaeW0a69ivvxJ/Modelos?node-id=100-1715), actualizado para impresión A4 con relaciones. Los modelos Django y sus migraciones en `backend/apps/*/migrations/` son la implementación ejecutable de este esquema.

El dominio tiene diez tablas. Django agrega las tablas de infraestructura para usuarios, permisos, sesiones y administración; no forman parte de las diez entidades de biblioteca. `Libro` representa la obra o edición catalogada; `Ejemplar` representa cada copia física. El autor se guarda como texto en `Libro.autor`: no hay tablas `Autor` ni `LibroAutor`.

## Tablas y campos

`PK` = clave primaria; `FK` = clave foránea; `UK` = valor único; `?` = admite `NULL`. Los tipos y longitudes concretos están definidos en los modelos y migraciones de Django.

| Tabla | Campos |
|---|---|
| **SEDE** | `id PK`, `nombre UK`, `direccion`, `contacto`, `horarios`, `estado` |
| **LIBRO** | `id PK`, `isbn UK ?`, `titulo`, `autor`, `editorial`, `edicion` |
| **EJEMPLAR** | `id PK`, `codigoInventario UK`, `libroId FK`, `sedePropietariaId FK`, `sedeActualId FK ?`, `estado`, `condicionFisica` |
| **SOCIO** | `id PK`, `numeroSocio UK`, `documento UK`, `nombre`, `contacto`, `estado` |
| **SOLICITUD_PRESTAMO** | `id PK`, `socioId FK`, `libroId FK`, `ejemplarId FK ?`, `sedeOrigenId FK`, `sedeDestinoId FK`, `reservaId FK UK ?`, `fechaSolicitud`, `tipo`, `estado` |
| **PRESTAMO** | `id PK`, `solicitudId FK UK`, `fechaEntrega`, `fechaVencimiento`, `fechaDevolucion ?`, `condicionDevolucion ?` |
| **RESERVA** | `id PK`, `socioId FK`, `libroId FK`, `sedeRetiroId FK`, `ejemplarAsignadoId FK ?`, `fechaReserva`, `fechaLimiteRetiro ?`, `estado` |
| **REMITO** | `id PK`, `numero UK`, `sedeOrigenId FK`, `sedeDestinoId FK`, `estado`, `fechaCreacion`, `fechaDespacho ?`, `fechaRecepcion ?` |
| **DETALLE_REMITO** | `id PK`, `remitoId FK`, `ejemplarId FK`, `solicitudId FK ?`, `condicionSalida`, `condicionRecepcion ?` |
| **EVENTO_REMITO** | `id PK`, `remitoId FK`, `fechaHora`, `estadoAnterior ?`, `estadoNuevo`, `responsable`, `observacion` |

## Relaciones

| Desde | Hacia | Cardinalidad y sentido |
|---|---|---|
| `EJEMPLAR.libroId` | `LIBRO.id` | Un libro puede tener muchos ejemplares; cada ejemplar pertenece a un libro. |
| `EJEMPLAR.sedePropietariaId` | `SEDE.id` | Cada ejemplar tiene una sede propietaria. |
| `EJEMPLAR.sedeActualId` | `SEDE.id` | La ubicación actual es opcional, por ejemplo durante el tránsito. |
| `SOLICITUD_PRESTAMO.socioId` | `SOCIO.id` | Un socio puede realizar muchas solicitudes. |
| `SOLICITUD_PRESTAMO.libroId` | `LIBRO.id` | La solicitud pide un libro. |
| `SOLICITUD_PRESTAMO.ejemplarId` | `EJEMPLAR.id` | La copia concreta puede asignarse después. |
| `SOLICITUD_PRESTAMO.sedeOrigenId` | `SEDE.id` | Sede propietaria de la copia asignada. |
| `SOLICITUD_PRESTAMO.sedeDestinoId` | `SEDE.id` | Sede donde se entrega al socio. |
| `SOLICITUD_PRESTAMO.reservaId` | `RESERVA.id` | Una reserva puede originar como máximo una solicitud. |
| `PRESTAMO.solicitudId` | `SOLICITUD_PRESTAMO.id` | Una solicitud genera como máximo un préstamo. |
| `RESERVA.socioId` | `SOCIO.id` | Un socio puede tener varias reservas. |
| `RESERVA.libroId` | `LIBRO.id` | Una reserva corresponde a un libro. |
| `RESERVA.sedeRetiroId` | `SEDE.id` | Sede elegida para retirar. |
| `RESERVA.ejemplarAsignadoId` | `EJEMPLAR.id` | La copia puede asignarse después. |
| `REMITO.sedeOrigenId` | `SEDE.id` | Sede que despacha. |
| `REMITO.sedeDestinoId` | `SEDE.id` | Sede que recibe. |
| `DETALLE_REMITO.remitoId` | `REMITO.id` | Un remito agrupa ejemplares. |
| `DETALLE_REMITO.ejemplarId` | `EJEMPLAR.id` | Cada detalle identifica una copia transportada. |
| `DETALLE_REMITO.solicitudId` | `SOLICITUD_PRESTAMO.id` | Puede vincular el traslado a una solicitud; también permite traslados sin solicitud. |
| `EVENTO_REMITO.remitoId` | `REMITO.id` | Un remito conserva sus eventos de estado ordenados por fecha y hora. |

## Lectura funcional

- El **remito** documenta exclusivamente el movimiento de ejemplares entre sedes. La entrega de una copia al socio se registra en **préstamo**, al momento de entregarla.
- En una solicitud **local**, origen y destino son la misma sede. En una **interbibliotecaria**, son sedes distintas. `SolicitudPrestamo.tipo` permite elegir la estrategia de tramitación.
- `Remito.estado` representa el estado actual y `EventoRemito` conserva el historial de cambios. Las clases del patrón **State** y las implementaciones del patrón **Strategy** pertenecen a la lógica de la aplicación, no son tablas adicionales.
- La disponibilidad se obtiene del estado, ubicación y asignación del ejemplar; no se duplica en `Libro`.
- `isbn` puede ser nulo, pero debe ser único cuando está informado. `solicitudId` en `Prestamo` y `reservaId` en `SolicitudPrestamo` son únicos para expresar las relaciones de como máximo uno.

## Reglas operativas y restricciones vigentes

La política de devolución, retorno, recepción y reserva está en [Reglas de negocio](reglas-negocio.md). La estructura mantiene diez entidades y admite el retorno sin cambiar la sede propietaria ni crear otro préstamo. La migración `catalogo/0003` añade la unicidad de edición sin ISBN por título, autor, editorial y edición sin distinguir mayúsculas. El DER A4 con relaciones está en [FigJam](https://www.figma.com/board/aYOy4RyT0MaeW0a69ivvxJ/Modelos?node-id=100-1715).

## Crear la base SQLite

Desde `backend/`, con las dependencias instaladas:

```powershell
$env:DJANGO_USE_SQLITE = "true"
python manage.py migrate
```

Esto crea `backend/db.sqlite3`. Para consultar su esquema con SQLite:

```powershell
sqlite3 db.sqlite3 ".schema"
```

En el despliegue con Docker se usa PostgreSQL; Django aplica las mismas migraciones con `python manage.py migrate`.


## Metadatos de operación y reportes

Ejemplar agrega `fecha_alta`, un metadato técnico para seleccionar las altas entre Desde y Hasta en RP04. Se define en `catalogo/0004`. La distribución de estados de ese reporte es actual, no histórica.

`common/0001` agrega la bitácora técnica `Operacion`: fecha, entidad, registro_id, accion, descripcion, usuario, sede_ids, antes y despues. Conserva eventos de escritura de la API para RP05; los identificadores y las instantáneas preservan evidencia incluso cuando cambia el registro. No reemplaza el historial de estados del remito ni agrega otra entidad al dominio de préstamos.
