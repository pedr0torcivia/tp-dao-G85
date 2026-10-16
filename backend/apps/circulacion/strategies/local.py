from apps.catalogo.models import Ejemplar, EstadoEjemplar
from apps.circulacion.exceptions import EstadoSolicitudInvalidoError
from apps.circulacion.models import (
    EstadoSolicitud,
    SolicitudPrestamo,
    TipoSolicitud,
)
from apps.sedes.models import Sede

from .base import TramitacionPrestamo


class TramitacionLocal(TramitacionPrestamo):
    def validar_creacion(
        self,
        *,
        sede_origen: Sede,
        sede_destino: Sede,
    ) -> None:
        if sede_origen.pk != sede_destino.pk:
            raise EstadoSolicitudInvalidoError(
                "Una solicitud local debe tener la misma sede "
                "de origen y destino."
            )

    def preparar_entrega(
        self,
        *,
        solicitud: SolicitudPrestamo,
        ejemplar: Ejemplar,
    ) -> None:
        if solicitud.tipo != TipoSolicitud.LOCAL:
            raise EstadoSolicitudInvalidoError(
                "La solicitud no utiliza tramitación local."
            )

        if solicitud.estado != EstadoSolicitud.ASIGNADA:
            raise EstadoSolicitudInvalidoError(
                "Solo se puede preparar una solicitud asignada."
            )

        if solicitud.ejemplar_id != ejemplar.pk:
            raise EstadoSolicitudInvalidoError(
                "El ejemplar no está asignado a la solicitud."
            )

        solicitud.estado = EstadoSolicitud.LISTA_PARA_ENTREGA
        ejemplar.estado = EstadoEjemplar.LISTO_PARA_ENTREGA

        solicitud.save(update_fields=["estado"])
        ejemplar.save(update_fields=["estado"])