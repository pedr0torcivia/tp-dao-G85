# Patrones de diseño

El sistema aplica dos patrones GoF que se conectan entre sí: **Strategy** decide cómo se tramita una solicitud y, en el caso interbibliotecario, entrega el ejemplar a la logística, donde **State** gobierna el ciclo de vida del remito. Ambos son visibles en la interfaz: las fichas de solicitud y de remito muestran qué clase está actuando y qué operaciones admite.

## State · ciclo de vida del remito

Código: `backend/apps/logistica/states.py` (estados) y `backend/apps/logistica/models.py` (contexto).

| Rol GoF | Clase | Responsabilidad |
| --- | --- | --- |
| Contexto | `Remito` | Expone `remito.comportamiento` (el objeto estado vigente) y `remito.transicionar(destino, responsable, observacion)`, único punto que cambia el estado y registra el `EventoRemito`. |
| Estado abstracto | `EstadoRemitoBase` | Declara las siete operaciones (`agregar`, `quitar`, `empaquetar`, `reabrir`, `despachar`, `recibir`, `cancelar`) y por defecto las rechaza con `TransicionInvalidaError`. |
| Estados concretos | `EnPreparacion`, `Empaquetado`, `EnTransito`, `Recibido`, `RecibidoConIncidencias`, `Cancelado` | Redefinen sólo lo que admiten y **ejecutan los efectos** de la transición (ejemplares, solicitudes, fechas). |

```
EN_PREPARACION --empaquetar--> EMPAQUETADO --despachar--> EN_TRANSITO --recibir--> RECIBIDO
      ^   |                      |    |                                  \-> RECIBIDO_CON_INCIDENCIAS
      |   +--cancelar--+         |    +--cancelar--+
      +-----reabrir----|---------+                 |
                       v                           v
                   CANCELADO <---------------------+
```

| Estado | Admite | Efecto principal |
| --- | --- | --- |
| `EnPreparacion` | agregar, quitar, empaquetar, cancelar | Arma el paquete; no se empaqueta vacío. |
| `Empaquetado` | reabrir, despachar, cancelar | `despachar` pone cada ejemplar en tránsito (sin sede actual) y las solicitudes en traslado. |
| `EnTransito` | recibir | Cada ejemplar se marca conforme, dañado o extraviado. Con alguna incidencia, el remito termina en `RECIBIDO_CON_INCIDENCIAS` y la solicitud afectada vuelve a `PENDIENTE` para asignar otra copia. |
| `Recibido`, `RecibidoConIncidencias`, `Cancelado` | — | Estados finales. |

Los servicios (`services.py`) sólo bloquean filas, validan reglas transversales (sedes activas, pertenencia del ejemplar) y delegan: `remito.comportamiento.despachar(remito, ...)`. Ningún servicio escribe `Remito.estado`.

`EstadoRemitoBase.operaciones_admitidas()` calcula, por introspección, qué operaciones redefine cada clase. La API lo expone como `acciones` junto a `estado_clase`, y la interfaz muestra únicamente esos botones: la regla vive en un solo lugar.

**Cómo demostrarlo:** abrir un remito en preparación, ver la nota «Patrón State» (`EnPreparacion`, operaciones en verde). Empaquetar → la nota pasa a `Empaquetado` y aparece *Reabrir*. Despachar → `EnTransito` sólo admite `recibir()`; cancelar ya no se ofrece y la API lo rechaza. Recibir marcando un ejemplar como dañado → `RecibidoConIncidencias`. La trazabilidad muestra cada transición con fecha y responsable.

## Strategy · tramitación de la solicitud

Código: `backend/apps/circulacion/strategies/`.

| Rol GoF | Clase | Responsabilidad |
| --- | --- | --- |
| Contexto | `crear_solicitud`, `preparar_entrega` (`circulacion/services.py`) | No preguntan por el tipo: piden la estrategia y la usan. |
| Estrategia | `TramitacionPrestamo` | `validar_creacion()`, `preparar_entrega()` y el `recorrido` de estados del circuito. Las precondiciones comunes de la preparación están en `validar_preparacion()`. |
| Concreta | `TramitacionLocal` | Exige misma sede; preparar deja la copia **lista en mostrador**. |
| Concreta | `TramitacionInterbibliotecaria` | Exige sedes distintas; preparar **incorpora la copia a un remito** hacia la sede de retiro (reutiliza el que esté en preparación para ese trayecto o crea uno con número automático). |
| Fábrica | `obtener_estrategia(tipo)` | Elige la clase según `SolicitudPrestamo.tipo`. |

El mismo botón *Preparar entrega* produce resultados distintos según la estrategia; esa es la evidencia del polimorfismo. La API expone `estrategia`, `estrategia_descripcion`, `recorrido` y `acciones` de cada solicitud.

Agregar un circuito nuevo (por ejemplo, envío a domicilio) requiere una clase y una entrada en la fábrica, sin modificar los servicios.

**Cómo demostrarlo:** crear dos solicitudes del mismo libro, una local y otra interbibliotecaria, desde *Nueva solicitud* (la pantalla muestra la disponibilidad por sede y anticipa la estrategia). Asignar y preparar: la local queda *Lista para entrega*; la interbibliotecaria aparece dentro de un remito en preparación. A partir de ahí manda el patrón State.

## Evidencia automatizada

- `apps/logistica/tests/test_states.py`: cada clase admite exactamente sus operaciones y rechaza el resto; efectos de empaquetar, reabrir y despachar.
- `apps/logistica/tests/test_services.py`: recepción con incidencias, retorno a sede propietaria, numeración automática, reabrir y quitar.
- `apps/circulacion/tests/test_strategies.py` y `test_interbibliotecaria.py`: elección de estrategia y preparación mediante remito.
- `apps/common/tests/test_circuitos.py`: circuitos completos por API.
- `frontend/e2e/circuitos.spec.ts`: los mismos circuitos desde el navegador, incluida la recepción con daño.
