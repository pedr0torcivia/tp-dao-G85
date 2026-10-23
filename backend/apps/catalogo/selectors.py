from django.db.models import Count, Q, QuerySet

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


def obtener_ejemplar(*, ejemplar_id: int) -> Ejemplar:
    return Ejemplar.objects.select_related(
        "libro",
        "sede_propietaria",
        "sede_actual",
    ).get(id=ejemplar_id)


def disponibilidad_por_sede(
    *,
    libro_id: int | None = None,
    sede_id: int | None = None,
) -> list[dict]:
    ejemplares = Ejemplar.objects.all()

    if libro_id:
        ejemplares = ejemplares.filter(libro_id=libro_id)
    if sede_id:
        ejemplares = ejemplares.filter(sede_propietaria_id=sede_id)

    filas = (
        ejemplares.values(
            "sede_propietaria_id",
            "sede_propietaria__nombre",
        )
        .annotate(
            total=Count("id"),
            disponibles=Count(
                "id",
                filter=Q(estado="DISPONIBLE"),
            ),
        )
        .order_by("sede_propietaria__nombre")
    )

    return [
        {
            "sede_id": fila["sede_propietaria_id"],
            "sede": fila["sede_propietaria__nombre"],
            "total": fila["total"],
            "disponibles": fila["disponibles"],
            "no_disponibles": fila["total"] - fila["disponibles"],
            "proporcion_disponible": (fila["disponibles"] / fila["total"] if fila["total"] else 0),
        }
        for fila in filas
    ]
