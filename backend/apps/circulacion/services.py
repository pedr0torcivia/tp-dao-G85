from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.catalogo.models import (
    CondicionFisica,
    Ejemplar,
    EstadoEjemplar,
)
from apps.sedes.services import validar_sede_activa
from apps.socios.models import EstadoSocio, Socio

from .exceptions import (
    EjemplarEnOtraSedeError,
    EjemplarNoAptoError,
    EjemplarNoCorrespondeError,
    EjemplarNoDisponibleError,
    EstadoReservaInvalidoError,
    EstadoSolicitudInvalidoError,
    FechaLimiteReservaInvalidaError,
    FechaPrestamoInvalidaError,
    PrestamoYaCreadoError,
    PrestamoYaDevueltoError,
    ReservaDuplicadaError,
    ReservaVencidaError,
    SocioInhabilitadoError,
    SolicitudEnRemitoVigenteError,
)
from .models import (
    EstadoReserva,
    EstadoSolicitud,
    Prestamo,
    Reserva,
    SolicitudPrestamo,
    TipoSolicitud,
)
from .strategies import obtener_estrategia


def validar_socio_habilitado(*, socio: Socio) -> None:
    if socio.estado != EstadoSocio.HABILITADO:
        raise SocioInhabilitadoError(f"El socio '{socio.numero_socio}' está inhabilitado.")


@transaction.atomic
def crear_solicitud(
    *,
    socio: Socio,
    libro,
    sede_origen,
    sede_destino,
    tipo: str,
) -> SolicitudPrestamo:
    validar_socio_habilitado(socio=socio)
    validar_sede_activa(sede=sede_origen)
    validar_sede_activa(sede=sede_destino)

    estrategia = obtener_estrategia(tipo)
    estrategia.validar_creacion(
        sede_origen=sede_origen,
        sede_destino=sede_destino,
    )

    return SolicitudPrestamo.objects.create(
        socio=socio,
        libro=libro,
        sede_origen=sede_origen,
        sede_destino=sede_destino,
        tipo=tipo,
        estado=EstadoSolicitud.PENDIENTE,
    )


def crear_solicitud_local(
    *,
    socio: Socio,
    libro,
    sede_origen,
    sede_destino,
) -> SolicitudPrestamo:
    """Compatibilidad con el primer incremento del flujo local."""
    return crear_solicitud(
        socio=socio,
        libro=libro,
        sede_origen=sede_origen,
        sede_destino=sede_destino,
        tipo=TipoSolicitud.LOCAL,
    )


@transaction.atomic
def asignar_ejemplar(
    *,
    solicitud: SolicitudPrestamo,
    ejemplar: Ejemplar,
) -> SolicitudPrestamo:
    solicitud = (
        SolicitudPrestamo.objects.select_for_update(of=("self",))
        .select_related(
            "socio",
            "libro",
            "sede_origen",
            "sede_destino",
        )
        .get(pk=solicitud.pk)
    )

    ejemplar = (
        Ejemplar.objects.select_for_update(of=("self",))
        .select_related(
            "libro",
            "sede_propietaria",
            "sede_actual",
        )
        .get(pk=ejemplar.pk)
    )

    if solicitud.estado != EstadoSolicitud.PENDIENTE:
        raise EstadoSolicitudInvalidoError("Solo se puede asignar una solicitud pendiente.")

    validar_socio_habilitado(socio=solicitud.socio)
    validar_sede_activa(sede=solicitud.sede_origen)
    validar_sede_activa(sede=solicitud.sede_destino)

    if ejemplar.estado != EstadoEjemplar.DISPONIBLE:
        raise EjemplarNoDisponibleError("El ejemplar seleccionado no está disponible.")

    if ejemplar.condicion_fisica != CondicionFisica.APTO:
        raise EjemplarNoAptoError("El ejemplar no está apto para préstamo.")

    if ejemplar.libro_id != solicitud.libro_id:
        raise EjemplarNoCorrespondeError("El ejemplar no corresponde al libro solicitado.")

    if ejemplar.sede_propietaria_id != solicitud.sede_origen_id:
        raise EjemplarEnOtraSedeError("La sede propietaria del ejemplar no coincide con el origen.")

    if ejemplar.sede_actual_id != solicitud.sede_origen_id:
        raise EjemplarEnOtraSedeError(
            "El ejemplar no se encuentra actualmente en la sede de origen."
        )

    solicitud.ejemplar = ejemplar
    solicitud.estado = EstadoSolicitud.ASIGNADA
    ejemplar.estado = EstadoEjemplar.ASIGNADO

    solicitud.save(update_fields=["ejemplar", "estado"])
    ejemplar.save(update_fields=["estado"])

    return solicitud


