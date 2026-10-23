# Roadmap de integración a main

Fecha: 23 de octubre de 2026. Responsable: I4 (coordinación de integración).

Plan verificado con un dry-run real de las cuatro fusiones sobre `origin/main` (cada merge ejecutado, conflictos resueltos y suite completa corrida). Complementa la [distribución del backend](distribucion-backend.md).

## Estado final

La integración se completó en la rama `integration/todas-ramas`, en este orden:

1. `feature/socios-backend` → merge limpio.
2. `feature/catalogo-backend` → merge limpio; adaptación de sus pruebas al enum `CondicionFisica` vigente (drift de base, ver F1).
3. `feature/circulacion-local` → merge con conflicto trivial en `config/urls.py`.
4. `feature/logistica-remitos` → merge con conflictos en `config/urls.py` y `apps/reportes/*` (coexisten RP01 y RP03).

Además se cerró el alcance del enunciado en esta rama:

- RP02 y RP04 (reportes que no estaba implementados).
- Reservas: servicios y API con los comandos del contrato del frontend.
- Baja de ejemplar y aprobación de disponibilidad (bajas lógicas vía estado).

Fixes de integración aplicados a código de otros integrantes:

- RP01 (I1): la vista no leía el parámetro `fecha_corte` de la request.
- Tests de catálogo (I2): valores de texto libre del enum viejo → `APTO`/`NO_APTO`.

Verificación: 149 tests en verde contra PostgreSQL, `makemigrations --check` sin cambios, ruff limpio.

## Estado de las ramas (verificado)

| Rama | Punto de divergencia | Commits propios | Archivos que toca |
|---|---|---|---|
| `feature/socios-backend` | `df308e2` | 1 | `apps/socios/*`, `apps/reportes/*`, `config/urls.py` |
| `feature/catalogo-backend` | `df308e2` | 6 | `apps/catalogo/*` (sin models), `README.md`, `config/urls.py` |
| `feature/circulacion-local` | `c2e957f` (main actual) | 2 | `apps/circulacion/*` (sin models), `config/urls.py` |
| `feature/logistica-remitos` | `c2e957f` (main actual) | 5 | `apps/logistica/*`, `apps/reportes/*`, `config/urls.py` |

Como cada rama toca su propio módulo, **no hay conflicto de esquema ni de modelos**: todos los cambios de `models.py` y migraciones ya están en main (`df308e2` y `c2e957f`).

## Resultado del dry-run de merges (en el orden 1→4)

1. `socios-backend` → ✅ merge limpio.
2. `catalogo-backend` → ✅ merge limpio (pero falla en tests, ver F1).
3. `circulacion-local` → ⚠️ conflicto único: `config/urls.py` (trivial: conservar todos los `include`).
4. `logistica-remitos` → ⚠️ conflicto en `config/urls.py` + `apps/reportes/urls.py` + `apps/reportes/views.py` (RP01 y RP03 coexisten: combinar `urlpatterns` y conservar ambas vistas).

Suite post-merge: **114 tests, 97 en verde, 17 fallidos — todos en `apps.catalogo.tests`**, por el hallazgo F1.

## Hallazgos que hay que cerrar ANTES de integrar

- **F1 — Drift de contrato de `CondicionFisica` (I2).** La rama de catálogo se hizo sobre `df308e2`, cuando el enum admitía valores como `Bueno` y `Muy bueno`. El commit de base `c2e957f` (ya en main) lo unificó a `APTO` / `NO_APTO`. El merge es limpio pero sus 17 tests rompen contra el modelo nuevo. Lo que corresponde es que **I2 adapte servicios, serializers y tests al enum vigente** (la base ya está confirmada porque Logística y Circulación ya dependen de `APTO/NO_APTO`). Este es el único bloqueo real.
- **F2 — Bug latente en RP01 (I1).** `reportes/views.py` (rama socios) declara la vista pero nunca lee `request.GET`; la primera línea `date.fromisoformat(fecha_corte)` falla con `NameError`. Arreglar en la rama antes del PR (agregar el parseo con `request.GET.get("fecha_corte")`).
- **F3 — Alcance del enunciado** (cerrado en la rama de integración): RP02 (demanda interbibliotecaria), RP04 (disponibilidad por sede), servicios/API de reservas y acción de baja de ejemplar quedaron implementados en `integration/todas-ramas` con sus pruebas. Sigue en backlog la trazabilidad fuera del remito y la Strategy interbibliotecaria de Circulación apuntando al traslado real.

