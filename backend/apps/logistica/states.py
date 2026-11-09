"""Patrón State aplicado al ciclo de vida del remito.

Participantes (GoF):

* **Contexto**: `Remito`. Expone `remito.comportamiento` (el objeto estado
  vigente) y `remito.transicionar(...)`, el único punto que cambia el estado y
  deja el evento de trazabilidad.
* **Estado abstracto**: `EstadoRemitoBase`. Declara todas las operaciones del
  remito y, por defecto, las rechaza con `TransicionInvalidaError`.
* **Estados concretos**: `EnPreparacion`, `Empaquetado`, `EnTransito`,
  `Recibido`, `RecibidoConIncidencias` y `Cancelado`. Cada uno redefine
  únicamente las operaciones que admite y ejecuta sus efectos (ejemplares,
  solicitudes, fechas) antes de pasar al estado siguiente.

Diagrama de transiciones::

    EN_PREPARACION --empaquetar--> EMPAQUETADO --despachar--> EN_TRANSITO
         ^    |                     |     |                       |
         |    +----cancelar----+    |     +--cancelar--+          +--recibir--> RECIBIDO
         +--------reabrir------|----+                  |          |
                               v                       v          +--recibir--> RECIBIDO_CON_
                           CANCELADO <-----------------+                        INCIDENCIAS

Los servicios de `services.py` sólo bloquean filas, validan reglas
transversales (sedes activas) y delegan: `remito.comportamiento.despachar(...)`.
Ningún servicio escribe `Remito.estado` a mano.
"""

from __future__ import annotations

from django.utils import timezone

from apps.catalogo.models import CondicionFisica, EstadoEjemplar
from apps.circulacion.models import EstadoSolicitud
from apps.socios.models import EstadoSocio

from .exceptions import (
    RecepcionInvalidaError,
    RemitoVacioError,
    SocioInhabilitadoError,
    TransicionInvalidaError,
)
from .models import DetalleRemito, EstadoRemito, Remito, ResultadoRecepcion

#: Operaciones que un estado puede admitir. El orden es el del flujo normal.
OPERACIONES = ("agregar", "quitar", "empaquetar", "reabrir", "despachar", "recibir", "cancelar")


class EstadoRemitoBase:
    """Estado abstracto: declara el protocolo y rechaza todo por defecto."""

    codigo: str = ""
    descripcion: str = ""
    es_final: bool = False

    def _rechazar(self, operacion: str):
        raise TransicionInvalidaError(
            f"Un remito {EstadoRemito(self.codigo).label.lower()} no admite «{operacion}»."
        )

    # --- Protocolo ------------------------------------------------------
    def agregar(self, remito: Remito, detalle: DetalleRemito) -> None:
        self._rechazar("agregar ejemplares")

    def quitar(self, remito: Remito, detalle: DetalleRemito) -> None:
        self._rechazar("quitar ejemplares")

    def empaquetar(self, remito: Remito, *, responsable: str, observacion: str = "") -> None:
        self._rechazar("empaquetar")

    def reabrir(self, remito: Remito, *, responsable: str, observacion: str = "") -> None:
        self._rechazar("reabrir")

    def despachar(self, remito: Remito, *, responsable: str, observacion: str = "") -> None:
        self._rechazar("despachar")

    def recibir(
        self,
        remito: Remito,
        *,
        resultados: dict[int, str],
        responsable: str,
        observacion: str = "",
    ) -> None:
        self._rechazar("recibir")

    def cancelar(self, remito: Remito, *, responsable: str, observacion: str = "") -> None:
        self._rechazar("cancelar")

    # --- Introspección para la API y la interfaz ------------------------
    def operaciones_admitidas(self) -> list[str]:
        """Operaciones que este estado redefine. La UI muestra sólo estas."""
        return [
            operacion
            for operacion in OPERACIONES
            if getattr(type(self), operacion) is not getattr(EstadoRemitoBase, operacion)
        ]