@transaction.atomic
def preparar_entrega(
    *,
    solicitud: SolicitudPrestamo,
) -> SolicitudPrestamo:
    solicitud = (
        SolicitudPrestamo.objects.select_for_update(of=("self",))
        .select_related("ejemplar")
        .get(pk=solicitud.pk)
    )

    if solicitud.ejemplar_id is None:
        raise EstadoSolicitudInvalidoError("La solicitud todavía no tiene un ejemplar asignado.")

    ejemplar = Ejemplar.objects.select_for_update().get(pk=solicitud.ejemplar_id)

    estrategia = obtener_estrategia(solicitud.tipo)
    estrategia.preparar_entrega(
        solicitud=solicitud,
        ejemplar=ejemplar,
    )

    return solicitud


@transaction.atomic
def entregar_solicitud(
    *,
    solicitud: SolicitudPrestamo,
    fecha_entrega,
    fecha_vencimiento,
) -> Prestamo:
    solicitud = (
        SolicitudPrestamo.objects.select_for_update(of=("self",))
        .select_related(
            "socio",
            "sede_destino",
            "ejemplar",
        )
        .get(pk=solicitud.pk)
    )

    if solicitud.estado != EstadoSolicitud.LISTA_PARA_ENTREGA:
        raise EstadoSolicitudInvalidoError("La solicitud no está lista para entregar.")

    if solicitud.ejemplar_id is None:
        raise EstadoSolicitudInvalidoError("La solicitud no tiene un ejemplar asignado.")

    ejemplar = Ejemplar.objects.select_for_update().get(pk=solicitud.ejemplar_id)

    if ejemplar.estado != EstadoEjemplar.LISTO_PARA_ENTREGA:
        raise EstadoSolicitudInvalidoError("El ejemplar no está listo para entregar.")

    if ejemplar.sede_actual_id != solicitud.sede_destino_id:
        raise EjemplarEnOtraSedeError("El ejemplar no se encuentra en la sede de entrega.")

    validar_socio_habilitado(socio=solicitud.socio)
    validar_sede_activa(sede=solicitud.sede_destino)

    if fecha_vencimiento <= fecha_entrega:
        raise FechaPrestamoInvalidaError("El vencimiento debe ser posterior a la entrega.")

    if Prestamo.objects.filter(solicitud=solicitud).exists():
        raise PrestamoYaCreadoError("La solicitud ya generó un préstamo.")

    reserva = None
    if solicitud.reserva_id is not None:
        reserva = Reserva.objects.select_for_update().get(pk=solicitud.reserva_id)
        if reserva.estado != EstadoReserva.LISTA_PARA_RETIRO:
            raise EstadoReservaInvalidoError("La reserva asociada no está lista para retirar.")
        if reserva.fecha_limite_retiro is None or fecha_entrega > reserva.fecha_limite_retiro:
            raise ReservaVencidaError("El plazo de retiro de la reserva venció.")

    prestamo = Prestamo.objects.create(
        solicitud=solicitud,
        fecha_entrega=fecha_entrega,
        fecha_vencimiento=fecha_vencimiento,
    )

    solicitud.estado = EstadoSolicitud.CUMPLIDA
    ejemplar.estado = EstadoEjemplar.PRESTADO

    if reserva is not None:
        reserva.estado = EstadoReserva.CUMPLIDA
        reserva.save(update_fields=["estado"])

    solicitud.save(update_fields=["estado"])
    ejemplar.save(update_fields=["estado"])

    return prestamo


