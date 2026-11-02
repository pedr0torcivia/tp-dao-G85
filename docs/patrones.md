# Patrones de diseño

## State en el remito

`backend/apps/logistica/states.py` define el contrato de estado y las clases concretas. `estado_actual(remito)` resuelve el objeto correspondiente. Los servicios en `services.py` delegan operaciones como empaquetar, despachar y recibir al estado actual; una operación no admitida falla antes de modificar el remito.

El campo `Remito.estado` persiste la situación actual; las clases expresan el comportamiento y `EventoRemito` conserva el historial. El patrón no consiste únicamente en un enum.

Para demostrarlo: intentar empaquetar un remito vacío, agregar una copia, empaquetar y despachar. Después del despacho, cancelar debe fallar. Registrar salida y recibir verificando las copias; mostrar los cinco eventos ordenados.

## Strategy en la tramitación

`backend/apps/circulacion/strategies/base.py` define `TramitacionPrestamo`. `factory.py` elige la implementación según `SolicitudPrestamo.tipo`.

`TramitacionLocal` valida que las sedes coincidan y prepara la copia para entrega. `TramitacionInterbibliotecaria` exige sedes diferentes y rechaza la preparación local: debe recorrer un remito. La recepción de logística deja solicitud y ejemplar listos para la entrega común, sin duplicar la creación del préstamo.

Para demostrarlo: crear una solicitud local y ejecutar preparar-entrega; repetir con una interbibliotecaria y mostrar que esa operación se rechaza. Completar el remito y entregar desde la misma API de circulación. Ambos comportamientos cumplen el contrato común y son elegidos por la fábrica.

## Evidencia

`apps/logistica/tests/test_states.py` verifica las transiciones. Las pruebas de estrategias están en `apps/circulacion/tests/test_strategies.py`. `apps/common/tests/test_circuitos.py` recorre la API completa, incluido el retorno de material apto y no apto. `frontend/e2e/circuitos.spec.ts` verifica la integración desde el navegador.
