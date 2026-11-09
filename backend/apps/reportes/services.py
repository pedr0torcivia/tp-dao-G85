"""RP03 — Movimiento entre sedes.

Envíos despachados por par origen/destino y tránsito medio entre despacho y
recepción, calculado sólo sobre remitos recibidos. La fecha de corte es la
fecha de despacho. Un remito creado y no despachado no entra al reporte; uno
despachado sin recibir entra al conteo pero no al promedio.
"""

from datetime import date

from django.db.models import Q
from django.utils import timezone

from apps.catalogo.models import CondicionFisica, Ejemplar, EstadoEjemplar
from apps.circulacion.models import Prestamo, SolicitudPrestamo
from apps.logistica.models import EstadoRemito, Remito, ResultadoRecepcion

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
    "Estado actual de los ejemplares dados de alta dentro del período, por libro y sede "
    "propietaria. El rango filtra fecha de alta; no reconstruye el stock histórico. "
    "Un ejemplar cuenta como "
    "disponible cuando su estado es DISPONIBLE, su condición física es apta, "
    "descansa en su sede propietaria y esa sede está activa."
)


def disponibilidad_catalogo(
    *, sede_id: int | None = None, desde: date | None = None, hasta: date | None = None
) -> dict:
    """RP04 — Disponibilidad de catálogo por sede.

    El rango selecciona las altas; los estados y la disponibilidad son actuales.
    """
    ejemplares = Ejemplar.objects.select_related("libro", "sede_propietaria", "sede_actual")
    if desde is not None:
        ejemplares = ejemplares.filter(fecha_alta__date__gte=desde)
    if hasta is not None:
        ejemplares = ejemplares.filter(fecha_alta__date__lte=hasta)
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


def operaciones_abmc(*, desde: date, hasta: date, sede_id: int | None = None) -> dict:
    from apps.common.models import Operacion

    eventos = Operacion.objects.filter(fecha__date__gte=desde, fecha__date__lte=hasta)
    filas, totales = [], {"ALTA": 0, "MODIFICACION": 0, "BAJA": 0, "OPERACION": 0}
    for evento in eventos.order_by("fecha", "id"):
        if sede_id is not None and sede_id not in evento.sede_ids:
            continue
        totales[evento.accion] = totales.get(evento.accion, 0) + 1
        filas.append(
            {
                "fecha": evento.fecha,
                "entidad": evento.entidad,
                "registro_id": evento.registro_id,
                "accion": evento.accion,
                "usuario": evento.usuario,
                "descripcion": evento.descripcion,
            }
        )
    etiquetas = {
        "ALTA": ("alta", "altas"),
        "MODIFICACION": ("modificación", "modificaciones"),
        "BAJA": ("baja", "bajas"),
        "OPERACION": ("otra operación", "otras operaciones"),
    }
    detalle = ", ".join(
        f"{n} {etiquetas[accion][0 if n == 1 else 1]}" for accion, n in totales.items()
    )
    return {
        "reporte": "RP05",
        "filas": filas,
        "totales": totales,
        "resumen": f"{len(filas)} operaciones: {detalle}",
        "criterio": "Operaciones exitosas registradas entre Desde y Hasta, ambos inclusive, "
        "con usuario y cambios antes/después. Las consultas y los intentos fallidos "
        "no se cuentan como cambios. La baja es lógica y conserva el historial. "
        "Con sede se incluyen solo registros vinculados a esa sede; "
        "libros y socios globales se ven sin filtro de sede.",
    }


