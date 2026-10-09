from django.db.models import QuerySet

from .models import EstadoSede, Sede


def listar_sedes() -> QuerySet[Sede]:
    return Sede.objects.all()


def listar_sedes_activas() -> QuerySet[Sede]:
    return Sede.objects.filter(estado=EstadoSede.ACTIVA)


def obtener_sede(*, sede_id: int) -> Sede:
    return Sede.objects.get(id=sede_id)
