# Plan de cierre del grupo 85

Tema 1 Biblioteca. Fecha de planificación de entrega: 9 de noviembre de 2026, a confirmar con la cátedra.

## Integrantes

| Legajo | Integrante |
|---|---|
| 400879 | Fanfliet Juan Ignacio |
| 400091 | Torcivia Pedro |
| 400193 | Dalmazzo Francisco Gaston |
| 400140 | Maretto Agustin |

Las responsabilidades finales se distribuyen entre los cuatro integrantes. Cada uno debe poder explicar el modelo y ambos patrones.

## Cierre funcional

El alcance vigente está en `reglas-negocio.md`. La versión integrada debe completar préstamo local, préstamo interbibliotecario con retorno, reserva, devolución, historial de remitos y cuatro reportes contra la base real.

## Revisión y entrega

1. Revisar `integration/cierre-tp` entre integrantes y fusionar a `main`.
2. Ejecutar la verificación con PostgreSQL y los recorridos del navegador.
3. Ejecutar `scripts/verificar-docker.ps1` desde un clon limpio y comprobar persistencia.
4. Ensayar `guion-demostracion.md`, incluyendo rechazos de operaciones inválidas y cálculos de reportes.
5. Presentar el documento del grupo, el DER actualizado y la explicación de State y Strategy.
6. Confirmar fecha oficial, formato de entrega y acceso al repositorio.

## Criterio de terminado

La funcionalidad debe persistir sus cambios, cumplir las validaciones de la consigna, superar las pruebas relevantes y poder ser explicada y revisada por otro integrante. Las limitaciones de verificación se registran expresamente en `verificacion-entrega.md`.
