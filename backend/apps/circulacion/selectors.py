from django.db.models import Exists, OuterRef, QuerySet, Subquery
from django.utils import timezone

from .models import EstadoReserva, Prestamo, Reserva, SolicitudPrestamo


def listar_solicitudes() -> QuerySet[SolicitudPrestamo]:
    from apps.logistica.models import ESTADOS_VIGENTES, DetalleRemito

    detalles = DetalleRemito.objects.filter(solicitud=OuterRef("pk"))
    return (
        SolicitudPrestamo.objects.annotate(
            en_remito_vigente=Exists(detalles.filter(remito__estado__in=ESTADOS_VIGENTES)),
            remito_vigente_estado=Subquery(
                detalles.filter(remito__estado__in=ESTADOS_VIGENTES)
                .order_by("-id")
                .values("remito__estado")[:1]
            ),
            ultimo_remito_id=Subquery(detalles.order_by("-id").values("remito_id")[:1]),
        )
        .select_related(
            "socio",
            "libro",
            "ejemplar",
            "sede_origen",
            "sede_destino",
            "reserva",
        )
        .all()
        .order_by("-fecha_solicitud")
    )


def listar_prestamos() -> QuerySet[Prestamo]:
    return (
        Prestamo.objects.select_related(
            "solicitud",
            "solicitud__socio",
            "solicitud__libro",
            "solicitud__ejemplar",
        )
        .all()
        .order_by("-fecha_entrega")
    )


def listar_prestamos_vigentes() -> QuerySet[Prestamo]:
    return listar_prestamos().filter(fecha_devolucion__isnull=True)


def listar_prestamos_vencidos() -> QuerySet[Prestamo]:
    return listar_prestamos().filter(
        fecha_devolucion__isnull=True,
        fecha_vencimiento__lt=timezone.now(),
    )


def listar_reservas() -> QuerySet[Reserva]:
    return (
        Reserva.objects.select_related(
            "socio",
            "libro",
            "sede_retiro",
            "ejemplar_asignado",
        )
        .all()
        .order_by("-fecha_reserva")
    )


def listar_reservas_vencidas(*, fecha_actual=None) -> QuerySet[Reserva]:
    fecha_actual = fecha_actual or timezone.now()
    return listar_reservas().filter(
        estado=EstadoReserva.LISTA_PARA_RETIRO,
        fecha_limite_retiro__lt=fecha_actual,
    )
