from django.db import IntegrityError, transaction

from .exceptions import (
    SocioDuplicadoError,
    SocioInhabilitadoError,
    SocioYaHabilitadoError,
    SocioYaInhabilitadoError,
)
from .models import EstadoSocio, Socio


def _limpiar_campos(datos: dict[str, str]) -> dict[str, str]:
    return {campo: valor.strip() for campo, valor in datos.items()}


@transaction.atomic
def crear_socio(
    *,
    numero_socio: str,
    documento: str,
    nombre: str,
    contacto: str,
) -> Socio:
    try:
        return Socio.objects.create(
            **_limpiar_campos(
                {
                    "numero_socio": numero_socio,
                    "documento": documento,
                    "nombre": nombre,
                    "contacto": contacto,
                }
            )
        )
    except IntegrityError as error:
        raise SocioDuplicadoError(
            "Ya existe un socio con ese número de socio o documento."
        ) from error


@transaction.atomic
def actualizar_socio(*, socio: Socio, **datos: str) -> Socio:
    socio = Socio.objects.select_for_update().get(pk=socio.pk)

    for campo, valor in _limpiar_campos(datos).items():
        setattr(socio, campo, valor)

    try:
        socio.save(update_fields=list(datos.keys()))
    except IntegrityError as error:
        raise SocioDuplicadoError(
            "Ya existe un socio con ese número de socio o documento."
        ) from error

    return socio


@transaction.atomic
def habilitar_socio(*, socio: Socio) -> Socio:
    socio = Socio.objects.select_for_update().get(pk=socio.pk)

    if socio.estado == EstadoSocio.HABILITADO:
        raise SocioYaHabilitadoError("El socio ya se encuentra habilitado.")

    socio.estado = EstadoSocio.HABILITADO
    socio.save(update_fields=["estado"])
    return socio


@transaction.atomic
def inhabilitar_socio(*, socio: Socio) -> Socio:
    socio = Socio.objects.select_for_update().get(pk=socio.pk)

    if socio.estado == EstadoSocio.INHABILITADO:
        raise SocioYaInhabilitadoError("El socio ya se encuentra inhabilitado.")

    socio.estado = EstadoSocio.INHABILITADO
    socio.save(update_fields=["estado"])
    return socio


def validar_socio_habilitado(*, socio: Socio) -> None:
    if socio.estado != EstadoSocio.HABILITADO:
        raise SocioInhabilitadoError(
            f"El socio '{socio.numero_socio}' se encuentra inhabilitado."
        )