"""RP03 — Movimiento entre sedes.

Envíos despachados por par origen/destino y tránsito medio entre despacho y
recepción, calculado sólo sobre remitos recibidos. La fecha de corte es la
fecha de despacho. Un remito creado y no despachado no entra al reporte; uno
despachado sin recibir entra al conteo pero no al promedio.
"""

from datetime import date

from django.db.models import Q

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
