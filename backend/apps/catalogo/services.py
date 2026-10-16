from django.db import transaction

from apps.sedes.services import validar_sede_activa

from .models import Ejemplar, EstadoEjemplar, Libro


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


@transaction.atomic
def crear_ejemplar(
    *,
    codigo_inventario: str,
    libro: Libro,
    sede_propietaria,
    condicion_fisica: str,
) -> Ejemplar:
    validar_sede_activa(sede=sede_propietaria)

    ejemplar = Ejemplar(
        codigo_inventario=codigo_inventario.strip(),
        libro=libro,
        sede_propietaria=sede_propietaria,
        sede_actual=sede_propietaria,
        estado=EstadoEjemplar.DISPONIBLE,
        condicion_fisica=condicion_fisica.strip(),
    )

    ejemplar.full_clean()
    ejemplar.save()

    return ejemplar