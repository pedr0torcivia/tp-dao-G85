from django.db import transaction

from .models import Libro


@transaction.atomic
def crear_libro(
    *,
    titulo: str,
    autor: str,
    editorial: str,
    edicion: str,
    isbn: str | None = None,
) -> Libro:
    libro = Libro(
        titulo=titulo.strip(),
        autor=autor.strip(),
        editorial=editorial.strip(),
        edicion=edicion.strip(),
        isbn=(isbn.strip() or None) if isbn is not None else None,
    )

    libro.full_clean()
    libro.save()

    return libro