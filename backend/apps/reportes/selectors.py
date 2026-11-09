from collections import defaultdict
from datetime import date

from django.db.models import Q
from django.utils import timezone

from apps.circulacion.models import Prestamo
from apps.circulacion.reglas import MULTA_DIARIA


def obtener_prestamos_vencidos(
    *, fecha_corte: date, sede_id: int | None = None, desde: date | None = None
) -> list[dict]:
    prestamos = (
        Prestamo.objects.filter(
            Q(fecha_devolucion__isnull=True) | Q(fecha_devolucion__date__gt=fecha_corte),
            fecha_vencimiento__date__lt=fecha_corte,
            fecha_entrega__date__lte=fecha_corte,
        )
        .select_related(
            "solicitud__socio",
            "solicitud__sede_destino",
            "solicitud__libro",
        )
        .order_by(
            "solicitud__sede_destino__nombre",
            "fecha_vencimiento",
            "id",
        )
    )
    if sede_id is not None:
        prestamos = prestamos.filter(solicitud__sede_destino_id=sede_id)
    if desde is not None:
        prestamos = prestamos.filter(fecha_entrega__date__gte=desde)

    por_sede = defaultdict(list)

    for prestamo in prestamos:
        solicitud = prestamo.solicitud
        sede = solicitud.sede_destino

        dias = (fecha_corte - timezone.localdate(prestamo.fecha_vencimiento)).days
        por_sede[(sede.pk, sede.nombre)].append(
            {
                "multa": float(MULTA_DIARIA * dias),
                "prestamo_id": prestamo.pk,
                "socio_id": solicitud.socio_id,
                "numero_socio": solicitud.socio.numero_socio,
                "socio": solicitud.socio.nombre,
                "libro": solicitud.libro.titulo,
                "fecha_entrega": prestamo.fecha_entrega,
                "fecha_vencimiento": prestamo.fecha_vencimiento,
                "dias_atraso": dias,
            }
        )

    return [
        {
            "sede_id": sede_id,
            "sede": nombre_sede,
            "cantidad": len(prestamos_sede),
            "multas": sum(p["multa"] for p in prestamos_sede),
            "prestamos": prestamos_sede,
        }
        for (sede_id, nombre_sede), prestamos_sede in por_sede.items()
    ]
