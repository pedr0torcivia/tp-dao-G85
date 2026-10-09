# TP DAO — Grupo 85

Sistema de préstamos interbibliotecarios para una red de bibliotecas.

## Documentación

- [Definición del producto](docs/definicion-producto.md)
- [Plan de proyecto y sprints](docs/plan-proyecto.md)
- [Modelos compartidos en FigJam](https://www.figma.com/board/aYOy4RyT0MaeW0a69ivvxJ/Modelos)

## Decisiones acordadas

- Frontend: React + TypeScript.
- Backend: Python + Django REST Framework.
- Persistencia: ORM de Django + PostgreSQL.
- Despliegue obligatorio: Docker + Docker Compose para frontend, backend y base de datos.
- Equipo: 4 integrantes, con 6–8 horas semanales por integrante.
- Forma de trabajo: sprints, asistencia de IA y revisión humana de decisiones y cambios.
- Entrega aproximada: **9 de noviembre de 2026**.

La definición funcional y los modelos están en propuesta v1. Las reglas pendientes se resolverán al comienzo del primer sprint.

## Estado

La estructura inicial del backend está implementada y verificada. Incluye Django REST Framework, configuración para PostgreSQL, módulos del dominio, documentación OpenAPI, endpoint de salud, pruebas y contenedores para backend y base de datos. El frontend todavía no fue inicializado.

## Inicio rápido del backend y PostgreSQL

Crear el archivo local de configuración y levantar los servicios:

```powershell
Copy-Item .env.example .env
docker compose up --build
```

Una vez iniciados:

- API: `http://localhost:8000/api/`
- Estado: `http://localhost:8000/api/health/`
- Swagger: `http://localhost:8000/api/docs/`
- Administración: `http://localhost:8000/admin/`

Los comandos para ejecutar y comprobar el backend sin contenedores se encuentran en [`backend/README.md`](backend/README.md).

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
