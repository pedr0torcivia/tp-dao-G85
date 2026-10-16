# Distribución del trabajo del backend

Fecha de actualización: 16 de octubre de 2026.

Este documento define cómo se divide el desarrollo del backend de EntreLibros entre los cuatro integrantes del Grupo 85. Complementa la [definición del producto](definicion-producto.md), el [plan del proyecto](plan-proyecto.md) y la guía de integración frontend-backend.

El [esquema de la base de datos](esquema-base-de-datos.md) documenta el DER acordado para los cuatro módulos.

## Criterio de división

El trabajo se divide por módulos funcionales completos y no por capas técnicas. Cada responsable desarrolla y comprende los modelos, migraciones, servicios, consultas, serializers, vistas, rutas y pruebas de su área.

Todos los módulos deben respetar estas reglas generales:

- Las reglas de negocio se ejecutan en el backend, aunque el frontend también ayude a validarlas.
- Los cambios relacionados de una operación se confirman dentro de una transacción.
- Los estados controlados cambian mediante acciones específicas, no mediante un `PATCH` genérico.
- Las restricciones estructurales también se protegen en PostgreSQL.
- Las relaciones y nombres de campos deben coincidir con los contratos TypeScript acordados.
- Cada cambio se integra mediante una PR revisada por otro integrante.

## Distribución principal

| Integrante | Área principal | Responsabilidad transversal | Reporte |
|---|---|---|---|
| I1 | Sedes y socios | Entorno compartido, Docker, autenticación e integración | RP01: préstamos vencidos |
| I2 | Catálogo y ejemplares | Esquema, migraciones, disponibilidad y concurrencia | RP04: disponibilidad por sede |
| I3 | Solicitudes, préstamos, devoluciones y reservas | Contratos API y patrón Strategy | RP02: demanda interbibliotecaria |
| I4 | Remitos y trazabilidad | Patrón State y coordinación de integración | RP03: movimientos entre sedes |

## Integrante 1: administración y plataforma

Sedes ya cuenta con una primera versión completa. El siguiente módulo principal de I1 es `apps/socios`.

### Backend de socios

- Implementar el modelo `Socio`.
- Garantizar unicidad de `numero_socio` y `documento`.
- Usar los estados `HABILITADO` e `INHABILITADO`.
- Implementar alta, consulta, edición, búsqueda y filtros.
- Implementar las acciones `habilitar` e `inhabilitar`.
- Impedir la eliminación física y el cambio directo del estado.
- Agregar pruebas de modelo, servicios y API.

Endpoints previstos:

```http
GET   /api/socios/
POST  /api/socios/
GET   /api/socios/{id}/
PATCH /api/socios/{id}/
POST  /api/socios/{id}/habilitar/
POST  /api/socios/{id}/inhabilitar/
```

Un socio inhabilitado no puede iniciar un préstamo nuevo, pero sí debe poder devolver material que ya tenía prestado.

### Responsabilidades transversales

- Mantener Docker Compose y las instrucciones de ejecución.
- Preparar datos reproducibles para la demostración.
- Colaborar en la autenticación y los permisos cuando se acuerde su alcance.
- Verificar construcción, migración y persistencia desde un clon limpio.
- Implementar RP01: cantidad, detalle y días de atraso de préstamos vencidos.

## Integrante 2: catálogo, ejemplares y disponibilidad

I2 es responsable de `apps/catalogo`.

### Entidades

- `Libro`.
- `Ejemplar`.

### Reglas principales

- ISBN único cuando está informado y `null` cuando no existe.
- Código de inventario único.
- Autor registrado como texto en `Libro.autor`; el esquema no incluye una tabla de autores.
- Sede propietaria obligatoria.
- Sede actual opcional durante el tránsito.
- Disponibilidad calculada a partir del ejemplar; no almacenada en `Libro`.
- Estado del ejemplar separado de su condición física.
- Relaciones históricas protegidas ante eliminaciones.

Estados previstos del ejemplar:

```text
DISPONIBLE
ASIGNADO
EN_TRANSITO
LISTO_PARA_ENTREGA
PRESTADO
EN_REVISION
BAJA
```

