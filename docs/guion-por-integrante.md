# Guion hablado por integrante · Grupo 85

Exposición de unos 16 minutos, dividida en cuatro bloques de 4 minutos. Cada bloque dice **qué decir** (texto para leer o adaptar), **qué hacer en pantalla** y **qué responder si preguntan**. Los casos y cifras salen de la base limpia de [preparar_exposicion](guia-exposicion.md).

| Bloque | Integrante | Tema | Tiempo |
|---|---|---|---|
| 1 | Fanfliet Juan Ignacio | Presentación, arquitectura y dominio | 0:00 – 4:00 |
| 2 | Torcivia Pedro | Circulación y patrón **Strategy** | 4:00 – 8:00 |
| 3 | Dalmazzo Francisco Gaston | Logística y patrón **State** | 8:00 – 12:00 |
| 4 | Maretto Agustin | Reportería, bitácora y cierre | 12:00 – 16:00 |

> La distribución es una propuesta: si alguien domina mejor otro tema, intercambien bloques. Cada integrante tiene que poder explicar el modelo y los dos patrones, así que conviene que todos lean el guion completo.

## Antes de empezar (10 minutos antes)

1. Abrir Docker Desktop y, desde la raíz del proyecto:

   ```powershell
   docker compose up -d --wait
   docker compose exec backend python manage.py preparar_exposicion --reiniciar
   ```

2. Abrir `http://localhost:5173`, ingresar con **biblioteca / demo** y dejar la sede **Biblioteca Central** seleccionada.
3. Dejar abiertas dos pestañas extra: `http://localhost:5173/exposicion.html` (apoyo visual) y [patrones.md](patrones.md) (por si piden ver código).
4. Una sola persona maneja el mouse por bloque: el que habla. Al pasar de bloque, decir el nombre del siguiente.

---

## Bloque 1 · Fanfliet — Presentación, arquitectura y dominio

**Qué decir**

> "Buenas, somos el grupo 85: Juan Ignacio Fanfliet, Pedro Torcivia, Francisco Dalmazzo y Agustín Maretto. Elegimos el Tema 1, Biblioteca, y construimos **EntreLibros**, un sistema para administrar préstamos y traslados en una red de bibliotecas.
>
> La arquitectura tiene tres capas. En el navegador, **React con TypeScript**. En el servidor, una **API en Django REST Framework**, donde viven las reglas de negocio en servicios de dominio. Y la persistencia es **PostgreSQL** a través del ORM de Django. Todo se levanta con **Docker Compose**: frontend, backend y base.
>
> La distinción más importante del dominio es entre **libro** y **ejemplar**. El libro es la obra o edición; el ejemplar es la copia física, con su código de inventario, la sede propietaria, dónde está ahora, su condición y su estado. Se pide un libro, pero se presta un ejemplar."

**Qué hacer en pantalla**

1. Mostrar la pantalla de inicio: mesa de trabajo de la sede.
2. Ir a **Catálogo** y buscar *Star Wars Vol. 1: Skywalker Strikes*.
3. Abrir sus ejemplares y señalar:
   - **EXPO-001**: disponible en Central.
   - **EXPO-002**: prestado y **vencido**.
   - **EXPO-003**: disponible en **Norte**.

> "Una misma obra, tres copias, tres situaciones distintas. Por eso la disponibilidad se calcula por ejemplar y por sede.
>
> Otro concepto clave: la **solicitud** es la intención del socio; el **préstamo** recién nace cuando se entrega la copia; y el **remito** documenta el transporte entre sedes. Pedro les va a mostrar cómo se tramita una solicitud."

**Si preguntan**

- *¿Por qué separaron solicitud y préstamo?* Porque entre el pedido y la entrega puede haber un traslado de días. Si el préstamo empezara al pedir, el plazo correría mientras el libro viaja.
- *¿Hay roles de usuario?* Bibliotecario y socio son roles del dominio. El personal autenticado opera toda la red; el socio es una entidad administrada, sin cuenta propia.
- *¿Por qué bajas lógicas?* Para conservar la trazabilidad: un ejemplar dado de baja sigue en el historial de préstamos y remitos.

---

## Bloque 2 · Torcivia — Circulación y patrón Strategy

**Qué decir**

> "Una solicitud puede ser **local**, cuando el socio retira en la misma sede donde está la copia, o **interbibliotecaria**, cuando la copia tiene que viajar. Las dos comparten la intención, pedir un libro, pero se preparan de forma muy distinta. Ahí aplicamos el patrón **Strategy**."

