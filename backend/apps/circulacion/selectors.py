from django.db.models import QuerySet
from django.utils import timezone

from .models import Prestamo, SolicitudPrestamo


def listar_solicitudes() -> QuerySet[SolicitudPrestamo]:
    return (
        SolicitudPrestamo.objects.select_related(
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