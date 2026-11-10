from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from apps.sedes.exceptions import SedeInactivaError
from apps.sedes.services import validar_sede_activa

from .exceptions import (
    CodigoInventarioDuplicadoError,
    EjemplarComprometidoError,
    EjemplarDadoDeBajaError,
    EjemplarInconsistenteError,
    EjemplarNoAsignadoError,
    EjemplarNoDisponibleError,
    EjemplarNoRevisadoError,
    FotoInvalidaError,
    SedePropietariaInactivaError,
)
from .models import CondicionFisica, Ejemplar, EstadoEjemplar, Libro


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
        campo = "isbn" if libro.isbn else "titulo"
        raise ValidationError({campo: "Ya existe esa edición en el catálogo."}) from error

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
        estado=(
            EstadoEjemplar.DISPONIBLE
            if condicion_fisica.strip() == CondicionFisica.APTO
            else EstadoEjemplar.EN_REVISION
        ),
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
    if ejemplar.condicion_fisica != CondicionFisica.APTO:
        if ejemplar.estado not in (EstadoEjemplar.DISPONIBLE, EstadoEjemplar.EN_REVISION):
            raise EjemplarComprometidoError("No se modifica la condición de material comprometido.")
        ejemplar.estado = EstadoEjemplar.EN_REVISION
    ejemplar.full_clean()
    ejemplar.save(update_fields=["condicion_fisica", "estado"])
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


FOTO_MAXIMA = 3 * 1024 * 1024
FIRMAS_IMAGEN = {
    b"\xff\xd8\xff": "image/jpeg",
    b"\x89PNG\r\n\x1a\n": "image/png",
}


def tipo_de_imagen(contenido: bytes) -> str | None:
    """Identifica la imagen por su firma real, no por el nombre del archivo."""
    for firma, tipo in FIRMAS_IMAGEN.items():
        if contenido.startswith(firma):
            return tipo
    if contenido[:4] == b"RIFF" and contenido[8:12] == b"WEBP":
        return "image/webp"
    return None


@transaction.atomic
def guardar_foto_ejemplar(*, ejemplar: Ejemplar, contenido: bytes) -> Ejemplar:
    if len(contenido) > FOTO_MAXIMA:
        raise FotoInvalidaError("La foto no puede superar los 3 MB.")
    tipo = tipo_de_imagen(contenido)
    if tipo is None:
        raise FotoInvalidaError("La foto debe ser una imagen JPG, PNG o WEBP.")
    ejemplar = Ejemplar.objects.select_for_update().get(pk=ejemplar.pk)
    ejemplar.foto = contenido
    ejemplar.foto_tipo = tipo
    ejemplar.save(update_fields=["foto", "foto_tipo"])
    return ejemplar


@transaction.atomic
def quitar_foto_ejemplar(*, ejemplar: Ejemplar) -> Ejemplar:
    ejemplar = Ejemplar.objects.select_for_update().get(pk=ejemplar.pk)
    ejemplar.foto = None
    ejemplar.foto_tipo = ""
    ejemplar.save(update_fields=["foto", "foto_tipo"])
    return ejemplar


@transaction.atomic
def dar_de_baja_ejemplar(*, ejemplar: Ejemplar) -> Ejemplar:
    """Baja lógica del ejemplar: el registro se conserva con estado BAJA."""
    ejemplar = Ejemplar.objects.select_for_update().get(pk=ejemplar.pk)

    if ejemplar.estado == EstadoEjemplar.BAJA:
        raise EjemplarDadoDeBajaError("El ejemplar ya está dado de baja.")

    if ejemplar.estado not in (EstadoEjemplar.DISPONIBLE, EstadoEjemplar.EN_REVISION):
        raise EjemplarComprometidoError("No se puede dar de baja un ejemplar comprometido.")

    ejemplar.estado = EstadoEjemplar.BAJA
    ejemplar.save(update_fields=["estado"])
    return ejemplar


@transaction.atomic
def aprobar_disponibilidad_ejemplar(*, ejemplar: Ejemplar) -> Ejemplar:
    """Da por revisado un ejemplar apto en su sede propietaria activa."""
    ejemplar = Ejemplar.objects.select_for_update().get(pk=ejemplar.pk)

    if ejemplar.estado != EstadoEjemplar.EN_REVISION:
        raise EjemplarNoRevisadoError("El ejemplar debe estar en revisión.")

    if ejemplar.condicion_fisica != CondicionFisica.APTO:
        raise EjemplarInconsistenteError("La condición física debe ser apta para préstamo.")

    if ejemplar.sede_actual_id != ejemplar.sede_propietaria_id:
        raise EjemplarInconsistenteError("El ejemplar debe estar en su sede propietaria.")

    try:
        validar_sede_activa(sede=ejemplar.sede_propietaria)
    except SedeInactivaError as error:
        raise SedePropietariaInactivaError(str(error)) from error

    ejemplar.estado = EstadoEjemplar.DISPONIBLE
    ejemplar.save(update_fields=["estado"])
    return ejemplar
