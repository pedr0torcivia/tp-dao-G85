"""RP03 — Movimiento entre sedes.

Envíos despachados por par origen/destino y tránsito medio entre despacho y
recepción, calculado sólo sobre remitos recibidos. La fecha de corte es la
fecha de despacho. Un remito creado y no despachado no entra al reporte; uno
despachado sin recibir entra al conteo pero no al promedio.
"""

from datetime import date

from django.db.models import Q

from apps.catalogo.models import CondicionFisica, Ejemplar, EstadoEjemplar
from apps.circulacion.models import SolicitudPrestamo
from apps.logistica.models import Remito

NSEM = 86400

CRITERIO = (
    "Cuenta los envíos despachados por par de sedes dentro del rango de la fecha "
    "de despacho. El tránsito medio calcula despacho–recepción usando sólo los "
    "remitos que ya fueron recibidos."
)


def movimientos_entre_sedes(*, desde: date, hasta: date, sede_id: int | None = None) -> dict:
    filtros = Q(fecha_despacho__date__gte=desde) & Q(fecha_despacho__date__lte=hasta)
    if sede_id is not None:
        filtros &= Q(sede_origen_id=sede_id) | Q(sede_destino_id=sede_id)

    grupos: dict[tuple[int, int], dict[str, float]] = {}
    for remito in Remito.objects.filter(filtros).order_by("fecha_despacho", "id"):
        clave = (remito.sede_origen_id, remito.sede_destino_id)
        grupo = grupos.setdefault(clave, {"despachados": 0, "recibidos": 0, "dias_transito": 0.0})
        grupo["despachados"] += 1

        if remito.fecha_recepcion is None:
            continue
        transito = (remito.fecha_recepcion - remito.fecha_despacho).total_seconds() / NSEM
        grupo["recibidos"] += 1
        grupo["dias_transito"] += transito

    filas = []
    for (origen, destino), datos in sorted(grupos.items()):
        promedio = None
        if datos["recibidos"]:
            promedio = round(datos["dias_transito"] / datos["recibidos"], 2)
        filas.append(
            {
                "sede_origen_id": origen,
                "sede_destino_id": destino,
                "despachados": datos["despachados"],
                "recibidos": datos["recibidos"],
                "dias_transito_promedio": promedio,
            }
        )

    despachados = sum(datos["despachados"] for datos in grupos.values())
    return {
        "reporte": "RP03",
        "criterio": CRITERIO,
        "resumen": f"{despachados} envíos despachados",
        "filas": filas,
    }


CRITERIO_DEMANDA = (
    "Cuenta solicitudes interbibliotecarias por libro y sede solicitante (destino), "
    "dentro del rango de la fecha de solicitud. Se excluyen las rechazadas y las "
    "canceladas; también las locales."
)


def demanda_interbibliotecaria(
    *,
    desde: date,
    hasta: date,
    sede_id: int | None = None,
) -> dict:
    """RP02 — Ranking de demanda interbibliotecaria.

    Una solicitud cuenta cuando es del tipo interbibliotecario, no está
    rechazada ni cancelada, y su fecha de solicitud cae en el rango. El
    filtro de sede se aplica sobre la sede solicitante (el destino).
    """
    filtros = (
        Q(tipo="INTERBIBLIOTECARIO")
        & Q(fecha_solicitud__date__gte=desde)
        & Q(fecha_solicitud__date__lte=hasta)
    )
    excluidos = Q(estado="RECHAZADA") | Q(estado="CANCELADA")
    solicitudes = (
        SolicitudPrestamo.objects.filter(filtros)
        .exclude(excluidos)
        .select_related("libro", "sede_destino")
    )
    if sede_id is not None:
        solicitudes = solicitudes.filter(sede_destino_id=sede_id)

    grupos: dict[tuple[int, int], dict] = {}
    for solicitud in solicitudes:
        clave = (solicitud.libro_id, solicitud.sede_destino_id)
        grupo = grupos.setdefault(
            clave,
            {
                "libro": solicitud.libro.titulo,
                "sede_destino": solicitud.sede_destino.nombre,
                "cantidad": 0,
            },
        )
        grupo["cantidad"] += 1

    filas = [
        {
            "libro_id": libro_id,
            "libro": datos["libro"],
            "sede_destino_id": sede_id_fila,
            "sede_destino": datos["sede_destino"],
            "cantidad": datos["cantidad"],
        }
        for (libro_id, sede_id_fila), datos in sorted(
            grupos.items(), key=lambda item: (-item[1]["cantidad"], item[1]["libro"])
        )
    ]

    total = sum(fila["cantidad"] for fila in filas)
    return {
        "reporte": "RP02",
        "criterio": CRITERIO_DEMANDA,
        "resumen": f"{total} solicitudes válidas",
        "filas": filas,
    }


CRITERIO_DISPONIBILIDAD = (
    "Corte actual por libro y sede propietaria. Un ejemplar cuenta como "
    "disponible cuando su estado es DISPONIBLE, su condición física es apta, "
    "descansa en su sede propietaria y esa sede está activa."
)


def disponibilidad_catalogo(*, sede_id: int | None = None) -> dict:
    """RP04 — Disponibilidad de catálogo por sede.

    No usa rango de fechas: refleja el estado actual de los ejemplares.
    """
    ejemplares = Ejemplar.objects.select_related("libro", "sede_propietaria", "sede_actual")
    if sede_id is not None:
        ejemplares = ejemplares.filter(sede_propietaria_id=sede_id)

    grupos: dict[tuple[int, int], dict] = {}
    for ejemplar in ejemplares:
        clave = (ejemplar.libro_id, ejemplar.sede_propietaria_id)
        grupo = grupos.setdefault(
            clave,
            {
                "libro": ejemplar.libro.titulo,
                "sede_propietaria": ejemplar.sede_propietaria.nombre,
                "sede_activa": ejemplar.sede_propietaria.estado == "ACTIVA",
                "total": 0,
                "disponibles": 0,
                "por_estado": {},
            },
        )
        grupo["total"] += 1
        grupo["por_estado"][ejemplar.estado] = grupo["por_estado"].get(ejemplar.estado, 0) + 1

        disponible = (
            ejemplar.estado == EstadoEjemplar.DISPONIBLE
            and ejemplar.condicion_fisica == CondicionFisica.APTO
            and ejemplar.sede_actual_id == ejemplar.sede_propietaria_id
            and grupo["sede_activa"]
        )
        if disponible:
            grupo["disponibles"] += 1

    filas = [
        {
            "libro_id": libro_id_fila,
            "libro": datos["libro"],
            "sede_propietaria_id": sede_id_fila,
            "sede_propietaria": datos["sede_propietaria"],
            "total": datos["total"],
            "disponibles": datos["disponibles"],
            "proporcion_porcentaje": (
                round(datos["disponibles"] / datos["total"] * 100) if datos["total"] else 0
            ),
            "por_estado": datos["por_estado"],
        }
        for (libro_id_fila, sede_id_fila), datos in sorted(
            grupos.items(), key=lambda item: (item[1]["libro"], item[1]["sede_propietaria"])
        )
    ]

    total_gral = sum(fila["total"] for fila in filas)
    disponibles_gral = sum(fila["disponibles"] for fila in filas)
    return {
        "reporte": "RP04",
        "criterio": CRITERIO_DISPONIBILIDAD,
        "resumen": f"{disponibles_gral} de {total_gral} ejemplares disponibles",
        "filas": filas,
    }