@transaction.atomic
def registrar_devolucion(
    *,
    prestamo: Prestamo,
    fecha_devolucion,
    condicion_devolucion: str,
) -> Prestamo:
    prestamo = (
        Prestamo.objects.select_for_update(of=("self",))
        .select_related("solicitud")
        .get(pk=prestamo.pk)
    )

    if prestamo.fecha_devolucion is not None:
        raise PrestamoYaDevueltoError("El préstamo ya fue devuelto.")

    if fecha_devolucion < prestamo.fecha_entrega:
        raise FechaPrestamoInvalidaError("La devolución no puede ser anterior a la entrega.")

    if condicion_devolucion not in CondicionFisica.values:
        raise FechaPrestamoInvalidaError("La condición de devolución no es válida.")

    solicitud = prestamo.solicitud

    if solicitud.ejemplar_id is None:
        raise EstadoSolicitudInvalidoError("El préstamo no tiene un ejemplar asociado.")

    ejemplar = Ejemplar.objects.select_for_update().get(pk=solicitud.ejemplar_id)

    prestamo.fecha_devolucion = fecha_devolucion
    prestamo.condicion_devolucion = condicion_devolucion

    ejemplar.estado = EstadoEjemplar.EN_REVISION
    ejemplar.condicion_fisica = condicion_devolucion

    prestamo.save(
        update_fields=[
            "fecha_devolucion",
            "condicion_devolucion",
        ]
    )
    ejemplar.save(
        update_fields=[
            "estado",
            "condicion_fisica",
        ]
    )

    return prestamo


@transaction.atomic
def cancelar_solicitud(
    *,
    solicitud: SolicitudPrestamo,
) -> SolicitudPrestamo:
    solicitud = SolicitudPrestamo.objects.select_for_update().get(pk=solicitud.pk)

    estados_cancelables = {
        EstadoSolicitud.PENDIENTE,
        EstadoSolicitud.ASIGNADA,
    }

    if solicitud.estado not in estados_cancelables:
        raise EstadoSolicitudInvalidoError("La solicitud no puede cancelarse en su estado actual.")

    if solicitud.detalles_remito.exclude(remito__estado__in=("CANCELADO", "RECIBIDO")).exists():
        raise SolicitudEnRemitoVigenteError(
            "La solicitud pertenece a un remito vigente. Cancelá primero el remito."
        )

    if solicitud.ejemplar_id is not None:
        ejemplar = Ejemplar.objects.select_for_update().get(pk=solicitud.ejemplar_id)
        ejemplar.estado = EstadoEjemplar.DISPONIBLE
        ejemplar.save(update_fields=["estado"])

    solicitud.estado = EstadoSolicitud.CANCELADA
    solicitud.save(update_fields=["estado"])

    return solicitud


@transaction.atomic
def rechazar_solicitud(*, solicitud: SolicitudPrestamo) -> SolicitudPrestamo:
    solicitud = SolicitudPrestamo.objects.select_for_update().get(pk=solicitud.pk)

    if solicitud.estado != EstadoSolicitud.PENDIENTE:
        raise EstadoSolicitudInvalidoError("Solo puede rechazarse una solicitud pendiente.")

    solicitud.estado = EstadoSolicitud.RECHAZADA
    solicitud.save(update_fields=["estado"])
    return solicitud


@transaction.atomic
def crear_reserva(*, socio: Socio, libro, sede_retiro) -> Reserva:
    validar_socio_habilitado(socio=socio)
    validar_sede_activa(sede=sede_retiro)

    try:
        return Reserva.objects.create(
            socio=socio,
            libro=libro,
            sede_retiro=sede_retiro,
            estado=EstadoReserva.PENDIENTE,
        )
    except IntegrityError as error:
        raise ReservaDuplicadaError(
            "Ya existe una reserva vigente para ese socio, libro y sede."
        ) from error


