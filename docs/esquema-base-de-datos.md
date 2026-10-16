# Esquema de la base de datos

Versión documentada del [DER limpio en FigJam](https://www.figma.com/board/aYOy4RyT0MaeW0a69ivvxJ/Modelos?node-id=84-1715), 16 de octubre de 2026. Es la referencia para acordar los modelos y migraciones de Django; este documento no crea tablas en PostgreSQL.

La base tiene diez tablas. `Libro` representa la obra o edición catalogada; `Ejemplar` representa cada copia física. El autor se guarda como texto en `Libro.autor`: no hay tablas `Autor` ni `LibroAutor`.

## Tablas y campos

`PK` = clave primaria; `FK` = clave foránea; `UK` = valor único; `?` = admite `NULL`. Los tipos y longitudes concretos se definirán al implementar las migraciones.

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

## Reglas por cerrar antes de migrar

El DER no decide por sí solo dónde se devuelve una copia y cómo regresa a su sede propietaria, si se admite recepción parcial de un remito, la prioridad y el vencimiento de reservas, ni el criterio de duplicados para libros sin ISBN. Estas reglas deben acordarse antes de fijar restricciones y flujos de negocio en Django.