class EnPreparacion(EstadoRemitoBase):
    codigo = EstadoRemito.EN_PREPARACION
    descripcion = "Se arma el envío: se agregan o quitan ejemplares."

    def agregar(self, remito, detalle):
        detalle.save()
        ejemplar = detalle.ejemplar
        ejemplar.estado = EstadoEjemplar.ASIGNADO
        ejemplar.save(update_fields=["estado"])

    def quitar(self, remito, detalle):
        _liberar_ejemplar(detalle)
        detalle.delete()

    def empaquetar(self, remito, *, responsable, observacion=""):
        if not remito.detalles.exists():
            raise RemitoVacioError("El remito debe contener al menos un ejemplar.")
        remito.transicionar(
            EstadoRemito.EMPAQUETADO, responsable=responsable, observacion=observacion
        )

    def cancelar(self, remito, *, responsable, observacion=""):
        _cancelar(remito, responsable=responsable, observacion=observacion)


class Empaquetado(EstadoRemitoBase):
    codigo = EstadoRemito.EMPAQUETADO
    descripcion = "El paquete está cerrado y espera al transporte."

    def reabrir(self, remito, *, responsable, observacion=""):
        remito.transicionar(
            EstadoRemito.EN_PREPARACION,
            responsable=responsable,
            observacion=observacion or "Paquete reabierto para modificar su contenido.",
        )

    def despachar(self, remito, *, responsable, observacion=""):
        detalles = list(remito.detalles.select_related("ejemplar", "solicitud__socio"))
        if not detalles:
            raise RemitoVacioError("El remito debe contener al menos un ejemplar.")
        for detalle in detalles:
            solicitud = detalle.solicitud
            if solicitud is not None and solicitud.socio.estado != EstadoSocio.HABILITADO:
                raise SocioInhabilitadoError(
                    f"El socio de la solicitud {solicitud.pk} está inhabilitado."
                )

        for detalle in detalles:
            ejemplar = detalle.ejemplar
            ejemplar.estado = EstadoEjemplar.EN_TRANSITO
            ejemplar.sede_actual = None
            ejemplar.save(update_fields=["estado", "sede_actual"])
            if detalle.solicitud is not None:
                detalle.solicitud.estado = EstadoSolicitud.EN_TRASLADO
                detalle.solicitud.save(update_fields=["estado"])

        remito.fecha_despacho = timezone.now()
        remito.transicionar(
            EstadoRemito.EN_TRANSITO, responsable=responsable, observacion=observacion
        )

    def cancelar(self, remito, *, responsable, observacion=""):
        _cancelar(remito, responsable=responsable, observacion=observacion)


class EnTransito(EstadoRemitoBase):
    codigo = EstadoRemito.EN_TRANSITO
    descripcion = "El material viaja. Sólo puede recibirse en destino."

    def recibir(self, remito, *, resultados, responsable, observacion=""):
        if not responsable.strip():
            raise RecepcionInvalidaError("Indicá quién recibe el material.")
        detalles = list(remito.detalles.select_related("ejemplar", "solicitud"))
        faltantes = [d for d in detalles if d.ejemplar_id not in resultados]
        if faltantes:
            raise RecepcionInvalidaError(
                "Revisá todos los ejemplares: cada uno debe marcarse como recibido, "
                "dañado o extraviado."
            )
        invalidos = set(resultados.values()) - set(ResultadoRecepcion.values)
        if invalidos:
            raise RecepcionInvalidaError("El resultado de recepción no es válido.")

        for detalle in detalles:
            _aplicar_recepcion(remito, detalle, resultados[detalle.ejemplar_id])

        con_incidencias = any(r != ResultadoRecepcion.CONFORME for r in resultados.values())
        remito.fecha_recepcion = timezone.now()
        remito.transicionar(
            EstadoRemito.RECIBIDO_CON_INCIDENCIAS if con_incidencias else EstadoRemito.RECIBIDO,
            responsable=responsable,
            observacion=observacion,
        )


