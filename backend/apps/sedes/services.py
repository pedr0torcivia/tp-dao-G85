from django.db import IntegrityError, transaction

from .exceptions import (
    NombreSedeDuplicadoError,
    SedeInactivaError,
    SedeYaActivaError,
    SedeYaDadaDeBajaError,
)
from .models import EstadoSede, Sede


@transaction.atomic
def crear_sede(
    *,
    nombre: str,
    direccion: str,
    contacto: str,
    horarios: str,
) -> Sede:
    try:
        return Sede.objects.create(
            nombre=nombre.strip(),
            direccion=direccion.strip(),
            contacto=contacto.strip(),
            horarios=horarios.strip(),
        )
    except IntegrityError as error:
        raise NombreSedeDuplicadoError("Ya existe una sede con ese nombre.") from error


@transaction.atomic
def dar_de_baja_sede(*, sede: Sede) -> Sede:
    sede = Sede.objects.select_for_update().get(pk=sede.pk)

    if sede.estado == EstadoSede.BAJA:
        raise SedeYaDadaDeBajaError("La sede ya se encuentra dada de baja.")

    # Las comprobaciones de operaciones activas se agregarán cuando existan
    # los préstamos, reservas y remitos.
    sede.estado = EstadoSede.BAJA
    sede.save(update_fields=["estado"])

    return sede


@transaction.atomic
def reactivar_sede(*, sede: Sede) -> Sede:
    sede = Sede.objects.select_for_update().get(pk=sede.pk)

    if sede.estado == EstadoSede.ACTIVA:
        raise SedeYaActivaError("La sede ya se encuentra activa.")

    sede.estado = EstadoSede.ACTIVA
    sede.save(update_fields=["estado"])

    return sede


def validar_sede_activa(*, sede: Sede) -> None:
    if sede.estado != EstadoSede.ACTIVA:
        raise SedeInactivaError(f"La sede '{sede.nombre}' se encuentra dada de baja.")
