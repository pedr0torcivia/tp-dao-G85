from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.catalogo.models import CondicionFisica, Ejemplar, EstadoEjemplar
from apps.circulacion.models import (
    EstadoSolicitud,
    SolicitudPrestamo,
    TipoSolicitud,
)
from apps.sedes.models import Sede
from apps.sedes.services import validar_sede_activa
from apps.socios.models import EstadoSocio

from .exceptions import (
    EjemplarInvalidoError,
    NumeroRemitoDuplicadoError,
    RecepcionInvalidaError,
    SedesInvalidasError,
    SocioInhabilitadoError,
    TransicionInvalidaError,
)
from .models import DetalleRemito, EstadoRemito, EventoRemito, Remito
from .states import estado_actual

RESPONSABLE_BASE = "Personal de biblioteca"

ESTADOS_VIGENTES = (
    EstadoRemito.EN_PREPARACION,
    EstadoRemito.EMPAQUETADO,
    EstadoRemito.DESPACHADO,
    EstadoRemito.EN_TRANSITO,
)


def _validar_sedes_activas(*, sede_origen_id: int, sede_destino_id: int) -> None:
    for sede_id in (sede_origen_id, sede_destino_id):
        sede = Sede.objects.get(pk=sede_id)
        validar_sede_activa(sede=sede)


def _registrar_evento(
    *,
    remito: Remito,
    destino: str,
    responsable: str,
    observacion: str,
) -> None:
    EventoRemito.objects.create(
        remito=remito,
        estado_anterior=remito.estado,
        estado_nuevo=destino,
        responsable=responsable.strip() or RESPONSABLE_BASE,
        observacion=observacion.strip(),
    )


@transaction.atomic
def crear_remito(
    *,
    numero: str,
    sede_origen_id: int,
    sede_destino_id: int,
) -> Remito:
    _validar_sedes_activas(sede_origen_id=sede_origen_id, sede_destino_id=sede_destino_id)

    if sede_origen_id == sede_destino_id:
        raise SedesInvalidasError("El origen y el destino deben ser diferentes.")

    try:
        remito = Remito.objects.create(
            numero=numero.strip(),
            sede_origen_id=sede_origen_id,
            sede_destino_id=sede_destino_id,
        )
    except IntegrityError as error:
        raise NumeroRemitoDuplicadoError("Ya existe un remito con ese número.") from error

    EventoRemito.objects.create(
        remito=remito,
        estado_anterior=None,
        estado_nuevo=EstadoRemito.EN_PREPARACION,
        responsable=RESPONSABLE_BASE,
        observacion="Remito registrado.",
    )

    return remito


@transaction.atomic
def agregar_ejemplar(*, remito: Remito, ejemplar_id: int) -> DetalleRemito:
    _validar_sedes_activas(
        sede_origen_id=remito.sede_origen_id, sede_destino_id=remito.sede_destino_id
    )

    remito = Remito.objects.select_for_update().get(pk=remito.pk)

    if not estado_actual(remito).admite_asignar():
        raise TransicionInvalidaError("Sólo se agregan ejemplares durante la preparación.")

    try:
        ejemplar = Ejemplar.objects.select_for_update().get(pk=ejemplar_id)
    except Ejemplar.DoesNotExist as error:
        raise EjemplarInvalidoError("Ejemplar inexistente.") from error

    if (
        ejemplar.sede_propietaria_id != remito.sede_origen_id
        or ejemplar.sede_actual_id != remito.sede_origen_id
    ):
        raise EjemplarInvalidoError("El ejemplar debe pertenecer al origen y estar allí.")

    en_remito_vigente = DetalleRemito.objects.filter(
        ejemplar=ejemplar,
        remito__estado__in=ESTADOS_VIGENTES,
    ).exists()
    if en_remito_vigente:
        raise EjemplarInvalidoError("El ejemplar ya está incluido en un remito vigente.")

    solicitud = SolicitudPrestamo.objects.filter(
        ejemplar=ejemplar,
        estado=EstadoSolicitud.ASIGNADA,
    ).first()

    disponible = (
        ejemplar.estado == EstadoEjemplar.DISPONIBLE
        and ejemplar.condicion_fisica == CondicionFisica.APTO
        and ejemplar.sede_actual_id == ejemplar.sede_propietaria_id
    )
    para_traslado = (
        solicitud is not None
        and solicitud.tipo == TipoSolicitud.INTERBIBLIOTECARIO
        and solicitud.sede_destino_id == remito.sede_destino_id
    )
    if not (disponible or para_traslado):
        raise EjemplarInvalidoError("El ejemplar no está disponible para este trayecto.")

    detalle = DetalleRemito.objects.create(
        remito=remito,
        ejemplar=ejemplar,
        solicitud=solicitud,
        condicion_salida=ejemplar.condicion_fisica,
    )
    ejemplar.estado = EstadoEjemplar.ASIGNADO
    ejemplar.save(update_fields=["estado"])

    return detalle