def activos_y_en_transito(*, desde: date, hasta: date, sede_id: int | None = None) -> dict:
    """RP06 — Préstamos abiertos al cierre del período y material que sigue viajando.

    Un préstamo cuenta si se entregó entre Desde y Hasta y no estaba devuelto al
    cierre de Hasta. El material en tránsito es el de los remitos despachados en
    el período que todavía no se recibieron.
    """
    prestamos = (
        Prestamo.objects.filter(
            Q(fecha_devolucion__isnull=True) | Q(fecha_devolucion__date__gt=hasta),
            fecha_entrega__date__gte=desde,
            fecha_entrega__date__lte=hasta,
        )
        .select_related(
            "solicitud__socio",
            "solicitud__libro",
            "solicitud__sede_destino",
            "solicitud__ejemplar",
        )
        .order_by("fecha_vencimiento")
    )
    if sede_id is not None:
        prestamos = prestamos.filter(solicitud__sede_destino_id=sede_id)

    filas = []
    for prestamo in prestamos:
        solicitud = prestamo.solicitud
        atraso = max(0, (hasta - timezone.localdate(prestamo.fecha_vencimiento)).days)
        filas.append(
            {
                "tipo": "PRESTAMO",
                "referencia": f"PRE-{prestamo.pk:04d}",
                "detalle": f"{solicitud.libro.titulo} · {solicitud.socio.nombre}",
                "ejemplar": solicitud.ejemplar.codigo_inventario if solicitud.ejemplar else "",
                "ubicacion": solicitud.sede_destino.nombre,
                "desde": prestamo.fecha_entrega,
                "situacion": f"Vencido hace {atraso} días" if atraso else "Al día",
            }
        )

    remitos = (
        Remito.objects.filter(
            estado=EstadoRemito.EN_TRANSITO,
            fecha_despacho__date__gte=desde,
            fecha_despacho__date__lte=hasta,
        )
        .select_related("sede_origen", "sede_destino")
        .prefetch_related("detalles__ejemplar__libro")
    )
    if sede_id is not None:
        remitos = remitos.filter(Q(sede_origen_id=sede_id) | Q(sede_destino_id=sede_id))
    en_transito = 0
    for remito in remitos:
        dias = (hasta - timezone.localdate(remito.fecha_despacho)).days
        for detalle in remito.detalles.all():
            en_transito += 1
            filas.append(
                {
                    "tipo": "TRANSITO",
                    "referencia": remito.numero,
                    "detalle": detalle.ejemplar.libro.titulo,
                    "ejemplar": detalle.ejemplar.codigo_inventario,
                    "ubicacion": f"{remito.sede_origen.nombre} → {remito.sede_destino.nombre}",
                    "desde": remito.fecha_despacho,
                    "situacion": f"{dias} días de viaje",
                }
            )

    activos = len(filas) - en_transito
    return {
        "reporte": "RP06",
        "criterio": (
            "Préstamos entregados en el período y abiertos al cierre de Hasta, por sede de "
            "entrega; y ejemplares de remitos despachados en el período que siguen en tránsito. "
            "Con sede: préstamos entregados allí y envíos que salen o llegan."
        ),
        "resumen": f"{activos} préstamos activos · {en_transito} ejemplares en tránsito",
        "filas": filas,
    }


def _tasa(grupo: dict) -> int | None:
    recibidos = grupo["exitosos"] + grupo["con_incidencias"]
    return round(grupo["exitosos"] / recibidos * 100) if recibidos else None


def efectividad_logistica(*, desde: date, hasta: date, sede_id: int | None = None) -> dict:
    """RP07 — Tasa de envíos exitosos e incidencias por trayecto.

    Un envío es exitoso si se recibió sin daños ni extravíos. La tasa se calcula
    sobre los envíos ya recibidos; los que siguen viajando se informan aparte.
    """
    filtros = Q(fecha_despacho__date__gte=desde) & Q(fecha_despacho__date__lte=hasta)
    if sede_id is not None:
        filtros &= Q(sede_origen_id=sede_id) | Q(sede_destino_id=sede_id)
    remitos = (
        Remito.objects.filter(filtros)
        .select_related("sede_origen", "sede_destino")
        .prefetch_related("detalles")
    )
    vacio = {
        "despachados": 0,
        "exitosos": 0,
        "con_incidencias": 0,
        "en_transito": 0,
        "danados": 0,
        "extraviados": 0,
    }
    grupos: dict[tuple[str, str], dict] = {}
    for remito in remitos:
        grupo = grupos.setdefault(
            (remito.sede_origen.nombre, remito.sede_destino.nombre), dict(vacio)
        )
        grupo["despachados"] += 1
        if remito.estado == EstadoRemito.EN_TRANSITO:
            grupo["en_transito"] += 1
        elif remito.estado == EstadoRemito.RECIBIDO_CON_INCIDENCIAS:
            grupo["con_incidencias"] += 1
        elif remito.estado == EstadoRemito.RECIBIDO:
            grupo["exitosos"] += 1
        for detalle in remito.detalles.all():
            if detalle.resultado_recepcion == ResultadoRecepcion.DANADO:
                grupo["danados"] += 1
            elif detalle.resultado_recepcion == ResultadoRecepcion.EXTRAVIADO:
                grupo["extraviados"] += 1

    filas = [
        {"origen": origen, "destino": destino, **grupo, "tasa_exito": _tasa(grupo)}
        for (origen, destino), grupo in sorted(grupos.items())
    ]
    total = {clave: sum(fila[clave] for fila in filas) for clave in vacio}
    tasa_total = _tasa(total)
    return {
        "reporte": "RP07",
        "criterio": (
            "Remitos despachados en el período, por trayecto. Exitoso: recibido sin "
            "incidencias. La tasa se calcula sobre los recibidos; los que siguen en tránsito "
            "se muestran aparte. Incidencias: ejemplares dañados o extraviados al recibir."
        ),
        "resumen": (
            f"{total['despachados']} envíos · {total['danados']} dañados · "
            f"{total['extraviados']} extraviados · tasa de éxito "
            + (f"{tasa_total} %" if tasa_total is not None else "sin recepciones")
        ),
        "totales": {**total, "tasa_exito": tasa_total},
        "filas": filas,
    }
