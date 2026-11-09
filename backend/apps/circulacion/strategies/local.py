from apps.catalogo.models import Ejemplar, EstadoEjemplar
from apps.circulacion.exceptions import EstadoSolicitudInvalidoError
from apps.circulacion.models import EstadoSolicitud, SolicitudPrestamo, TipoSolicitud
from apps.sedes.models import Sede

from .base import TramitacionPrestamo


class TramitacionLocal(TramitacionPrestamo):
    """El socio retira en la misma sede donde está el ejemplar."""

    tipo = TipoSolicitud.LOCAL
    nombre = "local"
    descripcion_preparacion = "Deja el ejemplar listo en el mostrador de la sede."
    recorrido = (
        EstadoSolicitud.PENDIENTE,
        EstadoSolicitud.ASIGNADA,
        EstadoSolicitud.LISTA_PARA_ENTREGA,
        EstadoSolicitud.CUMPLIDA,
    )

    def validar_creacion(self, *, sede_origen: Sede, sede_destino: Sede) -> None:
        if sede_origen.pk != sede_destino.pk:
            raise EstadoSolicitudInvalidoError(
                "Una solicitud local debe tener la misma sede de origen y destino."
            )

    def preparar_entrega(self, *, solicitud: SolicitudPrestamo, ejemplar: Ejemplar) -> None:
        self.validar_preparacion(solicitud=solicitud, ejemplar=ejemplar)
        solicitud.estado = EstadoSolicitud.LISTA_PARA_ENTREGA
        ejemplar.estado = EstadoEjemplar.LISTO_PARA_ENTREGA
        solicitud.save(update_fields=["estado"])
        ejemplar.save(update_fields=["estado"])
        return None
