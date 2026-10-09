# Plan de proyecto — v1

## Horizonte y capacidad

- Inicio de planificación: **9 de octubre de 2026**.
- Entrega aproximada: **9 de noviembre de 2026**, pendiente de confirmar con la cátedra.
- Equipo: **4 integrantes**, identificados como I1–I4 hasta asignar nombres.
- Dedicación: **6–8 horas semanales por persona**; **24–32 horas de equipo por semana**.
- Cuatro sprints: **96–128 horas humanas en total**, incluyendo coordinación, revisión, pruebas y documentación.
- Reservar aproximadamente un 20% para integración, correcciones y preparación de entrega. La capacidad no equivale íntegramente a horas de programación.
- El 6–9 de noviembre será un margen final; no se comprometen nuevas funcionalidades ni horas extra durante ese período.

La IA asistirá el trabajo, pero no se multiplica la capacidad por un factor de productividad supuesto. Se ajustará el alcance de las tareas y su tamaño según resultados reales; no se eliminarán procesos obligatorios, patrones, reportes o Docker para compensar atrasos.

## Producto y decisiones

El alcance y los criterios de aceptación se encuentran en [la definición del producto](definicion-producto.md). Se mantienen React + TypeScript, Django REST Framework, ORM de Django y PostgreSQL. El despliegue completo con Docker Compose es obligatorio.

Se prioriza una interfaz sencilla, operaciones completas y evidencia de reglas de negocio. Se aprovechará Django Admin para reducir trabajo en administración cuando sea suficiente, sin omitir los procesos exigidos ni usarlo para saltar transiciones controladas.

## Responsabilidades

| Integrante | Área principal | Responsabilidad transversal | Revisor habitual |
|---|---|---|---|
| I1 | Sedes y socios | Entorno compartido y Docker Compose | I3 |
| I2 | Catálogo y ejemplares | Consistencia del esquema y migraciones | I4 |
| I3 | Solicitudes, préstamos y reservas | Contrato API y Strategy | I1 |
| I4 | Remitos y trazabilidad | State y coordinación de integración | I2 |

Cada responsable construye el backend y la interfaz mínima de su área; puede recibir apoyo. Logística y circulación se revisan conjuntamente. Los reportes se reparten uno por integrante: I1 RP01, I2 RP04, I3 RP02, I4 RP03. Todos deben poder explicar los patrones, el modelo y el despliegue.

## Sprint 1 — 9 al 15 de octubre

**Objetivo:** cerrar reglas prioritarias y obtener la base ejecutable del producto, incluido un primer despliegue con Docker.

| Responsable | Trabajo principal | Resultado verificable |
|---|---|---|
| I1 | Inicializar proyecto y Compose; sedes y socios básicos | Frontend, API y PostgreSQL levantan; altas básicas por interfaz mínima o Admin |
| I2 | Modelos de catálogo, autor y ejemplar; migraciones y datos iniciales | Libros con copias identificables y sedes propietarias; migraciones desde una BD vacía |
| I3 | Contrato API de circulación; esqueleto Strategy | Entradas, respuestas y errores acordados; dos estrategias con contrato común |
| I4 | Modelo de remitos y eventos; esqueleto State | Transiciones acordadas y estructura de clases; evento inicial del remito |

Trabajo conjunto: resolver retorno, reserva, baja de sedes y acceso; revisar FigJam frente a modelos; fijar versiones; dividir backlog en tareas pequeñas. No generar toda la aplicación antes de validar estos acuerdos.

**Cierre:** un compañero levanta el entorno desde instrucciones escritas; datos básicos se guardan en PostgreSQL y sobreviven a un reinicio. Las reglas pendientes que bloquean circulación o logística quedan resueltas y documentadas.

## Sprint 2 — 16 al 22 de octubre

**Objetivo:** completar un préstamo local y demostrar las validaciones más importantes.

