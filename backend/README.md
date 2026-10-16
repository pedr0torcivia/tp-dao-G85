# Backend

API del sistema de préstamos interbibliotecarios construida con Django y Django REST Framework.

## Módulos

- `common`: comportamiento transversal, errores y endpoint de salud.
- `sedes`: administración y baja lógica de las bibliotecas.
- `socios`: socios, habilitación y detección de duplicados.
- `catalogo`: libros, autor como dato bibliográfico, ejemplares y disponibilidad.
- `circulacion`: solicitudes, préstamos, reservas y devoluciones.
- `logistica`: remitos, eventos y trazabilidad.
- `reportes`: consultas agregadas de la entrega.

Cada módulo incorporará sus modelos, servicios, selectores, serializers, vistas y pruebas a medida que se implementen sus casos de uso. Las reglas de negocio no deben depender de las vistas HTTP.

El esquema relacional se implementa con modelos y migraciones de Django. Para generar una base SQLite local, configurar `$env:DJANGO_USE_SQLITE = "true"` y ejecutar `python manage.py migrate`.

## Desarrollo local

Desde `backend/`, en PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements\development.txt
python manage.py migrate
python manage.py runserver
```

La configuración predeterminada espera PostgreSQL en `localhost:5432`. Las variables disponibles están documentadas en `../.env.example`.

## Comprobaciones

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
python -m pytest
ruff check .
ruff format --check .
```

Para pruebas unitarias aisladas que no requieren PostgreSQL:

```powershell
$env:DJANGO_USE_SQLITE = "true"
python -m pytest
```

SQLite es solo una facilidad para pruebas rápidas. El desarrollo integrado y el despliegue utilizan PostgreSQL.

## Rutas iniciales

- `GET /api/`: información básica de la API.
- `GET /api/health/`: comprobación de disponibilidad.
- `GET /api/schema/`: contrato OpenAPI.
- `GET /api/docs/`: interfaz Swagger.
- `/admin/`: administración de Django.

## Catálogo

El módulo `catalogo` administra libros, ejemplares y la disponibilidad por sede.

```http
GET   /api/libros/
POST  /api/libros/
GET   /api/libros/{id}/
PATCH /api/libros/{id}/

GET   /api/ejemplares/
POST  /api/ejemplares/
GET   /api/ejemplares/{id}/
PATCH /api/ejemplares/{id}/
POST  /api/ejemplares/{id}/asignar/
POST  /api/ejemplares/{id}/liberar/

GET   /api/disponibilidad/
```

La lista de libros admite `?search=` para buscar por título, autor o ISBN. La lista
de ejemplares admite `?libro_id=`, `?sede_id=` y `?estado=`. El reporte de
disponibilidad devuelve cantidades totales, disponibles, no disponibles y
proporción disponible por sede; también acepta `libro_id` y `sede_id`.

Los ejemplares se crean como `DISPONIBLE`, con su sede actual igual a la sede
propietaria. Las operaciones de asignar y liberar usan transacciones y bloquean
la fila para impedir asignaciones simultáneas del mismo ejemplar.