## Plan de integración (por qué orden y cómo)

Orden recomendado igual al de la distribución: I1 → I2 → I3 → I4. Aunque el orden es intercambiable (ramas independientes), así cada revisor cross ve su módulo primero.

Para cada paso:

1. El responsable de la rama crea PR → `main` (o la Integration la crea junto al responsable).
2. El revisor cruzado aprueba (I2 revisa PRs de I4 y viceversa; I1 con I3).
3. Merge `--no-ff` a main con el conflicto esperado resuelto según la tabla del dry-run.
4. Verificación mínima post-merge en main antes de seguir con la siguiente rama:
   - `python manage.py makemigrations --check --dry-run` (que no haya migraciones pendientes).
   - Suite contra PostgreSQL subida con Docker (`docker compose up -d db`). Los tests de concurrencia requieren PostgreSQL; SQLite sólo para iterar rápido.
   - `GET /api/schema/` responde (Swagger refleja las rutas nuevas de esa rama).
5. Sólo cuando el paso está verde en main, seguir con la siguiente rama.

### Paso 1 · I1: socios
- PR con la corrección F2 incluida.
- Conflicto esperado: ninguno.
- Verde si: tests de `socios`, `sedes` y `reportes.prestamos-vencidos` pasan en PostgreSQL.

### Paso 2 · I2: catálogo
- Bloqueado por F1: primero su PR de adaptación al enum, luego la integración.
- Conflicto esperado: ninguno (su rama no toca `models.py`).
- Verde si: los 17 tests de catálogo pasan en PostgreSQL.

### Paso 3 · I3: circulación local
- Conflicto esperado: `config/urls.py` (agregar `include("apps.circulacion.urls")` a lo ya merged).
- Verde si: tests de circulación + ciclo completo de préstamo local en PostgreSQL.

### Paso 4 · I4: logística (mi rama)
- Conflictos esperados: `config/urls.py` (sumar `logistica` y `reportes`) y `apps/reportes/{urls,views}.py` (coexistir RP01 y RP03). Resolver así: mantener ambas importaciones, ambos `urlpatterns` y ambas vistas en `views.py`.
- Verde si: suite completa (≥114 tests) en verde en PostgreSQL, ciclo de remito completo por `test_api` y RP03 contra su fixture.

### Paso 5 · Cierre de integración
- Clonar desde un clon limpio (I1 hace la verificación transversal).
- Alzar `docker compose up` y verificar el flujo end-to-end real con el front: `VITE_DATA_SOURCE=http`, préstamo local completo, remito armado en pantalla.
- Actualizar los docs de distribución si cambian estados de módulos.
- Borrar las ramas locales de features que queden y hacer tag de la versión integrada (opcional).

## Verificación de lo que la integración NO resuelve (backlog)

Sumar estos ítems al backlog del grupo para no perderlos:

1. RP02 — demanda interbibliotecaria (I3, depende del traslado ya implementado en I4).
2. RP04 — disponibilidad por sede (I2).
3. Reservas: serviços y API (I3; el modelo ya está).
4. Acción de baja de ejemplar `BAJA` (I2; hoy el estado es inalcanzable).
5. Trazabilidad de cambios de estado fuera del remito (decisión de grupo: por ahora sólo el remito bitacora eventos).
6. Estrategia interbibliotecaria de Circulación apuntando al traslado real de Logística (I3 + I4).

## Definición de terminado de la integración

- [ ] Cuatro ramas merged a main, una PR por rama, revisada por el par cross.
- [ ] Suite completa en verde contra PostgreSQL desde un run sobre main integrada.
- [ ] `makemigrations --check --dry-run` sin salida.
- [ ] Swagger refleja: socios, catalogo, circulacion, logistica y los dos reportes.
- [ ] Flujo de préstamo local completo demostrable con datos reales (no mock) desde el front.
- [ ] F1..F3 cerrados o registrados en el backlog con responsable.
