from apps.catalogo.models import Ejemplar
from apps.circulacion.exceptions import EstadoSolicitudInvalidoError
from apps.circulacion.models import EstadoSolicitud, SolicitudPrestamo, TipoSolicitud
from apps.sedes.models import Sede

from .base import TramitacionPrestamo


class TramitacionInterbibliotecaria(TramitacionPrestamo):
    """El ejemplar viaja desde la sede de origen hasta la sede de retiro."""

    tipo = TipoSolicitud.INTERBIBLIOTECARIO
    nombre = "interbibliotecaria"
    descripcion_preparacion = (
        "Incorpora el ejemplar a un remito hacia la sede de retiro (lo crea si no hay "
        "uno en preparación para ese trayecto)."
    )
    recorrido = (
        EstadoSolicitud.PENDIENTE,
        EstadoSolicitud.ASIGNADA,
        EstadoSolicitud.EN_TRASLADO,
        EstadoSolicitud.LISTA_PARA_ENTREGA,
        EstadoSolicitud.CUMPLIDA,
    )

    def validar_creacion(self, *, sede_origen: Sede, sede_destino: Sede) -> None:
        if sede_origen.pk == sede_destino.pk:
            raise EstadoSolicitudInvalidoError(
                "Una solicitud interbibliotecaria requiere sedes diferentes."
            )

    def preparar_entrega(self, *, solicitud: SolicitudPrestamo, ejemplar: Ejemplar):
        # Import diferido: logística depende de circulación y no al revés a nivel módulo.
        from apps.logistica.exceptions import LogisticaError
        from apps.logistica.services import agregar_ejemplar, remito_abierto

        self.validar_preparacion(solicitud=solicitud, ejemplar=ejemplar)
        if solicitud.detalles_remito.filter(
            remito__estado__in=("EN_PREPARACION", "EMPAQUETADO", "EN_TRANSITO")
        ).exists():
            raise EstadoSolicitudInvalidoError("La solicitud ya forma parte de un remito vigente.")
        try:
            remito = remito_abierto(
                sede_origen_id=solicitud.sede_origen_id,
                sede_destino_id=solicitud.sede_destino_id,
            )
            agregar_ejemplar(remito=remito, ejemplar_id=ejemplar.pk)
        except LogisticaError as error:
            raise EstadoSolicitudInvalidoError(str(error)) from error
        return remito