**Qué hacer en pantalla**

1. Ir a **Solicitudes**. Mostrar dos solicitudes **ASIGNADAS**:
   - *Naruto Vol. 1*: Maretto, Central → Central (local).
   - *Jujutsu Kaisen Vol. 1*: Fanfliet, Norte → Central (interbibliotecaria).
2. En **Naruto**, pulsar **Preparar entrega**: queda **LISTA_PARA_ENTREGA**, en mostrador.
3. En **Jujutsu Kaisen**, pulsar el **mismo botón**: la copia se incorpora a un **remito** en preparación.

> "Es el mismo botón y el mismo método, `preparar_entrega`, pero el resultado es distinto. El servicio no pregunta por el tipo de solicitud: le pide a una fábrica la estrategia que corresponde, `TramitacionLocal` o `TramitacionInterbibliotecaria`, y la ejecuta. Si mañana agregamos envío a domicilio, es una clase nueva y una entrada en la fábrica, sin tocar los servicios."

4. Volver a Naruto y pulsar **Registrar entrega** con un vencimiento futuro (por ejemplo, 14 días).

> "Recién ahora existe el préstamo y la copia figura **PRESTADO**. El plazo máximo es de 60 días."

5. Ir a **Préstamos**, abrir *Spider-Man: Kraven's Last Hunt* (EXPO-054, en Norte) y registrar una **devolución apta**.

> "Aunque vuelva apta, la copia queda **EN_REVISION**: alguien de la biblioteca la revisa antes de volver a prestarla."

6. **Regla de morosidad:** mostrar en **Préstamos vencidos** o en la ficha del socio que *Torcivia Pedro* tiene dos préstamos vencidos (Skywalker Strikes en Central y Thor en Norte).

> "Y como soy el socio moroso del escenario: con préstamos vencidos sin devolver, el sistema me bloquea nuevas solicitudes, reservas y entregas. Cada día de atraso suma $150 de multa. La copia de Jujutsu Kaisen quedó en un remito: Francisco les muestra qué pasa con él."

**Si preguntan**

- *¿Dónde está el código?* `backend/apps/circulacion/strategies/`. La fábrica es `obtener_estrategia(tipo)`.
- *¿Por qué no un `if` por tipo?* Porque las reglas de cada circuito (validación al crear, preparación, recorrido de estados) quedarían mezcladas en un solo método que crece con cada caso nuevo.
- *¿Qué pasa si se devuelve en otra sede?* La copia tiene que volver a su sede propietaria por remito; hasta entonces no se habilita. *The Dark Knight Returns* (EXPO-020) muestra ese caso.

---

## Bloque 3 · Dalmazzo — Logística y patrón State

**Qué decir**

> "El remito documenta el traslado de copias entre sedes. Lo que se puede hacer con un remito depende de en qué estado está: uno en preparación se puede modificar, uno en tránsito sólo se puede recibir. Para eso aplicamos el patrón **State**."

**Qué hacer en pantalla**

1. Ir a **Remitos** y abrir el de *X-Men: Days of Future Past* (Central → Norte), en **EN_PREPARACION**.

> "Fíjense en los botones: agregar, quitar, empaquetar o cancelar. La interfaz no decide qué botones mostrar: los pide a la API, que los calcula a partir de la clase del estado actual."

2. Pulsar **Empaquetar**: aparecen **Reabrir** y **Despachar**.
3. Pulsar **Despachar**: sólo queda **Recibir**. La copia pasa a **EN_TRANSITO** y no tiene sede actual.

> "Cancelar ya no se ofrece, y si alguien lo intentara directo contra la API, el estado lo rechaza con un error de transición inválida."

4. Pulsar **Recibir** y marcar la copia como **conforme**: el remito queda **RECIBIDO**.
5. Mostrar el **historial**: cada transición con fecha y responsable.
6. Abrir el remito de *Wolverine*: está en **RECIBIDO_CON_INCIDENCIAS**.

> "Este llegó dañado. La copia quedó no apta y la solicitud volvió a **PENDIENTE**, para asignar otra copia. Y *Iron Man: Extremis* muestra un remito **CANCELADO**, que es un estado final: no admite ninguna operación más."

