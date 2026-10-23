from django.db.models import Count, F, QuerySet

from apps.circulacion.models import (
    EstadoSolicitud,
    SolicitudPrestamo,
    TipoSolicitud,
)


def demanda_interbibliotecaria(
    *,
    fecha_desde=None,
    fecha_hasta=None,
    sede_id: int | None = None,
) -> QuerySet:
    solicitudes = SolicitudPrestamo.objects.filter(
        tipo=TipoSolicitud.INTERBIBLIOTECARIO,
    ).exclude(
        estado__in=(
            EstadoSolicitud.RECHAZADA,
            EstadoSolicitud.CANCELADA,
        )
    )

    if fecha_desde is not None:
        solicitudes = solicitudes.filter(fecha_solicitud__date__gte=fecha_desde)
    if fecha_hasta is not None:
        solicitudes = solicitudes.filter(fecha_solicitud__date__lte=fecha_hasta)
    if sede_id is not None:
        solicitudes = solicitudes.filter(sede_destino_id=sede_id)

    return (
        solicitudes.values("libro_id")
        .annotate(
            titulo=F("libro__titulo"),
            cantidad=Count("id"),
        )
        .order_by("-cantidad", "titulo", "libro_id")
    )
