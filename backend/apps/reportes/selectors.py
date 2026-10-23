from collections import defaultdict
from datetime import date

from apps.circulacion.models import Prestamo


def obtener_prestamos_vencidos(*, fecha_corte: date) -> list[dict]:
    prestamos = (
        Prestamo.objects.filter(
            fecha_vencimiento__lt=fecha_corte,
            fecha_devolucion__isnull=True,
        )
        .select_related(
            "solicitud__socio",
            "solicitud__sede_destino",
        )
        .order_by(
            "solicitud__sede_destino__nombre",
            "fecha_vencimiento",
            "id",
        )
    )

    por_sede = defaultdict(list)

    for prestamo in prestamos:
        solicitud = prestamo.solicitud
        sede = solicitud.sede_destino

        por_sede[(sede.pk, sede.nombre)].append(
            {
                "prestamo_id": prestamo.pk,
                "socio_id": solicitud.socio_id,
                "numero_socio": solicitud.socio.numero_socio,
                "socio": solicitud.socio.nombre,
                "fecha_entrega": prestamo.fecha_entrega,
                "fecha_vencimiento": prestamo.fecha_vencimiento,
                "dias_atraso": (fecha_corte - prestamo.fecha_vencimiento).days,
            }
        )

    return [
        {
            "sede_id": sede_id,
            "sede": nombre_sede,
            "cantidad": len(prestamos_sede),
            "prestamos": prestamos_sede,
        }
        for (sede_id, nombre_sede), prestamos_sede in por_sede.items()
    ]