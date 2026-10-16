# Roadmap I4 — Logística y trazabilidad

Fecha: 16 de octubre de 2026. Responsable: I4 (Agustín).

Plan de trabajo para `apps/logistica` (Remito, DetalleRemito, EventoRemito, patrón State) y RP03. Complementa la [distribución del backend](distribucion-backend.md). La especificación funcional se extrae de las fuentes acordadas: los contratos TypeScript del frontend (`frontend/src/domain/models.ts`, `frontend/src/api/mock.ts`, `frontend/src/domain/reports.ts`, `frontend/src/domain/workflows.test.ts`) y la definición del producto.

## 1. Objetivo

Un ejemplar de la red viaja de una sede a otra dentro de un remito, con cada paso registrado en un historial verificable, y el préstamo interbibliotecario se completa apoyándose en ese traslado. El patrón State gobierna las transiciones del remito y queda demostrable con clases y comportamiento.

## 2. Alcance

| Área | Contenido |
|---|---|
| Entidades | `Remito`, `DetalleRemito`, `EventoRemito` |
| Patrón | **State**: estados del remito como clases con operaciones permitidas y transiciones controladas |
| Comandos API | `asignar`, `empaquetar`, `despachar`, `registrar-salida`, `recibir`, `cancelar` |
| Reporte | RP03: envíos por origen/destino y tiempo promedio de tránsito de los recibidos |
| Transversal | Coordinar integración con Circulación (I3), documentar el patrón, preparar evidencia para la demo |

## 3. Especificación funcional

### 3.1 Entidades (contrato con el frontend)

```text
Remito            id, numero, sede_origen_id, sede_destino_id, estado,
                  fecha_creacion, fecha_despacho?, fecha_recepcion?
DetalleRemito     id, remito_id, ejemplar_id, solicitud_id?, condicion_salida,
                  condicion_recepcion?
EventoRemito      id, remito_id, fecha_hora, estado_anterior?, estado_nuevo,
                  responsable, observacion
```

Estados del remito: `EN_PREPARACION`, `EMPAQUETADO`, `DESPACHADO`, `EN_TRANSITO`, `RECIBIDO`, `CANCELADO`.

Rutas acordadas con el frontend: `remitos/`, `detalles-remito/`, `eventos-remito/`. Los listados devuelven la paginación estándar de DRF (el frontend sigue `next`).

### 3.2 Máquina de estados (patrón State)

Cada estado es una clase que decide qué operaciones acepta. No se cambia el estado con un `PATCH` genérico: sólo por comandos.

```text
EstadoRemitoBase (abstracta)
├── EnPreparacion   → empaquetar, cancelar, asignar ejemplar
├── Empaquetado     → despachar, cancelar
├── Despachado      → registrar-salida
├── EnTransito      → recibir
├── Recibido        (terminal)
└── Cancelado       (terminal)
```

Toda operación no permitida en el estado actual se rechaza con error y **sin cambios ni eventos parciales**.

### 3.3 Reglas por comando

| Comando | Estado requerido | Reglas | Efectos |
|---|---|---|---|
| crear remito | — | Sedes activas; origen ≠ destino; `numero` único | Estado `EN_PREPARACION`; primer `EventoRemito` |
| `asignar` | EN_PREPARACION | Ejemplar pertenece al origen y está en el origen; no está en otro remito vigente; disponible o vinculado a solicitud interbibliotecaria `ASIGNADA` hacia este destino | `DetalleRemito` con `condicion_salida`; ejemplar → `ASIGNADO` |
| `empaquetar` | EN_PREPARACION | Al menos un ejemplar en el detalle | → EMPAQUETADO + evento |
| `despachar` | EMPAQUETADO | Al menos un ejemplar; socios de las solicitudes vinculadas habilitados; sedes activas | `fecha_despacho`; ejemplares → `EN_TRANSITO` con `sede_actual = null`; solicitudes → `EN_TRASLADO`; + evento |
| `registrar-salida` | DESPACHADO | — | → EN_TRANSITO + evento |
| `recibir` | EN_TRANSITO | Recepción completa: todos los ejemplares verificados; responsable obligatorio; sedes activas no exigidas en este paso | `fecha_recepcion`; ejemplar → sede destino y `condicion_recepcion`; con solicitud → `LISTO_PARA_ENTREGA` / solicitud `LISTA_PARA_ENTREGA`; sin solicitud → `EN_REVISION`; + evento |
| `cancelar` | EN_PREPARACION o EMPAQUETADO | — | → CANCELADO + evento; ejemplares sin solicitud vuelven a `DISPONIBLE`; con solicitud quedan `ASIGNADO` |

