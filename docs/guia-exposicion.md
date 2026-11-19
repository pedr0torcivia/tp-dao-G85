# Guía de exposición de EntreLibros

Grupo 85 · Tema 1 Biblioteca · Versión para la defensa

EntreLibros administra préstamos y traslados en una red de bibliotecas. El libro identifica una obra o edición; el ejemplar es la copia física, con código de inventario, sede propietaria, ubicación actual, condición y estado. Una solicitud expresa la intención del socio. El préstamo nace cuando se entrega la copia. El remito documenta el transporte entre sedes.

## Preparación antes de exponer

Abrir Docker Desktop. Desde la raíz del proyecto ejecutar `if (-not (Test-Path .env)) { Copy-Item .env.example .env }`, luego `docker compose up -d --build --wait` y `docker compose exec backend python manage.py preparar_exposicion --reiniciar`. El último comando restablece los datos de biblioteca y la bitácora; conserva las cuentas. Abrir `http://localhost:5173` e ingresar con **biblioteca / demo**.

La base limpia contiene **20 títulos, 60 ejemplares (44 disponibles), 3 sedes, 4 socios, 22 solicitudes, 6 préstamos, 4 reservas y 7 remitos**. Central y Norte están activas; Sur está de baja. Las obras son reales; socios, sedes, inventarios y movimientos son datos de demostración.

## Recorrido principal de 15 minutos

1. Mostrar **Catálogo** y **Ejemplares**. Buscar *Star Wars Vol. 1: Skywalker Strikes*: EXPO-001 está disponible, EXPO-002 prestado y vencido, EXPO-003 disponible en Norte. Esto distingue obra de copia y permite explicar disponibilidad.
2. Abrir **Solicitudes** y comparar *Naruto Vol. 1* (Maretto, Central → Central) con *Jujutsu Kaisen Vol. 1* (Fanfliet, Norte → Central). Ambas están asignadas. Pulsar **Preparar entrega** en cada una: Naruto pasa a lista para entregar; Jujutsu Kaisen crea o incorpora la copia a un remito. La diferencia es Strategy.
3. Abrir **Remitos**. Usar el remito de *X-Men: Days of Future Past*, **EN_PREPARACION**, para empaquetar; luego despachar y recibir. Mostrar cómo cambian los botones permitidos y el historial. La diferencia entre los estados es State. Abrir el remito ya recibido de *Wolverine*: llegó dañado y la solicitud volvió a pendiente.
4. Abrir la solicitud local de Naruto y **Registrar entrega** con vencimiento futuro. Mostrar que recién ahora existe un préstamo y que la copia figura PRESTADO. En **Préstamos**, usar *Spider-Man: Kraven’s Last Hunt* para registrar una devolución apta: la copia queda EN_REVISION; aprobar disponibilidad desde su ficha cuando corresponda.
5. En **Ejemplares**, dar de alta DEFENSA-001 para *Batman: Year One* en Central. Consultarlo, editar su condición a NO_APTO y darlo de baja. En **Reportería**, mostrar **Disponibilidad por sede** y **Bitácora de operaciones** para comprobar alta, modificación y baja lógica.

Si falta tiempo, priorizar los puntos 1, 2, 3 y 5. Cada demostración puede restablecerse con `preparar_exposicion --reiniciar`.

<!-- page -->

# Casos listos para abrir