@transaction.atomic
def asignar_reserva(
    *,
    reserva: Reserva,
    ejemplar: Ejemplar,
    fecha_limite_retiro,
) -> Reserva:
    reserva = (
        Reserva.objects.select_for_update(of=("self",))
        .select_related("socio", "libro", "sede_retiro")
        .get(pk=reserva.pk)
    )
    ejemplar = (
        Ejemplar.objects.select_for_update(of=("self",))
        .select_related("libro", "sede_propietaria", "sede_actual")
        .get(pk=ejemplar.pk)
    )

    if reserva.estado != EstadoReserva.PENDIENTE:
        raise EstadoReservaInvalidoError("Solo puede asignarse una reserva pendiente.")

    validar_socio_habilitado(socio=reserva.socio)
    validar_sede_activa(sede=reserva.sede_retiro)

    if fecha_limite_retiro <= timezone.now():
        raise FechaLimiteReservaInvalidaError("La fecha límite de retiro debe ser futura.")
    if ejemplar.estado != EstadoEjemplar.DISPONIBLE:
        raise EjemplarNoDisponibleError("El ejemplar no está disponible.")
    if ejemplar.condicion_fisica != CondicionFisica.APTO:
        raise EjemplarNoAptoError("El ejemplar no está apto para préstamo.")
    if ejemplar.libro_id != reserva.libro_id:
        raise EjemplarNoCorrespondeError("El ejemplar no corresponde al libro reservado.")
    if (
        ejemplar.sede_propietaria_id != reserva.sede_retiro_id
        or ejemplar.sede_actual_id != reserva.sede_retiro_id
    ):
        raise EjemplarEnOtraSedeError(
            "El ejemplar debe pertenecer y encontrarse en la sede de retiro."
        )

    reserva.ejemplar_asignado = ejemplar
    reserva.fecha_limite_retiro = fecha_limite_retiro
    reserva.estado = EstadoReserva.LISTA_PARA_RETIRO
    ejemplar.estado = EstadoEjemplar.LISTO_PARA_ENTREGA

    reserva.save(update_fields=["ejemplar_asignado", "fecha_limite_retiro", "estado"])
    ejemplar.save(update_fields=["estado"])
    SolicitudPrestamo.objects.create(
        socio=reserva.socio,
        libro=reserva.libro,
        ejemplar=ejemplar,
        sede_origen=reserva.sede_retiro,
        sede_destino=reserva.sede_retiro,
        reserva=reserva,
        tipo=TipoSolicitud.LOCAL,
        estado=EstadoSolicitud.LISTA_PARA_ENTREGA,
    )
    return reserva


def _cerrar_reserva(*, reserva: Reserva, estado: str) -> Reserva:
    if reserva.estado not in (
        EstadoReserva.PENDIENTE,
        EstadoReserva.LISTA_PARA_RETIRO,
    ):
        raise EstadoReservaInvalidoError("La reserva ya se encuentra cerrada.")

    if reserva.ejemplar_asignado_id is not None:
        ejemplar = Ejemplar.objects.select_for_update().get(pk=reserva.ejemplar_asignado_id)
        ejemplar.estado = EstadoEjemplar.DISPONIBLE
        ejemplar.save(update_fields=["estado"])

    solicitud = SolicitudPrestamo.objects.filter(reserva=reserva).first()
    if solicitud is not None and solicitud.estado != EstadoSolicitud.CUMPLIDA:
        solicitud.estado = EstadoSolicitud.CANCELADA
        solicitud.save(update_fields=["estado"])

    reserva.estado = estado
    reserva.save(update_fields=["estado"])
    return reserva


@transaction.atomic
def cancelar_reserva(*, reserva: Reserva) -> Reserva:
    reserva = Reserva.objects.select_for_update().get(pk=reserva.pk)
    return _cerrar_reserva(reserva=reserva, estado=EstadoReserva.CANCELADA)


@transaction.atomic
def expirar_reserva(*, reserva: Reserva, fecha_actual=None) -> Reserva:
    reserva = Reserva.objects.select_for_update().get(pk=reserva.pk)
    fecha_actual = fecha_actual or timezone.now()

    if reserva.estado != EstadoReserva.LISTA_PARA_RETIRO:
        raise EstadoReservaInvalidoError("Solo puede expirar una reserva lista para retiro.")
    if reserva.fecha_limite_retiro is None or reserva.fecha_limite_retiro >= fecha_actual:
        raise ReservaVencidaError("La reserva todavía no alcanzó su vencimiento.")

    return _cerrar_reserva(reserva=reserva, estado=EstadoReserva.EXPIRADA)