Reglas invariantes en todo el ciclo:

1. La sede propietaria del ejemplar nunca cambia por el traslado.
2. Durante el tránsito, `sede_actual` es `null` (no es una sede).
3. Un ejemplar no puede estar en dos remitos vigentes (no `CANCELADO`/`RECIBIDO`).
4. Cada transición, el evento y los cambios de ejemplares/solicitudes se confirman en una única transacción.
5. Una operación rechazada no persiste nada.

### 3.4 EventoRemito

Cada transición persiste un evento con `estado_anterior`, `estado_nuevo`, `fecha_hora`, `responsable` (del payload o "Personal de biblioteca") y `observación` opcional. La creación inicial genera el primer evento (`estado_anterior = null`). El historial completo se consulta por `eventos-remito/?remito_id=…`, ordenado por `fecha_hora` e `id`.

### 3.5 RP03 — Movimiento entre sedes

- Filtros: rango `desde`/`hasta` por **fecha de despacho**, y `sede` (opcional: origen o destino).
- Agrupación por par origen → destino: cantidad despachada, cantidad recibida y tiempo medio de tránsito.
- El tiempo de tránsito es `fecha_recepcion − fecha_despacho`, promediado **sólo sobre remitos recibidos**; los pendientes no entran al promedio y se muestran como "Sin recepciones".
- Debe manejar resultados vacíos, explicar su criterio de conteo y comprobarse contra un conjunto de datos con resultado esperado calculado a mano.

## 4. Decisiones que debo cerrar con el grupo

| # | Decisión | Propuesta del mock (a ratificar) |
|---|---|---|
| 2 | Cómo regresa el ejemplar a su sede propietaria tras la devolución | Nuevo remito de retorno; el ejemplar queda `EN_REVISION` en la sede de entrega hasta que alguien lo disponga |
| 3 | Operaciones iniciadas cuando una sede se da de baja | Sólo crear/asignar/empaquetar/despachar exigen sedes activas; recibir un remito ya en tránsito se permite |
| 4 | Recepción completa o parcial | Completa: se verifican todos los ejemplares; la parcial queda como mejora futura |
| 5 | Condición física al recibir | Se copia la condición del ejemplar (`condicion_recepcion = condicion_fisica`); la revisión especial es opcional |
| 8 | Qué usuarios pueden despachar y recibir | Pendiente de la decisión general de autenticación (I1) |

## 5. Roadmap por sub-partes (una PR por paso)

Cada paso termina en una PR revisable (I2 es mi revisor cruzado) y con sus pruebas ejecutadas. Ramas breves, commits `TIPO(Área): descripción`.

### L0 — Especificación y acuerdos (rama `feature/logistica-spec`)
- Publicar este documento (o su versión final) y cerrar las decisiones de la sección 4 con el grupo.
- Acordar con I3 el campo `DetalleRemito.solicitud_id` (FK nullable) y con I2 el FK a `Ejemplar`.
- Commit: `ADD(Doc): Especificar módulo de logística y transiciones del remito`.
- Verificación: el grupo aprueba la spec; no hay código.

### L1 — Modelos y migración (rama `feature/logistica-modelos`) — requiere catálogo de I2
- `Remito` (`numero` único, sedes, estado con choices, fechas), `DetalleRemito` (FK remito, FK ejemplar, `solicitud_id` nullable, condiciones), `EventoRemito` (FK remito, estados, responsable, observación).
- Constraints de BD: unicidad de `numero`; unicidad de ejemplar en remitos vigentes (índice parcial cuando sea viable en PostgreSQL); consistencia básica entre estado y fechas.
- Admin de Django en modo consulta (sin delete, sin cambio directo de estado).
- Commit: `ADD(Logistica): Modelar remito, detalle y eventos con restricciones`.
- Pruebas `test_models`: unicidades, estados válidos, integridad referencial.

### L2 — Clases del patrón State (rama `feature/logistica-state`)
- `states.py`: base abstracta + una clase por estado; mapa estado → clase; transiciones y operaciones declaradas por clase.
- Servicios y vistas nunca escriben `estado` a mano: delegan en la clase.
- Commit: `ADD(Logistica): Implementar patrón State con clases de estado`.
- Pruebas `test_states` (sin BD, rápidas): para cada estado, operación permitida y operaciones rechazadas.

