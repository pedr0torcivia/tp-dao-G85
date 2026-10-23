from apps.circulacion.exceptions import TramitacionNoDisponibleError
from apps.circulacion.models import TipoSolicitud

from .base import TramitacionPrestamo
from .interbibliotecaria import TramitacionInterbibliotecaria
from .local import TramitacionLocal


def obtener_estrategia(tipo: str) -> TramitacionPrestamo:
    estrategias = {
        TipoSolicitud.LOCAL: TramitacionLocal,
        TipoSolicitud.INTERBIBLIOTECARIO: TramitacionInterbibliotecaria,
    }

    clase_estrategia = estrategias.get(tipo)

    if clase_estrategia is None:
        raise TramitacionNoDisponibleError(
            f"No existe una estrategia para el tipo '{tipo}'."
        )

    return clase_estrategia()