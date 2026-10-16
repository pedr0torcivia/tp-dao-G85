# Guía para levantar el proyecto completo

Esta guía explica cómo ejecutar el frontend, el backend y la base de datos del
proyecto **TP DAO — Grupo 85**.

La forma recomendada para todo el equipo es Docker Compose, porque utiliza las
mismas versiones y la misma configuración en todas las computadoras.

## 1. Tecnologías utilizadas

- Frontend: React, TypeScript y Vite.
- Backend: Python 3.13, Django 5.2 y Django REST Framework.
- Base de datos: PostgreSQL 17.
- ORM y migraciones: Django ORM.
- Contenedores: Docker y Docker Compose.

## 2. Requisitos para la opción recomendada

Cada integrante debe instalar:

1. Git.
2. Docker Desktop.

Docker Desktop debe estar iniciado antes de ejecutar los comandos. No hace
falta instalar Python, Node.js ni PostgreSQL si se trabaja exclusivamente con
Docker.

Para comprobar las instalaciones:

```powershell
git --version
docker --version
docker compose version
```

## 3. Primera descarga del repositorio

Clonar el repositorio y entrar en su carpeta:

```powershell
git clone <URL-DEL-REPOSITORIO>
cd tp-dao-G85
```

Cada integrante debe reemplazar `<URL-DEL-REPOSITORIO>` por la URL HTTPS o SSH
del repositorio del grupo.

Crear el archivo local de configuración:

```powershell
Copy-Item .env.example .env
```

El archivo `.env` contiene valores de desarrollo y no debe subirse al
repositorio.

## 4. Levantar frontend, backend y PostgreSQL con Docker

Desde la raíz del repositorio:

```powershell
docker compose up --build
```

La primera ejecución puede demorar porque Docker descarga las imágenes e
instala las dependencias. El backend espera a PostgreSQL y ejecuta las
migraciones automáticamente antes de iniciar.

Cuando los servicios estén listos:

| Servicio | Dirección |
|---|---|
| Frontend | <http://localhost:5173> |
| API | <http://localhost:8000/api/> |
| Estado del backend | <http://localhost:8000/api/health/> |
| Swagger | <http://localhost:8000/api/docs/> |
| Django Admin | <http://localhost:8000/admin/> |
| PostgreSQL | `localhost:5432` |

Para dejar los contenedores ejecutándose en segundo plano:

```powershell
docker compose up --build -d
```

Comprobar el estado:

```powershell
docker compose ps
```

Ver los registros de todos los servicios:

```powershell
docker compose logs -f
```

Ver únicamente los registros del backend:

```powershell
docker compose logs -f backend
```

Detener los servicios sin borrar los datos:

```powershell
docker compose down
```

## 5. Modo mock y modo integrado del frontend

El frontend puede utilizar datos simulados o consumir la API real.

### Datos simulados

Es el modo predeterminado y permite trabajar en la interfaz aunque todavía
falten endpoints del backend:

```env
VITE_DATA_SOURCE=mock
```

### API real

Para probar la integración completa, editar el archivo `.env` de la raíz:

```env
VITE_DATA_SOURCE=http
```

Luego reconstruir el frontend, porque las variables de Vite se aplican durante
la compilación:

```powershell
docker compose build frontend
docker compose up -d
```

En este modo el navegador utiliza `/api` y Nginx redirige las peticiones al
contenedor del backend.

Si todavía no están implementados todos los endpoints que solicita el
frontend, algunas pantallas pueden fallar en modo `http`. En ese caso se puede
continuar desarrollando con `mock` y probar los endpoints terminados desde
Swagger.

## 6. Actualizar el proyecto después de un cambio en `main`

Antes de comenzar una tarea nueva:

```powershell
git switch main
git pull origin main
git switch -c feature/nombre-de-la-tarea
```

Si la rama de trabajo ya existe:

```powershell
git switch nombre-de-la-rama
git fetch origin
git rebase origin/main
```

Después de descargar cambios que modifiquen dependencias, migraciones o
Dockerfiles, reconstruir:

```powershell
docker compose up --build -d
```

## 7. Comandos habituales del backend en Docker

Ejecutar comprobaciones de Django:

```powershell
docker compose exec backend python manage.py check
```

Aplicar migraciones manualmente:

```powershell
docker compose exec backend python manage.py migrate
```

Crear migraciones de una aplicación después de modificar sus modelos:

```powershell
docker compose exec backend python manage.py makemigrations circulacion
```

La migración generada debe revisarse y subirse al repositorio junto con el
cambio del modelo.

