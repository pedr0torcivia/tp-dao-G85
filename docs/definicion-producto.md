# Definición del producto — v1

Fecha de elaboración: 9 de octubre de 2026. Entrega aproximada: 9 de noviembre de 2026.

## Problema y propósito

Una red de bibliotecas necesita controlar socios, libros y ejemplares, registrar préstamos y devoluciones y trasladar material entre sedes conservando la trazabilidad del remito.

El producto será una aplicación web que centralice estas operaciones y permita consultar disponibilidad por sede. El alcance sigue el Tema 1 del TP Integrador 2026 de Desarrollo de Aplicaciones con Objetos.

## Usuarios y experiencia mínima

| Usuario | Necesidad | Funcionalidad prevista |
|---|---|---|
| Personal de biblioteca | Administrar y atender a socios | Administrar registros, solicitudes, reservas, préstamos y devoluciones |
| Personal encargado de logística | Controlar envíos | Preparar remitos, empaquetar, despachar, recibir y consultar su historial |
| Responsable de la red | Conocer la operación | Consultar cuatro reportes con filtros y resultados verificables |
| Usuario o socio | Conocer disponibilidad | Consultar catálogo y ejemplares por sede |

Estos son perfiles funcionales, no cuatro tipos de cuenta obligatorios. Se propone autenticación de personal con Django; el detalle de permisos y la consulta pública del catálogo se decidirán en el sprint 1. Un socio registrado no necesita automáticamente una cuenta de acceso.

## Alcance de la primera entrega

| ID | Requisito | Criterio de aceptación mínimo |
|---|---|---|
| RF01 | Administrar sedes | Alta, consulta, modificación y baja lógica; dirección, contacto, horarios y estado |
| RF02 | Administrar socios | Alta, consulta, modificación y habilitación; detección de duplicados |
| RF03 | Administrar catálogo y ejemplares | Distinguir libro de copia física; identificar cada ejemplar y su sede propietaria |
| RF04 | Registrar solicitudes locales e interbibliotecarias | Registrar socio, material, origen y destino; seguir la solicitud hasta la entrega |
| RF05 | Gestionar remitos | Empaquetar, despachar y recibir; consultar eventos ordenados con fecha y responsable |
| RF06 | Consultar disponibilidad | Mostrar ejemplares disponibles y su sede, considerando asignaciones y tránsito |
| RF07 | Gestionar reservas | Registrar y consultar reservas; asignar disponibilidad, cumplir, cancelar y controlar expiración según la regla acordada |
| RF08 | Registrar devoluciones | Cerrar el préstamo y registrar condición física sin habilitar automáticamente material no apto |
| RF09 | Generar cuatro reportes | Obtener los indicadores definidos abajo, filtrarlos y comprobarlos con datos conocidos |
| RF10 | Aplicar dos patrones | Implementar y demostrar State y Strategy con clases y comportamiento identificables |
| RNF01 | Despliegue con Docker | Ejecutar frontend, backend y PostgreSQL con Docker Compose; construcción y arranque desde un clon limpio |

## Reglas obligatorias

1. No prestar ejemplares no disponibles ni material a socios inhabilitados.
2. Controlar las fechas de vencimiento de los préstamos.
3. Mantener la trazabilidad del remito durante todo el trayecto.
4. Evitar duplicados de socios, catálogo y ejemplares.
5. La sede de origen del préstamo debe coincidir con la sede a la que pertenece el ejemplar.
6. No iniciar préstamos, reservas ni envíos hacia o desde una sede dada de baja.

Las operaciones sobre un mismo ejemplar deben preservar estas reglas aun si dos solicitudes llegan simultáneamente. La validación de una pantalla no reemplaza la validación del backend ni las restricciones de la BD.

## Propuestas funcionales a validar

- Una solicitud refiere a un libro y admite un ejemplar asignado. Cada entrega genera como máximo un préstamo por solicitud.
- El préstamo comienza al entregar el material al socio; el transporte no consume el plazo de lectura.
- En solicitudes locales, origen y destino son la misma sede; en interbibliotecarias son diferentes.
- El préstamo registra la sede de origen propietaria y la sede de entrega mediante su solicitud, para no confundir pertenencia con ubicación temporal.
- La sede propietaria y la ubicación actual del ejemplar se distinguen. Durante tránsito, la ubicación actual puede no corresponder a una sede.
- El vencimiento se calcula a partir de las fechas y de la ausencia de devolución; no se duplica innecesariamente como estado persistido.
- Una reserva refiere a libro, socio y sede de retiro. La asignación concreta del ejemplar puede realizarse después.
- Un remito puede estar vacío en preparación; para empaquetarlo o despacharlo debe contener al menos un ejemplar.
- Cancelar un remito se permite antes de despacharlo. Las operaciones ya despachadas requieren un tratamiento acordado, conservando el historial.

## Decisiones pendientes del sprint 1