| Responsable | Trabajo principal | Resultado verificable |
|---|---|---|
| I1 | Habilitación de socios, baja de sedes y permisos acordados | Operaciones inválidas rechazadas por el backend |
| I2 | Consulta de catálogo/disponibilidad y asignación segura | Dos solicitudes simultáneas no asignan el mismo ejemplar |
| I3 | Solicitud local, entrega y devolución; Strategy local | Circuito local completo desde React hasta PostgreSQL |
| I4 | Preparación, empaquetado y cancelación de remitos | State controla transiciones; cambios dejan historial |

**Cierre:** crear solicitud, entregar, consultar vencimiento y devolver registrando condición física. Mostrar rechazos por socio inhabilitado, sede de baja, ejemplar no disponible y origen incorrecto. Repetir el circuito en el entorno Docker actualizado.

## Sprint 3 — 23 al 29 de octubre

**Objetivo:** completar el préstamo interbibliotecario, las reservas y una primera versión de los cuatro reportes.

| Responsable | Trabajo principal | Resultado verificable |
|---|---|---|
| I1 | RP01 y datos para vencimientos; apoyo a integración | Cantidades y días de atraso comprobables por sede |
| I2 | Reserva/asignación junto a I3; recepción/ubicación junto a I4; RP04 | Disponibilidad consistente durante asignación, tránsito y devolución |
| I3 | Strategy interbibliotecaria; completar reservas; RP02 | Solicitud llega a entrega; reserva se cumple/cancela/expira según regla acordada |
| I4 | Despacho, tránsito, recepción e historial; RP03 | Remito recorre el ciclo completo y tiempos de tránsito se calculan correctamente |

**Cierre:** enviar un ejemplar entre dos sedes, recibirlo, entregarlo y devolverlo siguiendo la política acordada. Verificar historial y disponibilidad. Los cuatro reportes tienen cálculo y salida mínima; la presentación final puede completarse en sprint 4.

## Sprint 4 — 30 de octubre al 5 de noviembre

**Objetivo:** cerrar requisitos, validar reportes y preparar una entrega reproducible.

| Responsable | Trabajo principal | Resultado verificable |
|---|---|---|
| I1 | Prueba de despliegue desde clon limpio; configuración de entrega | Build, arranque, migraciones, datos y persistencia comprobados con Compose |
| I2 | Revisión de integridad y consistencia de modelos | Clases, DER, estados y migraciones representan el mismo producto |
| I3 | Pruebas de procesos y cuatro reportes junto a sus responsables | Resultados contrastados con un conjunto de datos de referencia |
| I4 | Integración final; documentación de patrones y guion de demostración | Evidencia de State/Strategy y recorrido de demostración completo |

**Cierre:** todos los requisitos obligatorios pasan su criterio de aceptación; cuatro reportes funcionan en la interfaz; cada integrante explica su área y ambos patrones. No quedan fallos que impidan completar un proceso principal o levantar el despliegue.

## Margen final — 6 al 9 de noviembre

Corregir fallos encontrados, ensayar presentación, preparar archivos y revisar instrucciones de entrega. Evitar cambios de tecnología, nuevas funcionalidades y refactorizaciones amplias. Si aparece un bloqueo, el grupo prioriza resolverlo y comunica el impacto real sobre la fecha.

## Trabajo con IA y human in the loop

Para cada tarea se seguirá este ciclo:

1. **Humano define:** resultado esperado, regla de negocio, límites y ejemplos de aceptación.
2. **IA prepara:** propuesta acotada de diseño/código/pruebas/documentación, usando el modelo y la versión de dependencias acordados.
3. **Responsable revisa:** lee el cambio, comprueba que entiende el comportamiento y corrige supuestos o requisitos inventados.
4. **Se verifica:** ejecutar los casos relevantes; revisar migraciones y efectos sobre estados, disponibilidad e historial.
5. **Otro integrante revisa e integra:** contrastar contra la issue y dejar evidencia de validación en la PR.

La IA puede acelerar tareas repetitivas, formular consultas de reportes, preparar fixtures y proponer pruebas. Las reglas del producto, la aceptación de cálculos y la integración final las decide el grupo. Si la IA encuentra una ambigüedad, se registra y resuelve; no se transforma silenciosamente en una regla nueva.

