from django.db.models import Q, QuerySet

from .models import Libro


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
