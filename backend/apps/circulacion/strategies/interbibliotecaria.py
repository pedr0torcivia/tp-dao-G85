from apps.catalogo.models import Ejemplar
from apps.circulacion.exceptions import TramitacionNoDisponibleError
from apps.circulacion.models import SolicitudPrestamo
from apps.sedes.models import Sede

from .base import TramitacionPrestamo


class TramitacionInterbibliotecaria:
    def validar_creacion(
        self,
        *,
        sede_origen: Sede,
        sede_destino: Sede,
    ) -> None:
        if sede_origen.pk == sede_destino.pk:
            raise ValueError(
                "Una solicitud interbibliotecaria requiere sedes diferentes."
            )

    def preparar_entrega(
        self,
        *,
        solicitud: SolicitudPrestamo,
        ejemplar: Ejemplar,
    ) -> None:
        raise TramitacionNoDisponibleError(
            "La tramitación interbibliotecaria todavía no está disponible."
        )