En la PR se indicará brevemente qué se cambió, cómo se verificó y qué decisión humana fue relevante. No hace falta conservar conversaciones enteras. Los resultados esperados de reportes deben comprobarse independientemente de la consulta generada.

## Backlog y seguimiento

Usar un tablero de GitHub con **Pendiente → En curso → En revisión → Terminado**. Las issues se crearán cuando el grupo valide este plan; este documento no implica que ya estén publicadas.

Cada issue contendrá: requisito RF/RNF/RP asociado, responsable, resultado esperado, criterio de aceptación, dependencias y estimación pequeña. Como guía, dividir tareas mayores a 2–4 horas de ejecución humana para permitir revisión dentro de la dedicación semanal.

- Inicio de sprint: 20 minutos para elegir tareas, revisar capacidad y dependencias.
- Durante la semana: actualización breve y asíncrona del tablero; informar bloqueos al detectarlos.
- Cierre: 30 minutos para demostración y revisión; registrar mejoras concretas para el siguiente sprint.
- El tiempo de reuniones y revisiones está incluido en las 6–8 horas de cada integrante.
- Una tarea principal en curso por persona; ayudar a terminar o revisar antes de acumular trabajo.
- Cambios en ramas breves, por ejemplo `codex/prestamo-local` si se usa la convención de este entorno; la convención del equipo puede acordarse en sprint 1.
- Integrar mediante PR revisada por otro integrante; evitar una integración única al final del mes.

## Definición de terminado

- Cumple el criterio de aceptación y las reglas de la consigna.
- Funciona integrada con API y PostgreSQL; si incluye interfaz, se verificó desde ella.
- Tiene pruebas relevantes para su riesgo: transiciones, validaciones, concurrencia y cálculos cuando correspondan.
- Incluye migraciones y datos de referencia si modificó persistencia.
- Funciona en Docker cuando afecta el entorno desplegado.
- Fue revisada por un compañero; no basta con que la IA declare que funciona.
- Documentación y modelos actualizados cuando cambió una decisión de dominio.

## Riesgos y respuesta

| Riesgo | Respuesta |
|---|---|
| Alcance grande para 96–128 horas | Mantener interfaz mínima; excluir opcionales; revisar avance al cierre de cada sprint |
| Docker consume tiempo al final | Tener un despliegue básico en sprint 1 y probarlo durante los cuatro sprints |
| Código generado no coincide con el dominio | Tareas acotadas, criterios explícitos, revisión humana y pruebas de comportamiento |
| Migraciones o API incompatibles entre integrantes | Acordar contrato y coordinar cambios de esquema antes de integrarlos |
| Doble asignación de un ejemplar | Transacciones, coordinación sobre el ejemplar y verificación de concurrencia |
| Patrones solo nominales | Mostrar comportamiento distribuido entre clases y ejemplos de operaciones permitidas/prohibidas |
| Reportes incorrectos | Definiciones de conteo, fechas y denominadores; datos con resultado esperado independiente |
| Reglas pendientes retrasan desarrollo | Resolver las que bloquean en sprint 1; documentar cambios y su impacto |

## Entregables

1. Aplicación React + Django REST Framework con PostgreSQL.
2. Dockerfiles, Compose y configuración de ejemplo para despliegue obligatorio.
3. Migraciones y datos reproducibles para la demostración.
4. Diagrama de clases, DER y máquinas de estado consistentes con la implementación.
5. Dos patrones explicados con referencias a sus clases y ejemplos.
6. Cuatro reportes y evidencia de comprobación de resultados.
7. README con comandos verificados, instrucciones de uso y guion de demostración.
8. Repositorio con cambios integrados y revisión humana trazable.

## Próximo paso

Asignar nombres a I1–I4, resolver las decisiones funcionales pendientes y transformar el sprint 1 en issues concretas. Las cuentas y roles en GitHub, el proveedor de alojamiento y la fecha oficial de la cátedra aún deben confirmarse.
