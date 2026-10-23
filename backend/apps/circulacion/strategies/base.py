from abc import ABC, abstractmethod

from apps.catalogo.models import Ejemplar
from apps.circulacion.models import SolicitudPrestamo
from apps.sedes.models import Sede


class TramitacionPrestamo(ABC):
    @abstractmethod
    def validar_creacion(
        self,
        *,
        sede_origen: Sede,
        sede_destino: Sede,
    ) -> None:
        """Valida si las sedes corresponden al tipo de solicitud."""

    @abstractmethod
    def preparar_entrega(
        self,
        *,
        solicitud: SolicitudPrestamo,
        ejemplar: Ejemplar,
    ) -> None:
        """Ejecuta la preparación correspondiente a la estrategia."""