### L3 — Servicios de preparación (rama `feature/logistica-preparacion`)
- Services: `crear_remito`, `agregar_ejemplar`, `empaquetar`, `cancelar_remito`; selectors: `obtener_remito`, `listar_remitos`, `historial_remito`.
- Transacciones con `select_for_update` sobre remito y ejemplares.
- Commit: `ADD(Logistica): Implementar preparación, empaquetado y cancelación del remito`.
- Pruebas `test_services`: éxito, cada rechazo de la tabla 3.3 y atomicidad (operación inválida no deja cambios ni eventos).

### L4 — Despacho, tránsito y recepción (rama `feature/logistica-recepcion`)
- Services: `despachar`, `registrar_salida`, `recibir`, con efectos coordinados sobre ejemplares y solicitudes (I3/I2).
- Commit: `ADD(Logistica): Implementar despacho, tránsito y recepción con historial`.
- Pruebas `test_services`: ciclo completo del remito (portar el escenario de `workflows.test.ts`), recepción incompleta rechazada, cancelación tras despacho rechazada, concurrencia (dos remitos pretendiendo el mismo ejemplar → uno gana).

### L5 — API, serializers y rutas (rama `feature/logistica-api`)
- ViewSets `remitos`, `detalles-remito`, `eventos-remito` + `@action` por comando (`POST /remitos/{id}/{comando}/`).
- Payloads: `asignar {ejemplar_id}`; `recibir {responsable, verificados, observacion?}`; resto `{responsable, observacion?}`. Errores con el envolvente común por campo.
- Estado nunca editable por `PATCH`.
- Commit: `ADD(Logistica): Exponer API de remitos con comandos de estado`.
- Pruebas `test_api`: ciclo completo por HTTP, rechazos con 400 y mensaje por campo, Swagger refleja el contrato.

### L6 — RP03 (rama `feature/reportes-movimientos`) — coordenar ruta con I3
- Selector + servicio del reporte según 3.5; endpoint `GET /api/reportes/movimientos/` con `desde`, `hasta`, `sede`.
- Fixtures de demostración con resultado esperado calculado a mano (incluye remito sin recibir excluido del promedio y caso vacío).
- Commit: `ADD(Reportes): Implementar RP03 de movimiento entre sedes con datos de verificación`.
- Pruebas: resultados exactos contra fixture, filtros, vacíos.

## 6. Dependencias y coordinación

```text
I2: Catálogo (Ejemplar) ──┐
                          ├──> L1..L5 (mis PRs) ──> I3: usa el traslado (Strategy interbibliotecaria)
I3: SolicitudPrestamo ────┘
```

- L1 bloqueada por `Ejemplar` (I2) y el acuerdo del FK con I3; L0, L2 y la spec puedo avanzarlas ya.
- `solicitud_id` en `DetalleRemito` es nullable: un remito puede llevar ejemplares sin solicitud asociada.
- Los efectos de `despachar`/`recibir` sobre `SolicitudPrestamo` (`EN_TRASLADO`, `LISTA_PARA_ENTREGA`) se codifican de común acuerdo con I3; definir juntos la firma de los servicios compartidos.

## 7. Estrategia de pruebas

- `test_states`: puros, sin BD (corren con SQLite) — la máquina de estados es la unidad crítica del patrón.
- `test_models` / `test_services` / `test_api`: con PostgreSQL (`DJANGO_USE_SQLITE` sólo para iteración rápida).
- Concurrencia: sólo con PostgreSQL (`select_for_update`); caso de doble asignación de ejemplar entre remitos.
- Aceptación: portar el escenario de remito de `workflows.test.ts` a pytest, y RP03 contra fixture con valores precalculados (independiente de la consulta implementada).

## 8. Definición de terminado (por PR)

- [ ] Cumple el requisito y las reglas 3.3, sin atajos de estado (`PATCH` no cambia estado).
- [ ] Modelo + migración cuando corresponde; verificada contra PostgreSQL.
- [ ] Servicios transaccionales y selectores separados; reglas fuera de las vistas.
- [ ] Pruebas de éxito, rechazo y riesgo (concurrencia, atomicidad) pasando.
- [ ] Swagger refleja el contrato; nombres coinciden con `models.ts`.
- [ ] La pantalla de remitos del frontend consume la API real sin mezclar IDs del mock.
- [ ] Funciona en Docker (`VITE_DATA_SOURCE=http`).
- [ ] PR revisada por I2, con evidencia de cómo se verificó.
