from django.db.models import Q, QuerySet

from .models import EstadoSocio, Socio


def listar_socios() -> QuerySet[Socio]:
    return Socio.objects.order_by("nombre", "numero_socio")


def buscar_socios(
    *,
    busqueda: str | None = None,
    estado: str | None = None,
) -> QuerySet[Socio]:
    socios = listar_socios()

    if estado:
        socios = socios.filter(estado=estado)

    if busqueda:
        socios = socios.filter(
            Q(numero_socio__icontains=busqueda)
            | Q(documento__icontains=busqueda)
            | Q(nombre__icontains=busqueda)
            | Q(contacto__icontains=busqueda)
        )

    return socios


def listar_socios_habilitados() -> QuerySet[Socio]:
    return listar_socios().filter(estado=EstadoSocio.HABILITADO)


def obtener_socio(*, socio_id: int) -> Socio:
    return Socio.objects.get(pk=socio_id)