| Caso | Qué demuestra |
|---|---|
| EXPO-001 · Skywalker Strikes | Préstamo local completo, desde solicitud hasta devolución y revisión. |
| EXPO-002 · Skywalker Strikes | Préstamo vencido de Torcivia: multa y bloqueo de nuevos pedidos. |
| EXPO-006 · Civil War | Remito ENV-2026-001 en tránsito; recibir conforme, dañado o extraviado. |
| EXPO-009 · Infinity Gauntlet | Remito recibido; copia lista para entregar en Central. |
| EXPO-011 · Batman: Year One | Ejemplar NO_APTO en revisión: no puede prestarse. |
| EXPO-017 · All Star Superman | Baja lógica de un ejemplar. |
| EXPO-020 · Batman: The Dark Knight Returns | Devolución en Norte de una copia de Central; retorno entre sedes. |
| EXPO-025 · Naruto Vol. 1 | Solicitud local ASIGNADA: Strategy deja la copia lista en mostrador. |
| EXPO-030 · Jujutsu Kaisen Vol. 1 | Solicitud interbibliotecaria ASIGNADA: Strategy inicia logística. |
| EXPO-033 · X-Men: The Dark Phoenix Saga | Remito EMPAQUETADO: reabrir, despachar o cancelar. |
| EXPO-034 · X-Men: Days of Future Past | Remito EN_PREPARACION: agregar, quitar, empaquetar o cancelar. |
| EXPO-037 · Wolverine | Remito RECIBIDO_CON_INCIDENCIAS, copia dañada y solicitud pendiente. |
| EXPO-043 a 045 · Iron Man: Extremis | Remito CANCELADO: estado final, sin operaciones posteriores. |
| EXPO-048 · Thor: God of Thunder | Segundo préstamo vencido de Torcivia, en otra sede. |
| EXPO-049 · Captain America: Winter Soldier | Devolución dañada; copia NO_APTO en revisión. |
| EXPO-054 · Spider-Man: Kraven’s Last Hunt | Préstamo vigente en Norte para demostrar devolución. |
| EXPO-055 · Batman: Hush | Reserva lista para retiro: entregar al socio. |
| EXPO-058 · Hawkeye | Reserva expirada: se canceló la solicitud y se liberó la copia. |

Otras variantes: *Deadpool* tiene una solicitud local pendiente, una reserva cancelada y copias disponibles; *Batman: The Killing Joke* tiene una solicitud rechazada. *Civil War* conserva una reserva pendiente. La sede Sur está de baja y no admite nuevos trámites. La numeración de remitos creados durante la demostración depende del año y de los ensayos previos; buscarlos por libro y estado.

## Estados que conviene explicar

**Solicitud:** PENDIENTE → ASIGNADA → LISTA_PARA_ENTREGA → CUMPLIDA en el circuito local. Entre sedes, después de asignar pasa por el remito y EN_TRASLADO antes de estar lista. Puede rechazarse o cancelarse antes de entregar.

**Ejemplar:** DISPONIBLE → ASIGNADO → LISTO_PARA_ENTREGA → PRESTADO → EN_REVISION → DISPONIBLE. En traslado pasa por EN_TRANSITO. Si está dañado queda NO_APTO en revisión; BAJA conserva el registro histórico.

**Remito:** EN_PREPARACION → EMPAQUETADO → EN_TRANSITO → RECIBIDO o RECIBIDO_CON_INCIDENCIAS. EMPAQUETADO puede reabrirse; se puede cancelar antes del despacho. Cada cambio registra fecha y responsable.

**Reserva:** PENDIENTE → LISTA_PARA_RETIRO → CUMPLIDA. También puede quedar CANCELADA o EXPIRADA; ambas liberan la copia apartada.

# Reglas, patrones y arquitectura

## Reglas de negocio para defender

Solo un socio habilitado puede pedir o retirar material. Si tiene préstamos vencidos sin devolver, se bloquean nuevas solicitudes, reservas y entregas. Solo se asigna una copia disponible y apta de la sede de origen. El préstamo empieza con la entrega al socio, dura como máximo 60 días y una devolución no puede ser anterior a la entrega. Cada día de atraso acumula $150 de multa.

Una solicitud entre sedes requiere remito recibido antes de la entrega. La devolución deja la copia en revisión, aunque esté apta. Una copia devuelta fuera de su sede propietaria debe regresar por remito; hasta entonces no se habilita. Una reserva separa una copia en la sede de retiro con un plazo; si vence, libera el ejemplar. Las bajas son lógicas para conservar trazabilidad.