Endpoints previstos:

```http
/api/libros/
/api/ejemplares/
```

La actualización de los datos bibliográficos de un libro, incluido su autor, corresponde al módulo de catálogo.

### Responsabilidades transversales

- Coordinar las migraciones y revisar la integridad del esquema.
- Implementar consultas de disponibilidad.
- Evitar la doble asignación de un ejemplar mediante bloqueos y transacciones.
- Colaborar con I3 en la asignación de reservas.
- Colaborar con I4 en la ubicación y recepción de ejemplares.
- Implementar RP04: cantidades, estados y proporción disponible por sede.

## Integrante 3: circulación

I3 es responsable de `apps/circulacion`.

### Entidades

- `SolicitudPrestamo`.
- `Prestamo`.
- `Reserva`.

### Procesos

- Crear una solicitud.
- Asignar un ejemplar.
- Preparar la entrega.
- Entregar y generar el préstamo.
- Controlar el vencimiento.
- Registrar la devolución y la condición física.
- Crear, asignar, cancelar y expirar reservas.

### Patrón Strategy

La tramitación debe usar un contrato común con dos implementaciones:

```text
TramitacionPrestamo
├── TramitacionLocal
└── TramitacionInterbibliotecaria
```

La estrategia local se implementa primero. La interbibliotecaria se completa cuando Logística permita trasladar y recibir el ejemplar.

### Reglas principales

- El socio debe estar habilitado para solicitar y recibir material.
- Las sedes involucradas deben estar activas.
- El ejemplar debe estar disponible y corresponder al libro solicitado.
- La sede propietaria debe coincidir con la sede de origen.
- Una solicitud genera como máximo un préstamo.
- El préstamo se crea al entregar, no al despachar.
- La fecha de vencimiento debe ser posterior a la entrega.
- La devolución se permite aunque el socio haya sido inhabilitado.
- La solicitud y el ejemplar deben bloquearse durante asignaciones o entregas concurrentes.

### Responsabilidades transversales

- Mantener el contrato de la API de circulación.
- Conservar los nombres de las relaciones acordados con el frontend.
- Coordinar las pruebas de recorridos completos.
- Implementar RP02: ranking de demanda interbibliotecaria, excluyendo solicitudes rechazadas y canceladas.

## Integrante 4: logística y trazabilidad

I4 es responsable de `apps/logistica`.

### Entidades

- `Remito`.
- `DetalleRemito`.
- `EventoRemito`.

### Patrón State

Estados previstos:

```text
EN_PREPARACION
EMPAQUETADO
DESPACHADO
EN_TRANSITO
RECIBIDO
CANCELADO
```

Cada clase de estado debe decidir qué operaciones permite. Un campo enumerado o un único bloque de condicionales no es suficiente para demostrar el patrón.

### Procesos

- Crear un remito.
- Agregar ejemplares durante la preparación.
- Empaquetar.
- Despachar.
- Registrar la salida.
- Recibir.
- Cancelar antes del despacho.
- Consultar el historial completo.

### Reglas principales

- Origen y destino diferentes y activos.
- Un remito no puede despacharse vacío.
- Un ejemplar no puede pertenecer a dos remitos vigentes.
- La sede propietaria del ejemplar se conserva.
- La sede actual pasa a `null` durante el tránsito.
- Cada transición genera un `EventoRemito`.
- La transición, el evento y los cambios de ejemplares se confirman conjuntamente.
- Una operación rechazada no deja cambios ni eventos parciales.

### Responsabilidades transversales

- Coordinar la integración entre Circulación y Logística.
- Mantener la documentación del patrón State.
- Preparar la evidencia de patrones para la presentación.
- Implementar RP03: envíos por origen/destino y tiempo promedio de tránsito de remitos recibidos.

## Decisiones que debe cerrar todo el grupo

Antes de completar Circulación y Logística, los cuatro integrantes deben acordar y documentar:

1. Dónde se devuelve un ejemplar.
2. Cómo regresa a su sede propietaria.
3. Qué sucede con operaciones ya iniciadas cuando una sede se da de baja.
4. Si la recepción de un remito debe ser completa o puede ser parcial.
5. Cómo se registra la condición física observada al recibir.
6. Qué prioridad y plazo tienen las reservas.
7. Cómo se detectan duplicados de libros sin ISBN.
8. Qué usuarios pueden habilitar, despachar, recibir y consultar reportes.

Las decisiones deben indicar la situación, la regla aceptada, ejemplos permitidos y prohibidos, y los estados o relaciones afectados.

## Dependencias entre módulos

```text
I1: Socios ───────────────────┐
                              ├──> I3: Circulación
I2: Catálogo y ejemplares ────┘            │
                                           v
                                  I4: Logística
```

I3 necesita Socios y Ejemplares para terminar el préstamo local. Mientras espera esas integraciones puede preparar modelos, contratos, Strategy y pruebas. I4 puede preparar Remito, EventoRemito y las clases State, pero debe coordinar con I3 las relaciones con solicitudes.

## Orden de integración recomendado

1. `feature/socios-backend`.
2. `feature/catalogo-modelos`.
3. `feature/catalogo-api`.
4. `feature/circulacion-modelos`.
5. `feature/circulacion-local`.
6. `feature/logistica-modelos`.
7. `feature/logistica-state`.
8. `feature/circulacion-interbibliotecaria`.
9. `feature/reservas`.
10. `feature/reportes`.

Conviene dividir las PR grandes en cambios pequeños y verificables. Los cambios de esquema que afecten a otro módulo deben acordarse antes de generar la migración.

## Revisiones cruzadas

- I1 revisa las PR de I3.
- I3 revisa las PR de I1.
- I2 revisa las PR de I4.
- I4 revisa las PR de I2.
- Circulación y Logística revisan conjuntamente cualquier cambio de estados o relaciones compartidas.

## Cronograma

### 16 al 22 de octubre

- I1: Socios completo y reglas de habilitación.
- I2: Catálogo, ejemplares y disponibilidad.
- I3: Solicitud local, préstamo, devolución y Strategy local.
- I4: Remito en preparación, empaquetado, cancelación y primeras clases State.

Objetivo: completar un préstamo local real y demostrar los rechazos principales.

### 23 al 29 de octubre

- I1: RP01 y apoyo a integración.
- I2: asignación de reservas, recepción/ubicación y RP04.
- I3: Strategy interbibliotecaria, reservas y RP02.
- I4: despacho, tránsito, recepción, historial y RP03.

Objetivo: completar un préstamo interbibliotecario y obtener una primera versión de los cuatro reportes.

### 30 de octubre al 5 de noviembre

- I1: despliegue desde un clon limpio y configuración de entrega.
- I2: revisión de integridad, modelos y migraciones.
- I3: pruebas completas de procesos y reportes.
- I4: integración final, documentación de patrones y guion de demostración.

### 6 al 9 de noviembre

Sólo se realizan correcciones, documentación, preparación de datos y ensayo de la demostración. No se agregan funcionalidades opcionales ni se cambia de tecnología.

## Definición de terminado

Una tarea de backend se considera terminada cuando:

- Cumple el requisito y las reglas de negocio asociadas.
- Incluye modelo y migración cuando corresponde.
- Incluye servicios transaccionales y consultas separadas.
- Expone serializers, vistas y rutas sin permitir atajos de estado.
- Tiene pruebas de éxito, rechazo y riesgo relevante.
- Fue verificada contra PostgreSQL.
- Swagger refleja el contrato real.
- La pantalla correspondiente puede usar la API real sin mezclar IDs del mock.
- Funciona dentro de Docker.
- Otro integrante revisó y aprobó la PR.

## Flujo de trabajo por tarea

1. Elegir una operación concreta y asociarla con su requisito.
2. Acordar estados previos, resultado, payload, respuesta, errores y permisos.
3. Implementar modelo y migración si falta persistencia.
4. Implementar servicio y selector.
5. Agregar serializer, vista y ruta.
6. Probar éxito, rechazos y concurrencia cuando corresponda.
7. Conectar la pantalla mockeada con el endpoint real.
8. Solicitar revisión y registrar cómo se verificó la aceptación.
