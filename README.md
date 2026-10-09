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

Planificación inicial. Todavía no se implementaron la aplicación ni el despliegue. Los comandos de instalación, ejecución y prueba se incorporarán cuando estén verificados.

## Formato de commits

Se utiliza el mismo formato observado en enCuota: `TIPO(Área): Descripción en español`.

- `ADD`: agregar funcionalidad o archivos.
- `UPD`: actualizar comportamiento o contenido.
- `FIX`: corregir errores.
- `REF`: refactorizar.
- `DEL`: eliminar contenido.
- `TEST`: agregar o modificar pruebas.
- `INTEGRATE`: integrar trabajo de módulos.

Ejemplos: `ADD(Doc): Agregar definición del producto y plan de proyecto`, `ADD(Arch): Configurar despliegue con Docker` y `FIX(Prestamo): Impedir préstamos de ejemplares no disponibles`.
