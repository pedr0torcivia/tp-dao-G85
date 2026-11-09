"""Patrón Strategy aplicado a la tramitación de solicitudes de préstamo.

Participantes (GoF):

* **Contexto**: los servicios de `circulacion.services` (`crear_solicitud`,
  `preparar_entrega`). No preguntan por el tipo de solicitud: piden la
  estrategia a la fábrica y la usan a través de esta interfaz.
* **Estrategia abstracta**: `TramitacionPrestamo`.
* **Estrategias concretas**:
    - `TramitacionLocal`: el ejemplar ya está en la sede de retiro; preparar la
      entrega lo deja listo en el mostrador.
    - `TramitacionInterbibliotecaria`: el ejemplar está en otra sede; preparar
      la entrega lo incorpora a un remito hacia la sede de retiro. La entrega se
      habilita cuando la logística (patrón State) registra la recepción.
* **Fábrica**: `obtener_estrategia(tipo)` elige la clase según
  `SolicitudPrestamo.tipo`.

Agregar un circuito nuevo (por ejemplo, envío a domicilio) sólo requiere otra
estrategia y una entrada en la fábrica, sin tocar los servicios.
"""

from abc import ABC, abstractmethod

from apps.catalogo.models import Ejemplar, EstadoEjemplar
from apps.circulacion.exceptions import EstadoSolicitudInvalidoError
from apps.circulacion.models import EstadoSolicitud, SolicitudPrestamo
from apps.sedes.models import Sede


class TramitacionPrestamo(ABC):
    #: Valor de `SolicitudPrestamo.tipo` que atiende la estrategia.
    tipo: str = ""
    #: Nombre legible del circuito.
    nombre: str = ""
    #: Qué hace `preparar_entrega` en esta estrategia (se muestra en la interfaz).
    descripcion_preparacion: str = ""
    #: Estados que recorre la solicitud con esta estrategia, en orden.
    recorrido: tuple[str, ...] = ()

    @abstractmethod
    def validar_creacion(self, *, sede_origen: Sede, sede_destino: Sede) -> None:
        """Valida si las sedes corresponden al tipo de solicitud."""

    @abstractmethod
    def preparar_entrega(self, *, solicitud: SolicitudPrestamo, ejemplar: Ejemplar):
        """Ejecuta la preparación propia del circuito. Puede devolver un remito."""

    def validar_preparacion(self, *, solicitud: SolicitudPrestamo, ejemplar: Ejemplar) -> None:
        """Precondiciones comunes a toda estrategia (método plantilla)."""
        if solicitud.tipo != self.tipo:
            raise EstadoSolicitudInvalidoError(
                f"La solicitud no utiliza tramitación {self.nombre}."
            )
        if solicitud.estado != EstadoSolicitud.ASIGNADA:
            raise EstadoSolicitudInvalidoError("Solo se puede preparar una solicitud asignada.")
        if solicitud.ejemplar_id != ejemplar.pk:
            raise EstadoSolicitudInvalidoError("El ejemplar no está asignado a la solicitud.")
        if ejemplar.estado != EstadoEjemplar.ASIGNADO:
            raise EstadoSolicitudInvalidoError("El ejemplar no se encuentra en estado asignado.")