Comprobar que no falten migraciones:

```powershell
docker compose exec backend python manage.py makemigrations --check --dry-run
```

Ejecutar las pruebas compatibles con el runner de Django:

```powershell
docker compose exec backend python manage.py test
```

Crear un usuario para Django Admin:

```powershell
docker compose exec backend python manage.py createsuperuser
```

Abrir una consola interactiva de Django:

```powershell
docker compose exec backend python manage.py shell
```

## 8. Revisar PostgreSQL

Los valores predeterminados se encuentran en `.env`:

```text
Base de datos: biblioteca
Usuario: biblioteca
Contraseña: biblioteca
Host desde Windows: localhost
Puerto: 5432
```

Abrir la consola de PostgreSQL dentro del contenedor:

```powershell
docker compose exec database psql -U biblioteca -d biblioteca
```

Comandos útiles dentro de `psql`:

```text
\dt
\d sedes_sede
SELECT * FROM django_migrations ORDER BY applied DESC;
\q
```

También se puede usar DBeaver, pgAdmin u otro cliente con las credenciales
anteriores.

Los datos se guardan en el volumen Docker `postgres_data`, por lo que no se
eliminan al ejecutar `docker compose down`.

### Reiniciar completamente la base de datos

El siguiente comando elimina todos los datos locales. Solo debe utilizarse
cuando realmente se quiera reconstruir la base desde cero:

```powershell
docker compose down -v
docker compose up --build -d
```

## 9. Desarrollo local sin ejecutar toda la aplicación en Docker

Esta opción es útil para tener recarga rápida y ejecutar herramientas de
desarrollo. Requiere Python 3.13 y Node.js 24 o versiones compatibles.

### 9.1 Levantar solamente PostgreSQL

Desde la raíz:

```powershell
docker compose up -d database
```

### 9.2 Backend local

En una terminal, desde la raíz:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements\development.txt
python manage.py migrate
python manage.py runserver
```

La configuración local utiliza PostgreSQL en `localhost:5432` de forma
predeterminada.

Si PowerShell impide activar el entorno virtual, puede habilitarse solamente
para la terminal actual:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

Para ejecutar las comprobaciones completas del backend local:

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
python -m pytest
ruff check .
ruff format --check .
```

### 9.3 Frontend local

En una segunda terminal, desde la raíz:

```powershell
cd frontend
Copy-Item .env.example .env.local
npm ci
npm run dev
```

Para consumir el backend real, configurar `frontend/.env.local` así:

```env
VITE_DATA_SOURCE=http
VITE_API_BASE_URL=/api
```

Vite enviará las peticiones `/api` al backend local en
`http://127.0.0.1:8000`.

Pruebas y compilación del frontend:

```powershell
npm test
npm run build
```

## 10. Problemas frecuentes

### Docker no está disponible

Comprobar que Docker Desktop esté iniciado:

```powershell
docker info
```

### Un puerto ya está ocupado

Los puertos utilizados son `5173`, `8000` y `5432`. Revisarlos con:

```powershell
Get-NetTCPConnection -State Listen | Where-Object LocalPort -In 5173,8000,5432
```

Cerrar la aplicación que utiliza el puerto o detener otro conjunto de
contenedores antes de volver a iniciar el proyecto.

### El backend no inicia

Revisar primero:

```powershell
docker compose ps
docker compose logs backend
docker compose logs database
```

Los errores más frecuentes son migraciones incompatibles, variables faltantes
o PostgreSQL todavía no disponible.

### Los cambios del frontend no aparecen en Docker

La imagen contiene una compilación estática. Reconstruirla:

```powershell
docker compose build frontend
docker compose up -d frontend
```

Para desarrollo diario del frontend es más rápido utilizar `npm run dev`.

### Los cambios del backend no aparecen en Docker

El código se copia al construir la imagen y Gunicorn no tiene recarga
automática. Reconstruir el servicio:

```powershell
docker compose build backend
docker compose up -d backend
```

Para desarrollo diario del backend es más rápido utilizar
`python manage.py runserver`.

## 11. Lista rápida de verificación

Antes de informar que un cambio está listo:

1. Actualizar la rama con `main`.
2. Levantar los tres servicios.
3. Abrir el frontend.
4. Comprobar `/api/health/`.
5. Revisar el endpoint modificado en Swagger.
6. Ejecutar las pruebas correspondientes.
7. Confirmar que no falten migraciones.
8. No incluir archivos `.env`, `.venv`, `node_modules` ni datos locales en el
   commit.