class Recibido(EstadoRemitoBase):
    codigo = EstadoRemito.RECIBIDO
    descripcion = "Entregado en destino sin novedades. Estado final."
    es_final = True


class RecibidoConIncidencias(EstadoRemitoBase):
    codigo = EstadoRemito.RECIBIDO_CON_INCIDENCIAS
    descripcion = "Entregado en destino con daños o faltantes registrados. Estado final."
    es_final = True


class Cancelado(EstadoRemitoBase):
    codigo = EstadoRemito.CANCELADO
    descripcion = "El envío se anuló antes de salir. Estado final."
    es_final = True


# --- Efectos compartidos -------------------------------------------------
def _liberar_ejemplar(detalle: DetalleRemito) -> None:
    """Devuelve el ejemplar al estado que tenía antes de entrar al remito."""
    ejemplar = detalle.ejemplar
    if detalle.solicitud_id is not None:
        # Sigue reservado para su solicitud, que vuelve a estar asignada.
        ejemplar.estado = EstadoEjemplar.ASIGNADO
    elif (
        ejemplar.sede_actual_id != ejemplar.sede_propietaria_id
        or ejemplar.condicion_fisica != CondicionFisica.APTO
    ):
        ejemplar.estado = EstadoEjemplar.EN_REVISION
    else:
        ejemplar.estado = EstadoEjemplar.DISPONIBLE
    ejemplar.save(update_fields=["estado"])


def _cancelar(remito: Remito, *, responsable: str, observacion: str) -> None:
    for detalle in remito.detalles.select_related("ejemplar"):
        _liberar_ejemplar(detalle)
    remito.transicionar(EstadoRemito.CANCELADO, responsable=responsable, observacion=observacion)


def _aplicar_recepcion(remito: Remito, detalle: DetalleRemito, resultado: str) -> None:
    ejemplar = detalle.ejemplar
    solicitud = detalle.solicitud
    detalle.resultado_recepcion = resultado

    if resultado == ResultadoRecepcion.EXTRAVIADO:
        detalle.condicion_recepcion = None
        ejemplar.estado = EstadoEjemplar.BAJA
        ejemplar.sede_actual = None
    else:
        if resultado == ResultadoRecepcion.DANADO:
            ejemplar.condicion_fisica = CondicionFisica.NO_APTO
        detalle.condicion_recepcion = ejemplar.condicion_fisica
        ejemplar.sede_actual_id = remito.sede_destino_id
        llega_para_socio = (
            solicitud is not None
            and resultado == ResultadoRecepcion.CONFORME
            and ejemplar.condicion_fisica == CondicionFisica.APTO
        )
        ejemplar.estado = (
            EstadoEjemplar.LISTO_PARA_ENTREGA if llega_para_socio else EstadoEjemplar.EN_REVISION
        )

    if solicitud is not None:
        if ejemplar.estado == EstadoEjemplar.LISTO_PARA_ENTREGA:
            solicitud.estado = EstadoSolicitud.LISTA_PARA_ENTREGA
            solicitud.save(update_fields=["estado"])
        else:
            # La copia no sirve: la solicitud vuelve a la cola para asignar otra.
            solicitud.estado = EstadoSolicitud.PENDIENTE
            solicitud.ejemplar = None
            solicitud.save(update_fields=["estado", "ejemplar"])

    ejemplar.save(update_fields=["estado", "sede_actual", "condicion_fisica"])
    detalle.save(update_fields=["condicion_recepcion", "resultado_recepcion"])


ESTADOS_REMITO: dict[str, EstadoRemitoBase] = {
    estado.codigo: estado
    for estado in (
        EnPreparacion(),
        Empaquetado(),
        EnTransito(),
        Recibido(),
        RecibidoConIncidencias(),
        Cancelado(),
    )
}


def estado_actual(remito: Remito) -> EstadoRemitoBase:
    """Resuelve el objeto State correspondiente al valor persistido."""
    return ESTADOS_REMITO[remito.estado]
