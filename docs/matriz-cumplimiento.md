# Matriz de cumplimiento — Grupo 85

Tema 1: Biblioteca. Referencia: `Enunciado.pdf`, TP Integrador 2026. Revisión: 1 de noviembre de 2026. El alcance obligatorio está implementado; los resultados ejecutados se registran en `verificacion-entrega.md`.

## Procesos obligatorios

| Proceso de la consigna | Implementación | Evidencia |
|---|---|---|
| 1. Administrar sedes | Alta, consulta, edición, baja lógica y reactivación; dirección, contacto, horarios y estado | `apps/sedes/tests/test_api.py`, `test_services.py` y `test_models.py`; pantalla Sedes |
| 2. Administrar socios | Alta, consulta, edición, habilitación e inhabilitación; documento y número únicos | `apps/socios/`; los circuitos crean socios por API y validan su habilitación en circulación |
| 3. Administrar libros y ejemplares | Libro con autor, ISBN y edición; ejemplar con inventario, propietaria, ubicación y condición | `apps/catalogo/tests/test_api.py`; alta de libro y persistencia en Chrome |
| 4. Solicitudes locales e interbibliotecarias | Flujo completo hasta entrega, con origen y destino; Strategy selecciona el trámite | `apps/circulacion/tests/test_api.py`, `test_services.py`, `test_interbibliotecaria.py`, `test_strategies.py`; dos recorridos en Chrome |
| 5. Empaquetar, despachar y recibir con remito trazable | State controla transiciones; historial con fecha, responsable y observación; remito de retorno | `apps/logistica/tests/`; circuito interbibliotecario con ida y retorno en Chrome |
| 6. Consultar disponibilidad | Listas y filtros por libro y sede; solo material apto, disponible y en propietaria activa | `apps/common/tests/test_circuitos.py`, pruebas de catálogo y RP04 |
| 7. Gestionar reservas | Crear, consultar, asignar con límite futuro, cumplir, cancelar y expirar; liberar copia al cancelar o expirar | `apps/circulacion/tests/test_reservas.py`; reserva cumplida en Chrome |
| 8. Registrar devoluciones y condición física | Cierre del préstamo; registro APTO/NO_APTO y revisión; retorno a propietaria sin crear otro préstamo | `apps/common/tests/test_circuitos.py`, circulación y recorridos local e interbibliotecario en Chrome |

Las rutas de las pruebas de esta matriz son relativas a `backend/`, salvo las de Chrome, que están en `frontend/e2e/`.

## Validaciones de negocio

| Validación obligatoria | Control y evidencia |
|---|---|
| No prestar ejemplares no disponibles | Servicios de catálogo y circulación; bloqueo de fila y pruebas de asignación concurrente en PostgreSQL |
| No prestar a socios inhabilitados | Validación central del socio en solicitudes, reservas y entrega; `test_reglas.py` y `test_reservas.py` |
| Controlar vencimientos | Vencimiento posterior a entrega, devolución no anterior a entrega, reserva con fecha límite futura; RP01 con corte histórico |
| Trazabilidad de remito durante todo el trayecto | Transiciones mediante State; `EventoRemito` persistido junto al cambio; pruebas de ciclo completo e historial |
| Evitar duplicados de socios, catálogo y ejemplares | Restricciones de BD y errores de API: documento/número, ISBN o edición normalizada sin ISBN e inventario único |
| Propietaria del ejemplar igual al origen del préstamo | Validación al asignar y entregar; separación de propietaria y ubicación actual en modelo y DER |
| No iniciar operaciones desde/hacia sedes dadas de baja | Validación de sedes en solicitudes, reservas, asignaciones y remitos; se permite cerrar recepciones/devoluciones ya iniciadas |

## Patrones y reportes

| Obligación | Implementación y prueba |
|---|---|
| Patrón State | Clases de estados del remito en `apps/logistica/states.py`; transiciones válidas e inválidas en `test_states.py` y `test_services.py` |
| Patrón Strategy | Estrategias de trámite local e interbibliotecario en `apps/circulacion/strategies/`; selección y comportamiento en `test_strategies.py` |
| RP01: préstamos vencidos | Corte histórico, atraso en días y agrupación por sede de entrega; pruebas con devolución posterior al corte |
| RP02: demanda interbibliotecaria | Ranking por libro y sede solicitante en rango; excluye canceladas y rechazadas |
| RP03: movimientos | Despachos por trayecto y promedio de días de tránsito de recibidos; despacho/recepción contrastados |
| RP04: disponibilidad | Altas del período, totales y proporción disponible por libro, propietaria y estado actual; sin reconstrucción histórica |
| RP05: comprobación ABMC | Escrituras exitosas de la API, fecha, usuario y cambios; transacción compartida con la operación |

Los cinco reportes se calculan en el backend y se consultan desde el frontend con rango Desde/Hasta obligatorio, exportación CSV e impresión/PDF. Los valores de referencia se contrastan con datos conocidos en `apps/common/tests/test_circuitos.py` y se explican en `guion-demostracion.md`. `patrones.md` contiene la explicación para la defensa.

## Acceso, despliegue y documentación

| Elemento | Estado |
|---|---|
| Acceso de personal | Credenciales reales, sesiones, cierre, rutas privadas y protección CSRF; 14 pruebas específicas y dos recorridos de navegador |
| Docker Compose | Frontend Nginx, backend Gunicorn y PostgreSQL, comprobaciones de salud y volumen persistente; construcción y reinicio verificados |
| Datos reproducibles | `cargar_demo` no borra ni restablece datos y crea la cuenta de demostración solo si no existe |
| Modelo | Diez entidades del dominio; DER A4 con relaciones y cardinalidades, imagen y presentación del grupo |
| Documentación | Guías de arranque, acceso, reglas, esquema, patrones, guion y verificación |
| Integrantes | Los cuatro nombres y legajos constan en `plan-proyecto.md` y la presentación |

## Entrega y defensa

La aplicación y la documentación están preparadas para la revisión del grupo. La publicación/fusión de la rama y el workflow remoto quedan registrados como pasos de entrega, no como funcionalidad faltante. Confirmar con la cátedra fecha, mecanismo de entrega y acceso al repositorio; ensayar la defensa con los cuatro integrantes.

Los procesos opcionales de la consigna —notificaciones, historial de lecturas, recomendaciones, códigos de barras y tratamiento especial de extravíos o destrucción— no son requisitos pendientes de esta entrega. Se registra la condición física obligatoria en la devolución.

El escenario de exposición contiene 44 obras y 132 copias con portadas locales, con un caso preparado para cada estado de solicitud, reserva, préstamo y remito (ver `catalogo-exposicion.md`). La guía PDF detalla ABMC, casos y cálculos. `apps/common/tests/test_exposicion.py` verifica la bitácora, los límites de fechas, la carga y el efecto de las bajas en los reportes.
