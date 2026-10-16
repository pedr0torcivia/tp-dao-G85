from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from apps.sedes.exceptions import SedeInactivaError
from apps.sedes.services import validar_sede_activa

from .exceptions import (
    CodigoInventarioDuplicadoError,
    EjemplarDadoDeBajaError,
    EjemplarNoAsignadoError,
    EjemplarNoDisponibleError,
    SedePropietariaInactivaError,
)
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

    try:
        libro.full_clean()
        libro.save()
    except IntegrityError as error:
        raise ValidationError({"isbn": "Ya existe un libro con ese ISBN."}) from error

    return libro


@transaction.atomic
def crear_ejemplar(
    *,
    codigo_inventario: str,
    libro: Libro,
    sede_propietaria,
    condicion_fisica: str,
) -> Ejemplar:
    try:
        validar_sede_activa(sede=sede_propietaria)
    except SedeInactivaError as error:
        raise SedePropietariaInactivaError(str(error)) from error

    ejemplar = Ejemplar(
        codigo_inventario=codigo_inventario.strip(),
        libro=libro,
        sede_propietaria=sede_propietaria,
        sede_actual=sede_propietaria,
        estado=EstadoEjemplar.DISPONIBLE,
        condicion_fisica=condicion_fisica.strip(),
    )

    try:
        ejemplar.full_clean()
        ejemplar.save()
    except ValidationError as error:
        if "codigo_inventario" in error.message_dict:
            raise CodigoInventarioDuplicadoError(
                "Ya existe un ejemplar con ese código de inventario."
            ) from error
        raise
    except IntegrityError as error:
        raise CodigoInventarioDuplicadoError(
            "Ya existe un ejemplar con ese código de inventario."
        ) from error

    return ejemplar


@transaction.atomic
def actualizar_libro(*, libro: Libro, datos: dict) -> Libro:
    libro = Libro.objects.select_for_update().get(pk=libro.pk)

    for campo in ("titulo", "autor", "editorial", "edicion"):
        if campo in datos:
            setattr(libro, campo, datos[campo].strip())
    if "isbn" in datos:
        libro.isbn = datos["isbn"].strip() if datos["isbn"] else None

    libro.full_clean()
    libro.save()
    return libro


@transaction.atomic
def actualizar_condicion_ejemplar(*, ejemplar: Ejemplar, condicion_fisica: str) -> Ejemplar:
    ejemplar = Ejemplar.objects.select_for_update().get(pk=ejemplar.pk)

    if ejemplar.estado == EstadoEjemplar.BAJA:
        raise EjemplarDadoDeBajaError("El ejemplar está dado de baja.")

    ejemplar.condicion_fisica = condicion_fisica.strip()
    ejemplar.full_clean()
    ejemplar.save(update_fields=["condicion_fisica"])
    return ejemplar


@transaction.atomic
def asignar_ejemplar(*, ejemplar: Ejemplar) -> Ejemplar:
    ejemplar = Ejemplar.objects.select_for_update().get(pk=ejemplar.pk)

    if ejemplar.estado != EstadoEjemplar.DISPONIBLE:
        raise EjemplarNoDisponibleError(
            f"El ejemplar está en estado {ejemplar.get_estado_display()}."
        )

    ejemplar.estado = EstadoEjemplar.ASIGNADO
    ejemplar.save(update_fields=["estado"])
    return ejemplar


@transaction.atomic
def liberar_ejemplar(*, ejemplar: Ejemplar) -> Ejemplar:
    ejemplar = Ejemplar.objects.select_for_update().get(pk=ejemplar.pk)

    if ejemplar.estado != EstadoEjemplar.ASIGNADO:
        raise EjemplarNoAsignadoError("El ejemplar no está asignado.")

    ejemplar.estado = EstadoEjemplar.DISPONIBLE
    ejemplar.save(update_fields=["estado"])
    return ejemplar
