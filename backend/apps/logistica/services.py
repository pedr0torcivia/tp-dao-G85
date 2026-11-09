"""Casos de uso de logística.

Cada servicio bloquea las filas involucradas, valida las reglas transversales
(sedes activas, pertenencia del ejemplar) y delega la operación en el objeto
State del remito (`remito.comportamiento`). El estado decide si la operación
es válida y aplica sus efectos; los servicios nunca escriben `Remito.estado`.
"""

from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.catalogo.models import CondicionFisica, Ejemplar, EstadoEjemplar
from apps.circulacion.models import EstadoSolicitud, SolicitudPrestamo, TipoSolicitud
from apps.sedes.models import Sede
from apps.sedes.services import validar_sede_activa

from .exceptions import (
    EjemplarInvalidoError,
    NumeroRemitoDuplicadoError,
    RecepcionInvalidaError,
    SedesInvalidasError,
)
from .models import (
    ESTADOS_VIGENTES,
    DetalleRemito,
    EstadoRemito,
    EventoRemito,
    Remito,
    ResultadoRecepcion,
)

RESPONSABLE_BASE = "Personal de biblioteca"


def _validar_sedes_activas(*, sede_origen_id: int, sede_destino_id: int) -> None:
    for sede in Sede.objects.filter(pk__in=(sede_origen_id, sede_destino_id)):
        validar_sede_activa(sede=sede)


def _bloquear(remito: Remito) -> Remito:
    return Remito.objects.select_for_update().get(pk=remito.pk)


def _numero_siguiente() -> str:
    anio = timezone.localdate().year
    ultimo = Remito.objects.order_by("-id").values_list("id", flat=True).first() or 0
    for n in range(ultimo + 1, ultimo + 1000):
        numero = f"REM-{anio}-{n:05d}"
        if not Remito.objects.filter(numero__iexact=numero).exists():
            return numero
    raise NumeroRemitoDuplicadoError("No se pudo generar un número de remito libre.")


