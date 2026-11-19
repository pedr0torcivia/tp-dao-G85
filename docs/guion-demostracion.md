# Guion breve de demostración · Grupo 85

La [guía completa](guia-exposicion.md) y su [PDF](Guia-exposicion-grupo-85.pdf) contienen los casos, reglas y respuestas para la defensa.

## Antes de comenzar

Con Docker Desktop abierto, desde la raíz ejecutar:

```powershell
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
docker compose up -d --build --wait
docker compose exec backend python manage.py preparar_exposicion --reiniciar
```

Abrir `http://localhost:5173` e ingresar con **biblioteca / demo**. La carga limpia contiene **20 títulos, 60 copias y 44 disponibles**. `--reiniciar` borra datos de biblioteca y bitácora para volver al escenario inicial; conserva las cuentas.

## Secuencia de 15 minutos

1. **Dominio:** mostrar una obra y sus copias. EXPO-001, EXPO-002 y EXPO-003 son tres situaciones de *Skywalker Strikes*.
2. **Strategy:** abrir Naruto local y Jujutsu Kaisen entre sedes, ambas asignadas. Ejecutar **Preparar entrega** y comparar el resultado.
3. **State:** abrir el remito de X-Men: Days of Future Past, empaquetar, despachar y recibir; observar acciones e historial. Abrir Wolverine para ver una recepción con daño.
4. **Circulación:** entregar la solicitud local de Naruto y devolver el préstamo vigente de Spider-Man. Mostrar revisión antes de volver a disponibilidad.
5. **Tema 1 / Reportería:** alta, modificación a NO_APTO y baja de DEFENSA-001; comprobar disponibilidad y los tres eventos en Bitácora de operaciones. Exportar CSV o imprimir.

En una base restablecida, Disponibilidad por sede parte de **44/60**. Después del alta apta, **45/61**; tras cambiar a NO_APTO, **44/61**; tras la baja, el total sigue en 61 y la copia figura BAJA. Para las operaciones nuevas, filtrar la bitácora por el día de la demostración.
