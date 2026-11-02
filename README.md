# TP DAO — Grupo 85

Sistema de préstamos interbibliotecarios para una red de bibliotecas.

## Documentación

- [Guía de exposición en PDF](docs/Guia-exposicion-grupo-85.pdf)
- [Guía de exposición editable](docs/guia-exposicion.md)
- [Catálogo y casos preparados](docs/catalogo-exposicion.md)
- [Documentos de reportes](docs/reportes-referencia/)

- [Matriz de cumplimiento del enunciado](docs/matriz-cumplimiento.md)
- [Presentación del grupo](docs/Presentacion-grupo-85.docx)
- [DER A4 para descargar](docs/DER-grupo-85-A4.png)
- [Acceso y cuentas de personal](docs/acceso.md)
- [Definición del producto](docs/definicion-producto.md)
- [Plan de proyecto y sprints](docs/plan-proyecto.md)
- [Distribución del trabajo del backend](docs/distribucion-backend.md)
- [Guía para levantar el proyecto completo](docs/guia-levantar-proyecto.md)
- [DER A4 con relaciones](https://www.figma.com/board/aYOy4RyT0MaeW0a69ivvxJ/Modelos?node-id=100-1715)
- [Modelos compartidos en FigJam](https://www.figma.com/board/aYOy4RyT0MaeW0a69ivvxJ/Modelos)

## Decisiones acordadas

- Frontend: React + TypeScript.
- Backend: Python + Django REST Framework.
- Persistencia: ORM de Django + PostgreSQL.
- Despliegue obligatorio: Docker + Docker Compose para frontend, backend y base de datos.
- Equipo: 4 integrantes, con 6–8 horas semanales por integrante.
- Forma de trabajo: tareas breves, revisión entre integrantes y pruebas de integración.
- Entrega aproximada: **9 de noviembre de 2026**.

Las reglas operativas vigentes se describen en `docs/reglas-negocio.md`.

## Estado

La aplicación integra React con la API y PostgreSQL, con autenticación de personal y sesiones protegidas. Incluye sedes, socios, catálogo, préstamos locales e interbibliotecarios, reservas, devolución y retorno de ejemplares, remitos con historial y cinco reportes consultados en el backend. El modo de demostración sin servidor se habilita únicamente con `VITE_DATA_SOURCE=mock`.

Los cinco reportes exigen Desde y Hasta, permiten CSV e impresión/PDF e incluyen una bitácora que comprueba altas, modificaciones, bajas y operaciones. RP04 filtra altas del período y muestra su estado actual; RP05 muestra la fecha y los cambios de cada escritura de la API.

La documentación de cierre está en [Reglas y alcance](docs/reglas-negocio.md), [Patrones](docs/patrones.md), [Guion de demostración](docs/guion-demostracion.md) y [Verificación](docs/verificacion-entrega.md).

## Cómo ejecutar el sistema con Docker

Requisitos: Git, Docker y Docker Compose. En Windows, iniciar Docker Desktop con contenedores Linux antes de ejecutar los comandos.

Desde la raíz del repositorio, crear el archivo local de configuración si todavía no existe y levantar frontend, backend y PostgreSQL:

```powershell
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
docker compose up --build
```

Una vez iniciados:

- Aplicación: `http://localhost:5173/`
- API: `http://localhost:8000/api/`
- Estado: `http://localhost:8000/api/health/`
- Swagger: `http://localhost:8000/api/docs/`
- Administración: `http://localhost:8000/admin/`

Los comandos para ejecutar y comprobar el backend sin contenedores se encuentran en [`backend/README.md`](backend/README.md).

Las migraciones del backend se aplican automáticamente al iniciar su contenedor. El frontend usa la API real por defecto y guarda las operaciones en PostgreSQL. Para cargar ejemplos reproducibles, ejecutar `docker compose exec backend python manage.py preparar_exposicion`. El comando no borra ni restablece cambios existentes. También crea la cuenta de personal **biblioteca / demo** si no existe; usarla en el formulario de acceso. Para otras cuentas y cambio de clave, consultar [Acceso](docs/acceso.md).

Para detener los servicios, presionar `Ctrl+C`. Para retirar los contenedores, ejecutar desde la raíz del repositorio:

```powershell
docker compose down
```

Los datos de PostgreSQL se conservan en un volumen de Docker.

Para ejecutar la verificación automatizada desde PowerShell, usar `./scripts/verificar-docker.ps1`. Para preparar el ZIP del código y la documentación de entrega, usar `./scripts/empaquetar-entrega.ps1`; se genera `output/Entrega-grupo-85.zip`, sin `.env`, dependencias instaladas ni datos locales.

### Ejecutar solo el frontend sin Docker

Con Node.js y npm instalados, desde la raíz del repositorio:

```powershell
cd frontend
npm ci
npm run dev
```

Abrir la dirección que muestre Vite en la terminal (por defecto, `http://127.0.0.1:5173/`). Este modo usa la API local en el puerto 8000. Para explorar sin backend, configurar explícitamente `VITE_DATA_SOURCE=mock` en `frontend/.env`.

## Formato de commits

Se utiliza el siguiente formato: `TIPO(Área): Descripción en español`.

- `ADD`: agregar funcionalidad o archivos.
- `UPD`: actualizar comportamiento o contenido.
- `FIX`: corregir errores.
- `REF`: refactorizar.
- `DEL`: eliminar contenido.
- `TEST`: agregar o modificar pruebas.
- `INTEGRATE`: integrar trabajo de módulos.

Ejemplos: `ADD(Doc): Agregar definición del producto y plan de proyecto`, `ADD(Arch): Configurar despliegue con Docker` y `FIX(Prestamo): Impedir préstamos de ejemplares no disponibles`.