> "En el código, `Remito` es el contexto; `EstadoRemitoBase` declara las siete operaciones y por defecto las rechaza; y cada estado concreto redefine sólo las que admite y ejecuta sus efectos. El único punto que cambia el estado es `remito.transicionar`, que además registra el evento. Agustín cierra con los reportes."

**Si preguntan**

- *¿Dónde está el código?* `backend/apps/logistica/states.py` (estados) y `models.py` (contexto).
- *¿Cómo se relacionan los dos patrones?* Strategy decide cómo se tramita la solicitud; en el caso interbibliotecario entrega la copia a un remito, y desde ahí manda State.
- *¿Cómo saben qué botones mostrar?* `operaciones_admitidas()` detecta qué métodos redefine cada clase de estado; la API lo expone como `acciones`.
- *¿Cómo lo probaron?* `apps/logistica/tests/test_states.py` verifica que cada estado admite exactamente sus operaciones, y `frontend/e2e/circuitos.spec.ts` recorre los circuitos desde el navegador.

---

## Bloque 4 · Maretto — Reportería, bitácora y cierre

**Qué decir**

> "La reportería tiene **siete informes** que consultan la base real. Todos piden un rango **Desde / Hasta**, se pueden filtrar por sede y exportar a CSV o imprimir como PDF. Voy a mostrar cómo reflejan un cambio en vivo."

**Qué hacer en pantalla**

1. **Reportería → Disponibilidad por sede**, con Desde **01/10/2026** y Hasta **hoy**: muestra **44 de 60** disponibles.
2. Ir a **Ejemplares** y dar de alta **DEFENSA-001** para *Batman: Year One* en Central, condición apta. Volver al informe: **45 de 61**.
3. Editar DEFENSA-001 y cambiar la condición a **NO_APTO**: **44 de 61**, con una copia más en revisión.
4. Dar de **baja** DEFENSA-001: el total sigue en **61** y la copia aparece como **BAJA**.

> "La baja es lógica: el ejemplar no desaparece, cambia de estado."

5. **Bitácora de operaciones**, con Desde y Hasta iguales a **hoy**: aparecen el **ALTA**, la **MODIFICACION** y la **BAJA** de DEFENSA-001, con usuario y valores antes y después. Exportar a CSV.

> "La bitácora registra cada escritura exitosa de la API, con quién la hizo y qué cambió. Las consultas no se registran."

6. Recorrer rápido otros tres informes:
   - **Préstamos vencidos y multas**, de 01/10/2026 a 31/10/2026: los dos préstamos de Torcivia, con **19 y 7 días** de atraso y **$3.900** de multa en total.
   - **Libros más pedidos entre sedes**: *Naruto* y *Jujutsu Kaisen* encabezan el ranking.
   - **Envíos exitosos e incidencias**: 4 envíos, 1 dañado (Wolverine).

**Cierre**

> "En resumen: EntreLibros cubre el circuito completo, desde el pedido hasta la devolución y el retorno de la copia a su sede, con trazabilidad en cada paso. Aplicamos **Strategy** para la forma de tramitar una solicitud y **State** para el ciclo de vida del remito, y los dos se ven directamente en la interfaz. Todo está cubierto con pruebas de backend y recorridos de navegador. Muchas gracias; quedamos a disposición para preguntas."

**Si preguntan**

- *¿Disponibilidad es histórica?* No: muestra el estado actual de las copias dadas de alta en el rango. No reconstruye el stock de una fecha pasada.
- *¿Cómo se calcula la multa?* $150 por día calendario de atraso, desde el vencimiento hasta la fecha de corte del informe.
- *¿Qué cuenta como disponible?* Estado DISPONIBLE, condición apta, ubicada en su sede propietaria y con esa sede activa.

---

## Si algo sale mal

- **Un botón no aparece o un caso ya fue usado en un ensayo:** reiniciar los datos (tarda unos segundos y conserva las cuentas):

  ```powershell
  docker compose exec backend python manage.py preparar_exposicion --reiniciar
  ```

- **La página no carga:** `docker compose ps` para ver que los tres contenedores estén `healthy`; si no, `docker compose up -d --wait`.
- **Se cierra la sesión:** volver a ingresar con **biblioteca / demo**; la aplicación vuelve a la pantalla en la que estaban.
- **Falta tiempo:** priorizar Strategy (bloque 2, pasos 1–3), State (bloque 3, pasos 1–4) y la disponibilidad con bitácora (bloque 4, pasos 1–5).