@transaction.atomic
def crear_remito(
    *,
    sede_origen_id: int,
    sede_destino_id: int,
    numero: str | None = None,
) -> Remito:
    if sede_origen_id == sede_destino_id:
        raise SedesInvalidasError("El origen y el destino deben ser diferentes.")
    _validar_sedes_activas(sede_origen_id=sede_origen_id, sede_destino_id=sede_destino_id)

    try:
        with transaction.atomic():
            remito = Remito.objects.create(
                numero=(numero or "").strip() or _numero_siguiente(),
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


def remito_abierto(*, sede_origen_id: int, sede_destino_id: int) -> Remito:
    """Reutiliza el remito en preparación del mismo trayecto o crea uno nuevo.

    Así varias solicitudes hacia la misma sede viajan juntas en un paquete.
    """
    existente = (
        Remito.objects.select_for_update()
        .filter(
            sede_origen_id=sede_origen_id,
            sede_destino_id=sede_destino_id,
            estado=EstadoRemito.EN_PREPARACION,
        )
        .order_by("id")
        .first()
    )
    if existente is not None:
        return existente
    return crear_remito(sede_origen_id=sede_origen_id, sede_destino_id=sede_destino_id)


@transaction.atomic
def agregar_ejemplar(*, remito: Remito, ejemplar_id: int) -> DetalleRemito:
    remito = _bloquear(remito)
    _validar_sedes_activas(
        sede_origen_id=remito.sede_origen_id, sede_destino_id=remito.sede_destino_id
    )
    if "agregar" not in remito.comportamiento.operaciones_admitidas():
        remito.comportamiento._rechazar("agregar ejemplares")

    try:
        ejemplar = Ejemplar.objects.select_for_update().get(pk=ejemplar_id)
    except Ejemplar.DoesNotExist as error:
        raise EjemplarInvalidoError("Ejemplar inexistente.") from error

    if ejemplar.sede_actual_id != remito.sede_origen_id:
        raise EjemplarInvalidoError("El ejemplar no se encuentra en la sede de origen del remito.")

    if DetalleRemito.objects.filter(
        ejemplar=ejemplar, remito__estado__in=ESTADOS_VIGENTES
    ).exists():
        raise EjemplarInvalidoError("El ejemplar ya está incluido en un remito vigente.")

    solicitud = SolicitudPrestamo.objects.filter(
        ejemplar=ejemplar, estado=EstadoSolicitud.ASIGNADA
    ).first()

    es_retorno = (
        ejemplar.sede_actual_id != ejemplar.sede_propietaria_id
        and remito.sede_destino_id == ejemplar.sede_propietaria_id
        and ejemplar.estado == EstadoEjemplar.EN_REVISION
    )
    para_solicitud = (
        solicitud is not None
        and solicitud.tipo == TipoSolicitud.INTERBIBLIOTECARIO
        and solicitud.sede_destino_id == remito.sede_destino_id
        and ejemplar.sede_propietaria_id == remito.sede_origen_id
    )
    traslado_libre = (
        solicitud is None
        and ejemplar.estado == EstadoEjemplar.DISPONIBLE
        and ejemplar.condicion_fisica == CondicionFisica.APTO
        and ejemplar.sede_propietaria_id == remito.sede_origen_id
    )
    if not (es_retorno or para_solicitud or traslado_libre):
        if solicitud is not None and solicitud.sede_destino_id != remito.sede_destino_id:
            raise EjemplarInvalidoError(
                "El ejemplar está asignado a una solicitud con otra sede de destino."
            )
        raise EjemplarInvalidoError(
            "El ejemplar no está disponible para este trayecto: debe estar disponible en su "
            "sede, asignado a una solicitud hacia el destino o volver a su sede propietaria."
        )

    detalle = DetalleRemito(
        remito=remito,
        ejemplar=ejemplar,
        solicitud=solicitud if para_solicitud else None,
        condicion_salida=ejemplar.condicion_fisica,
    )
    remito.comportamiento.agregar(remito, detalle)
    return detalle


@transaction.atomic
def quitar_ejemplar(*, remito: Remito, ejemplar_id: int) -> Remito:
    remito = _bloquear(remito)
    detalle = remito.detalles.select_related("ejemplar").filter(ejemplar_id=ejemplar_id).first()
    if detalle is None:
        raise EjemplarInvalidoError("El ejemplar no forma parte del remito.")
    remito.comportamiento.quitar(remito, detalle)
    return remito


@transaction.atomic
def preparar_retorno(*, ejemplar_id: int) -> Remito:
    """Arma (o completa) el remito que devuelve un ejemplar a su sede propietaria."""
    try:
        ejemplar = Ejemplar.objects.get(pk=ejemplar_id)
    except Ejemplar.DoesNotExist as error:
        raise EjemplarInvalidoError("Ejemplar inexistente.") from error
    if ejemplar.sede_actual_id is None or ejemplar.sede_actual_id == ejemplar.sede_propietaria_id:
        raise EjemplarInvalidoError("El ejemplar ya está en su sede propietaria.")
    remito = remito_abierto(
        sede_origen_id=ejemplar.sede_actual_id, sede_destino_id=ejemplar.sede_propietaria_id
    )
    agregar_ejemplar(remito=remito, ejemplar_id=ejemplar.pk)
    return remito


def _transicion(nombre: str, *, validar_sedes: bool):
    """Fabrica servicios de transición simples que delegan en el estado."""

    @transaction.atomic
    def servicio(*, remito: Remito, responsable: str = "", observacion: str = "") -> Remito:
        remito = _bloquear(remito)
        if validar_sedes:
            _validar_sedes_activas(
                sede_origen_id=remito.sede_origen_id, sede_destino_id=remito.sede_destino_id
            )
        getattr(remito.comportamiento, nombre)(
            remito, responsable=responsable.strip() or RESPONSABLE_BASE, observacion=observacion
        )
        return remito

    servicio.__name__ = f"{nombre}_remito"
    return servicio


empaquetar_remito = _transicion("empaquetar", validar_sedes=True)
reabrir_remito = _transicion("reabrir", validar_sedes=False)
# Despachar inicia el envío: la regla «no iniciar envíos desde/hacia una sede de baja» aplica acá.
despachar_remito = _transicion("despachar", validar_sedes=True)
cancelar_remito = _transicion("cancelar", validar_sedes=False)


@transaction.atomic
def recibir_remito(
    *,
    remito: Remito,
    responsable: str,
    verificados: list[int] | None = None,
    resultados: dict[int, str] | None = None,
    observacion: str = "",
) -> Remito:
    """Registra la llegada. Cada ejemplar se marca conforme, dañado o extraviado.

    `verificados` se mantiene por compatibilidad: equivale a marcar esos
    ejemplares como conformes.
    """
    remito = _bloquear(remito)
    combinados: dict[int, str] = {
        int(ejemplar_id): ResultadoRecepcion.CONFORME for ejemplar_id in (verificados or [])
    }
    for ejemplar_id, resultado in (resultados or {}).items():
        combinados[int(ejemplar_id)] = resultado
    if not combinados and remito.detalles.exists():
        raise RecepcionInvalidaError("Verificá todos los ejemplares. El remito se recibe completo.")
    remito.comportamiento.recibir(
        remito, resultados=combinados, responsable=responsable, observacion=observacion
    )
    return remito