## Por qué Strategy y State

**Strategy** se usa porque una solicitud local y una entre sedes comparten la intención de préstamo, pero su preparación cambia: mostrador frente a traslado documentado. El mismo botón **Preparar entrega** ejecuta el recorrido correspondiente al tipo de solicitud. Permite agregar otro modo de tramitación sin mezclar todas las reglas en un único flujo.

**State** se usa porque las acciones válidas de un remito dependen de su estado actual. Un remito en preparación puede cambiar contenido; uno empaquetado puede reabrirse o despacharse; uno en tránsito solo se recibe. Cada estado gobierna sus operaciones y efectos. La ficha muestra el estado, las acciones disponibles y el historial.

## Arquitectura y roles

La aplicación tiene tres capas de ejecución: **React + TypeScript** en el navegador, **API Django REST Framework** con servicios de dominio y persistencia mediante **ORM de Django + PostgreSQL**. Docker Compose inicia frontend, backend y base. El backend separa catálogo, sedes, socios, circulación, logística, reportes y auditoría. Las validaciones de negocio se aplican en el backend y las operaciones relacionadas se guardan en transacciones.

Bibliotecario y socio son **roles del dominio**, no dos tipos de cuenta del sistema: el personal autenticado opera toda la red y un socio es una entidad administrada, sin acceso propio. La sede seleccionada organiza el trabajo, no limita permisos. Hay cuenta de personal para la demostración y un superusuario administra cuentas desde Django Admin. Librerías principales: React, React Router, Vite, Tailwind CSS, Django, Django REST Framework, psycopg y drf-spectacular; Playwright y Vitest verifican el frontend.

# Reportería · Tema 1

Los siete informes consultan datos reales del backend. Todos exigen **Desde** y **Hasta** válidos; pueden filtrarse y exportarse a CSV o imprimirse/guardarse como PDF desde el navegador. Elegir el rango según el caso: **01/10/2026 a 31/10/2026** para los hechos históricos preparados, o **el día de la exposición** para las operaciones nuevas y su bitácora.

| Informe | Para qué sirve |
|---|---|
| Préstamos activos y material en tránsito | Distingue copias entregadas de copias que todavía viajan. |
| Préstamos vencidos y multas | Muestra morosidad, días de atraso y monto acumulado. |
| Libros más pedidos entre sedes | Mide demanda interbibliotecaria por libro y sede solicitante; excluye cancelados y rechazados. |
| Disponibilidad por sede | Muestra el estado actual de las copias dadas de alta en el rango, agrupadas por obra y sede propietaria. No es una reconstrucción histórica del stock. |
| Envíos exitosos e incidencias | Compara recepciones conformes con dañadas o extraviadas. |
| Movimiento entre sedes | Cuenta despachos por trayecto y tiempos de recepción de viajes terminados. |
| Bitácora de operaciones | Comprueba escrituras exitosas de la API: fecha, usuario, entidad y cambio antes/después. Las consultas no aparecen. |

**Demostración de reportes:** abrir Disponibilidad por sede con Desde 01/10/2026 y Hasta la fecha actual: en la base limpia muestra **44 de 60** disponibles. Crear DEFENSA-001 apto: pasa a **45 de 61**. Cambiarlo a NO_APTO: **44 de 61**, con una copia más en revisión. Darlo de baja: el total sigue en 61 y esa copia aparece en BAJA. Luego abrir Bitácora de operaciones con Desde y Hasta iguales al día de la demostración: mostrar ALTA, MODIFICACION y BAJA del mismo ejemplar y exportar CSV o imprimir.

Con corte **31/10/2026**, Torcivia tenía dos préstamos con **19 y 7 días** de atraso. Los remitos históricos incluyen **tres despachos y dos recepciones**. Naruto y Jujutsu Kaisen concentran pedidos entre sedes. La bitácora registra cambios de la API; restablecer la base antes de repetir cifras exactas.