| Decisión | Resultado necesario |
|---|---|
| Devolución y retorno | Dónde se devuelve y cómo regresa el ejemplar a su sede propietaria |
| Reservas | Orden de atención, plazo de retiro y liberación de asignaciones |
| Recepción | Si se exige recibir el remito completo; la revisión especial de incidencias es opcional en la consigna |
| Sede dada de baja | Tratamiento de préstamos y envíos que ya estaban iniciados |
| Duplicados de catálogo | Identificación por edición/ISBN y criterio para registros sin ISBN |
| Habilitación de socios | Quién puede modificarla y qué reglas la determinan |
| Acceso | Autenticación de personal, permisos y acceso a consulta de disponibilidad |
| Fecha de entrega | Confirmar con la cátedra; 9/11/2026 es una fecha de planificación |

## Reportes comprometidos

| ID | Reporte | Indicadores y filtros |
|---|---|---|
| RP01 | Préstamos vencidos | Cantidad y días de atraso; detalle y agrupación por sede de entrega; fecha de corte explícita |
| RP02 | Demanda interbibliotecaria | Ranking de libros y cantidad de solicitudes, por fecha de solicitud y sede solicitante; excluir rechazadas y canceladas |
| RP03 | Movimiento entre sedes | Envíos despachados por origen/destino y tiempo promedio de tránsito de los recibidos; filtrar por fecha de despacho y usar despacho–recepción |
| RP04 | Disponibilidad por sede | Cantidad de ejemplares por libro, sede propietaria y estado; proporción disponible sobre el total; corte actual explícito |

Cada reporte deberá manejar resultados vacíos, explicar su criterio de conteo y tener un conjunto de datos cuyo resultado esperado esté calculado previamente. En RP03, los remitos aún no recibidos no forman parte del promedio; en RP04, un ejemplar prestado, asignado o en tránsito no cuenta como disponible.

Se elige disponibilidad como cuarto reporte para no depender de reglas opcionales de incidencias o de multas sin definir. Esta elección debe mantenerse consistente en el backlog y en la demostración.

## Diseño y tecnologías

```text
React + TypeScript
        ↓ API REST
Python + Django REST Framework
        ↓ servicios de aplicación y objetos del dominio
ORM de Django
        ↓
PostgreSQL
```

Aplicación modular con una única base de datos. Áreas: administración, catálogo, circulación, logística y reportes. La API recibe solicitudes y devuelve resultados; los servicios coordinan casos de uso y transacciones; las entidades y los patrones expresan las reglas del dominio.

- **State:** estados de Remito como clases con operaciones permitidas y transiciones controladas. El historial se persiste por separado. Un campo con valores enumerados no basta para demostrar el patrón.
- **Strategy:** tramitación local e interbibliotecaria mediante implementaciones intercambiables de un contrato común, con validaciones compartidas.
- Las actualizaciones de estados, historial y disponibilidad que pertenecen a una operación se confirman conjuntamente.
- El ORM de Django será el único responsable de modelos y migraciones. Prisma no forma parte del stack.
- Las versiones se fijarán durante el primer sprint, tras verificar compatibilidad.

## Despliegue obligatorio

Docker y Docker Compose son un requisito acordado, no una mejora opcional.

- Servicio de frontend: compilación de React y publicación de archivos estáticos mediante servidor HTTP.
- Servicio de backend: Django REST Framework con un servidor de aplicación apto para la entrega desplegada.
- Servicio de base de datos: PostgreSQL con almacenamiento persistente.
- Configuración por variables de entorno, ejemplo versionado y credenciales reales fuera del repositorio.
- Procedimiento documentado para construir, iniciar, aplicar migraciones y cargar datos de demostración.
- Verificación de que los servicios estén listos; el orden de arranque por sí solo no garantiza disponibilidad de la BD.
- Probar reinicio y conservación de datos, acceso al frontend, comunicación con API y conexión con PostgreSQL.

El destino de alojamiento público está pendiente. La entrega debe funcionar con Compose en el entorno acordado; no se presupone un proveedor de hosting. Durante desarrollo se podrá ejecutar React y Django localmente, conservando el despliegue completo en contenedores como requisito de aceptación.

## Fuera del alcance inicial

Notificaciones, recomendaciones, historial personal de lecturas, códigos de barras, multas, automatización de incidencias especiales, inicio de sesión para cada socio y mejoras visuales avanzadas. Solo se reconsiderarán si todos los requisitos obligatorios están terminados y revisados.

## Definición de éxito

La demostración recorre un préstamo local y otro interbibliotecario hasta la devolución, incluye una reserva y el historial de un remito, muestra rechazos de operaciones inválidas y presenta cuatro reportes comprobables. El equipo explica los dos patrones y levanta la aplicación desde un clon limpio mediante Docker Compose.

## Referencias

- Consigna: `C:/Users/Bangho/Downloads/tema1.pdf` (referencia local del usuario; todavía no está incorporada al repositorio).
- [Tablero de modelos](https://www.figma.com/board/aYOy4RyT0MaeW0a69ivvxJ/Modelos).
- [Repositorio](https://github.com/pedr0torcivia/tp-dao-G85).
