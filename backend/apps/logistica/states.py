"""Patrón State del remito.

Cada estado del remito es una clase que decide qué operaciones acepta y
hacia dónde transiciona. Los servicios delegan en estas clases y nunca
escriben `Remito.estado` directamente: la clase devuelve el estado destino
o rechaza con `TransicionInvalidaError`.

Las clases deciden; los servicios aplican los efectos (fechas, ejemplares,
solicitudes y evento) dentro de una única transacción.
"""

from apps.logistica.exceptions import RemitoVacioError, TransicionInvalidaError
from apps.logistica.models import EstadoRemito, Remito

MENSAJE_TRANSICION_INVALIDA = "Esta transición no está permitida."
MENSAJE_REMITO_VACIO = "El remito debe contener al menos un ejemplar."


class EstadoRemitoBase:
    """Contrato común de los estados. Por defecto rechaza toda transición."""

    nombre: str = ""

    def empaquetar(self, remito: Remito) -> str:
        raise TransicionInvalidaError(MENSAJE_TRANSICION_INVALIDA)

    def despachar(self, remito: Remito) -> str:
        raise TransicionInvalidaError(MENSAJE_TRANSICION_INVALIDA)

    def registrar_salida(self, remito: Remito) -> str:
        raise TransicionInvalidaError(MENSAJE_TRANSICION_INVALIDA)

    def recibir(self, remito: Remito) -> str:
        raise TransicionInvalidaError(MENSAJE_TRANSICION_INVALIDA)

    def cancelar(self, remito: Remito) -> str:
        raise TransicionInvalidaError(MENSAJE_TRANSICION_INVALIDA)

    def admite_asignar(self) -> bool:
        """Sólo la preparación admite agregar ejemplares al detalle."""
        return False


class EnPreparacion(EstadoRemitoBase):
    nombre = EstadoRemito.EN_PREPARACION

    def empaquetar(self, remito: Remito) -> str:
        if not remito.detalles.exists():
            raise RemitoVacioError(MENSAJE_REMITO_VACIO)
        return EstadoRemito.EMPAQUETADO

    def cancelar(self, remito: Remito) -> str:
        return EstadoRemito.CANCELADO

    def admite_asignar(self) -> bool:
        return True


class Empaquetado(EstadoRemitoBase):
    nombre = EstadoRemito.EMPAQUETADO

    def despachar(self, remito: Remito) -> str:
        if not remito.detalles.exists():
            raise RemitoVacioError(MENSAJE_REMITO_VACIO)
        return EstadoRemito.DESPACHADO

    def cancelar(self, remito: Remito) -> str:
        return EstadoRemito.CANCELADO


class Despachado(EstadoRemitoBase):
    nombre = EstadoRemito.DESPACHADO

    def registrar_salida(self, remito: Remito) -> str:
        return EstadoRemito.EN_TRANSITO


class EnTransito(EstadoRemitoBase):
    nombre = EstadoRemito.EN_TRANSITO

    def recibir(self, remito: Remito) -> str:
        return EstadoRemito.RECIBIDO


class Recibido(EstadoRemitoBase):
    nombre = EstadoRemito.RECIBIDO


class Cancelado(EstadoRemitoBase):
    nombre = EstadoRemito.CANCELADO


ESTADOS_REMITO: dict[str, EstadoRemitoBase] = {
    estado.nombre: estado
    for estado in (
        EnPreparacion(),
        Empaquetado(),
        Despachado(),
        EnTransito(),
        Recibido(),
        Cancelado(),
    )
}


def estado_actual(remito: Remito) -> EstadoRemitoBase:
    """Devuelve la clase de estado correspondiente al valor persistido."""
    return ESTADOS_REMITO[remito.estado]
