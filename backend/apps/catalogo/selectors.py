from django.db.models import Q, QuerySet

from .models import Ejemplar, Libro


def listar_libros(*, search: str | None = None) -> QuerySet[Libro]:
    libros = Libro.objects.all().order_by("titulo", "id")

    if search:
        termino = search.strip()

        if termino:
            libros = libros.filter(
                Q(titulo__icontains=termino)
                | Q(autor__icontains=termino)
                | Q(isbn__icontains=termino)
            )

    return libros


def obtener_libro(*, libro_id: int) -> Libro:
    return Libro.objects.get(id=libro_id)


def listar_ejemplares(
    *,
    libro_id: int | None = None,
    sede_id: int | None = None,
    estado: str | None = None,
) -> QuerySet[Ejemplar]:
    ejemplares = Ejemplar.objects.select_related(
        "libro",
        "sede_propietaria",
        "sede_actual",
    ).order_by("codigo_inventario", "id")

    if libro_id:
        ejemplares = ejemplares.filter(libro_id=libro_id)

    if sede_id:
        ejemplares = ejemplares.filter(sede_propietaria_id=sede_id)

    if estado:
        ejemplares = ejemplares.filter(estado=estado)

    return ejemplares
