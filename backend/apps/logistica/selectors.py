from django.db.models import QuerySet

from .models import DetalleRemito, EventoRemito, Remito


def listar_remitos(*, estado: str | None = None) -> QuerySet[Remito]:
    queryset = Remito.objects.all()
    if estado:
        queryset = queryset.filter(estado=estado)
    return queryset


def obtener_remito(*, remito_id: int) -> Remito:
    return Remito.objects.get(pk=remito_id)


def listar_detalles(*, remito_id: int) -> QuerySet[DetalleRemito]:
    return DetalleRemito.objects.filter(remito_id=remito_id)


def historial_remito(*, remito_id: int) -> QuerySet[EventoRemito]:
    return EventoRemito.objects.filter(remito_id=remito_id)