@transaction.atomic
def empaquetar_remito(
    *,
    remito: Remito,
    responsable: str = "",
    observacion: str = "",
) -> Remito:
    _validar_sedes_activas(
        sede_origen_id=remito.sede_origen_id, sede_destino_id=remito.sede_destino_id
    )

    remito = Remito.objects.select_for_update().get(pk=remito.pk)
    destino = estado_actual(remito).empaquetar(remito)

    _registrar_evento(
        remito=remito,
        destino=destino,
        responsable=responsable,
        observacion=observacion,
    )
    remito.estado = destino
    remito.save(update_fields=["estado"])

    return remito


@transaction.atomic
def cancelar_remito(
    *,
    remito: Remito,
    responsable: str = "",
    observacion: str = "",
) -> Remito:
    remito = Remito.objects.select_for_update().get(pk=remito.pk)
    destino = estado_actual(remito).cancelar(remito)

    for detalle in remito.detalles.select_related("ejemplar"):
        if detalle.solicitud_id is None:
            ejemplar = detalle.ejemplar
            ejemplar.estado = EstadoEjemplar.DISPONIBLE
            ejemplar.save(update_fields=["estado"])

    _registrar_evento(
        remito=remito,
        destino=destino,
        responsable=responsable,
        observacion=observacion,
    )
    remito.estado = destino
    remito.save(update_fields=["estado"])

    return remito


@transaction.atomic
def despachar_remito(
    *,
    remito: Remito,
    responsable: str = "",
    observacion: str = "",
) -> Remito:
    _validar_sedes_activas(
        sede_origen_id=remito.sede_origen_id,
        sede_destino_id=remito.sede_destino_id,
    )

    remito = Remito.objects.select_for_update().get(pk=remito.pk)
    destino = estado_actual(remito).despachar(remito)

    detalles = list(remito.detalles.select_related("ejemplar", "solicitud", "solicitud__socio"))
    for detalle in detalles:
        solicitud = detalle.solicitud
        if solicitud is not None and solicitud.socio.estado != EstadoSocio.HABILITADO:
            raise SocioInhabilitadoError("El socio debe estar habilitado.")

    remito.fecha_despacho = timezone.now()
    for detalle in detalles:
        ejemplar = detalle.ejemplar
        ejemplar.estado = EstadoEjemplar.EN_TRANSITO
        ejemplar.sede_actual = None
        ejemplar.save(update_fields=["estado", "sede_actual"])

        solicitud = detalle.solicitud
        if solicitud is not None:
            solicitud.estado = EstadoSolicitud.EN_TRASLADO
            solicitud.save(update_fields=["estado"])

    _registrar_evento(
        remito=remito,
        destino=destino,
        responsable=responsable,
        observacion=observacion,
    )
    remito.estado = destino
    remito.save(update_fields=["estado", "fecha_despacho"])

    return remito


@transaction.atomic
def registrar_salida_remito(
    *,
    remito: Remito,
    responsable: str = "",
    observacion: str = "",
) -> Remito:
    _validar_sedes_activas(
        sede_origen_id=remito.sede_origen_id,
        sede_destino_id=remito.sede_destino_id,
    )

    remito = Remito.objects.select_for_update().get(pk=remito.pk)
    destino = estado_actual(remito).registrar_salida(remito)

    _registrar_evento(
        remito=remito,
        destino=destino,
        responsable=responsable,
        observacion=observacion,
    )
    remito.estado = destino
    remito.save(update_fields=["estado"])

    return remito


@transaction.atomic
def recibir_remito(
    *,
    remito: Remito,
    verificados: list[int],
    responsable: str,
    observacion: str = "",
) -> Remito:
    remito = Remito.objects.select_for_update().get(pk=remito.pk)
    destino = estado_actual(remito).recibir(remito)

    detalles = list(remito.detalles.select_related("ejemplar", "solicitud"))
    verificados_set = set(verificados)
    if any(detalle.ejemplar_id not in verificados_set for detalle in detalles):
        raise RecepcionInvalidaError(
            "Verificá todos los ejemplares. La recepción parcial está pendiente de definición."
        )
    if not responsable.strip():
        raise RecepcionInvalidaError("Indicá quién recibe el material.")

    remito.fecha_recepcion = timezone.now()
    for detalle in detalles:
        ejemplar = detalle.ejemplar
        detalle.condicion_recepcion = ejemplar.condicion_fisica
        ejemplar.sede_actual_id = remito.sede_destino_id

        solicitud = detalle.solicitud
        if solicitud is not None:
            ejemplar.estado = EstadoEjemplar.LISTO_PARA_ENTREGA
            solicitud.estado = EstadoSolicitud.LISTA_PARA_ENTREGA
            solicitud.save(update_fields=["estado"])
        else:
            ejemplar.estado = EstadoEjemplar.EN_REVISION
        ejemplar.save(update_fields=["estado", "sede_actual"])
        detalle.save(update_fields=["condicion_recepcion"])

    _registrar_evento(
        remito=remito,
        destino=destino,
        responsable=responsable,
        observacion=observacion,
    )
    remito.estado = destino
    remito.save(update_fields=["estado", "fecha_recepcion"])

    return remito
