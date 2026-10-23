from django.db import transaction
from django.utils import timezone

from apps.catalogo.models import CondicionFisica, Ejemplar, EstadoEjemplar
from apps.sedes.services import validar_sede_activa
from apps.socios.models import EstadoSocio, Socio

from .exceptions import (
    EjemplarEnOtraSedeError,
    EjemplarNoAptoError,
    EjemplarNoCorrespondeError,
    EjemplarNoDisponibleError,
    EstadoReservaInvalidoError,
    EstadoSolicitudInvalidoError,
    FechaLimiteRetiroInvalidaError,
    FechaPrestamoInvalidaError,
    PrestamoYaCreadoError,
    PrestamoYaDevueltoError,
    ReservaSinEjemplarError,
    ReservaVigenteDuplicadaError,
    SocioInhabilitadoError,
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
        raise SocioInhabilitadoError(
            f"El socio '{socio.numero_socio}' está inhabilitado."
        )

#Transaccion para crear una solicitud local
@transaction.atomic
def crear_solicitud_local(
    *,
    socio: Socio,
    libro,
    sede_origen,
    sede_destino,
) -> SolicitudPrestamo:
    validar_socio_habilitado(socio=socio)
    validar_sede_activa(sede=sede_origen)
    validar_sede_activa(sede=sede_destino)

    estrategia = obtener_estrategia(TipoSolicitud.LOCAL)
    estrategia.validar_creacion(
        sede_origen=sede_origen,
        sede_destino=sede_destino,
    )

    return SolicitudPrestamo.objects.create(
        socio=socio,
        libro=libro,
        sede_origen=sede_origen,
        sede_destino=sede_destino,
        tipo=TipoSolicitud.LOCAL,
        estado=EstadoSolicitud.PENDIENTE,
    )

#Funcion para asginar un ejemplar a la solicitud
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
        raise EstadoSolicitudInvalidoError(
            "Solo se puede asignar una solicitud pendiente."
        )

    validar_socio_habilitado(socio=solicitud.socio)
    validar_sede_activa(sede=solicitud.sede_origen)
    validar_sede_activa(sede=solicitud.sede_destino)

    if ejemplar.estado != EstadoEjemplar.DISPONIBLE:
        raise EjemplarNoDisponibleError(
            "El ejemplar seleccionado no está disponible."
        )

    if ejemplar.condicion_fisica != CondicionFisica.APTO:
        raise EjemplarNoAptoError(
            "El ejemplar no está apto para préstamo."
        )

    if ejemplar.libro_id != solicitud.libro_id:
        raise EjemplarNoCorrespondeError(
            "El ejemplar no corresponde al libro solicitado."
        )

    if ejemplar.sede_propietaria_id != solicitud.sede_origen_id:
        raise EjemplarEnOtraSedeError(
            "La sede propietaria del ejemplar no coincide con el origen."
        )

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

#Funcion para prepar la entraga del ejemplar a la solicitud
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
        raise EstadoSolicitudInvalidoError(
            "La solicitud todavía no tiene un ejemplar asignado."
        )

    ejemplar = Ejemplar.objects.select_for_update().get(
        pk=solicitud.ejemplar_id
    )

    estrategia = obtener_estrategia(solicitud.tipo)
    estrategia.preparar_entrega(
        solicitud=solicitud,
        ejemplar=ejemplar,
    )

    return solicitud

#Funcion para entregar y crear el prestamo 
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
        raise EstadoSolicitudInvalidoError(
            "La solicitud no está lista para entregar."
        )

    if solicitud.ejemplar_id is None:
        raise EstadoSolicitudInvalidoError(
            "La solicitud no tiene un ejemplar asignado."
        )

    ejemplar = Ejemplar.objects.select_for_update().get(
        pk=solicitud.ejemplar_id
    )

    if ejemplar.estado != EstadoEjemplar.LISTO_PARA_ENTREGA:
        raise EstadoSolicitudInvalidoError(
            "El ejemplar no está listo para entregar."
        )

    validar_socio_habilitado(socio=solicitud.socio)
    validar_sede_activa(sede=solicitud.sede_destino)

    if fecha_vencimiento <= fecha_entrega:
        raise FechaPrestamoInvalidaError(
            "El vencimiento debe ser posterior a la entrega."
        )

    if Prestamo.objects.filter(solicitud=solicitud).exists():
        raise PrestamoYaCreadoError(
            "La solicitud ya generó un préstamo."
        )

    prestamo = Prestamo.objects.create(
        solicitud=solicitud,
        fecha_entrega=fecha_entrega,
        fecha_vencimiento=fecha_vencimiento,
    )

    solicitud.estado = EstadoSolicitud.CUMPLIDA
    ejemplar.estado = EstadoEjemplar.PRESTADO

    solicitud.save(update_fields=["estado"])
    ejemplar.save(update_fields=["estado"])

    return prestamo

#Funcion para registrar devolucion del prestamo
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
        raise PrestamoYaDevueltoError(
            "El préstamo ya fue devuelto."
        )

    if fecha_devolucion < prestamo.fecha_entrega:
        raise FechaPrestamoInvalidaError(
            "La devolución no puede ser anterior a la entrega."
        )

    if condicion_devolucion not in CondicionFisica.values:
        raise FechaPrestamoInvalidaError(
            "La condición de devolución no es válida."
        )

    solicitud = prestamo.solicitud

    if solicitud.ejemplar_id is None:
        raise EstadoSolicitudInvalidoError(
            "El préstamo no tiene un ejemplar asociado."
        )

    ejemplar = Ejemplar.objects.select_for_update().get(
        pk=solicitud.ejemplar_id
    )

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

#Cancelar solicitud
@transaction.atomic
def cancelar_solicitud(
    *,
    solicitud: SolicitudPrestamo,
) -> SolicitudPrestamo:
    solicitud = SolicitudPrestamo.objects.select_for_update().get(
        pk=solicitud.pk
    )

    estados_cancelables = {
        EstadoSolicitud.PENDIENTE,
        EstadoSolicitud.ASIGNADA,
        EstadoSolicitud.LISTA_PARA_ENTREGA,
    }

    if solicitud.estado not in estados_cancelables:
        raise EstadoSolicitudInvalidoError(
            "La solicitud no puede cancelarse en su estado actual."
        )

    if solicitud.ejemplar_id is not None:
        ejemplar = Ejemplar.objects.select_for_update().get(
            pk=solicitud.ejemplar_id
        )
        ejemplar.estado = EstadoEjemplar.DISPONIBLE
        ejemplar.save(update_fields=["estado"])

    solicitud.estado = EstadoSolicitud.CANCELADA
    solicitud.save(update_fields=["estado"])

    return solicitud


# Servicios de reservas


def _reserva_con_bloqueo(reserva: Reserva) -> Reserva:
    return Reserva.objects.select_for_update(of=("self",)).get(pk=reserva.pk)


def _ejemplar_con_bloqueo(ejemplar_id: int) -> Ejemplar:
    return (
        Ejemplar.objects.select_for_update(of=("self",))
        .select_related("libro", "sede_propietaria", "sede_actual")
        .get(pk=ejemplar_id)
    )


def _cerrar_reserva(*, reserva: Reserva, estado_final: str) -> Reserva:
    """Efectos comunes de cancelar y expirar: liberar material y solicitudes."""
    ejemplar = reserva.ejemplar_asignado
    if ejemplar is not None:
        ejemplar = _ejemplar_con_bloqueo(ejemplar.pk)
        if ejemplar.estado == EstadoEjemplar.LISTO_PARA_ENTREGA:
            ejemplar.estado = EstadoEjemplar.DISPONIBLE
            ejemplar.save(update_fields=["estado"])

    for solicitud in SolicitudPrestamo.objects.filter(reserva=reserva):
        if solicitud.estado != EstadoSolicitud.CUMPLIDA:
            solicitud.estado = EstadoSolicitud.CANCELADA
            solicitud.save(update_fields=["estado"])

    reserva.estado = estado_final
    reserva.save(update_fields=["estado"])
    return reserva


@transaction.atomic
def crear_reserva(
    *,
    socio: Socio,
    libro,
    sede_retiro,
) -> Reserva:
    validar_sede_activa(sede=sede_retiro)

    vigente = Reserva.objects.filter(
        socio=socio,
        libro=libro,
        sede_retiro=sede_retiro,
        estado__in=(EstadoReserva.PENDIENTE, EstadoReserva.LISTA_PARA_RETIRO),
    ).exists()
    if vigente:
        raise ReservaVigenteDuplicadaError(
            "Ya existe una reserva vigente para ese socio, libro y sede."
        )

    return Reserva.objects.create(
        socio=socio,
        libro=libro,
        sede_retiro=sede_retiro,
        estado=EstadoReserva.PENDIENTE,
    )


@transaction.atomic
def asignar_reserva(
    *,
    reserva: Reserva,
    ejemplar: Ejemplar,
    fecha_limite_retiro,
) -> Reserva:
    """Deja el ejemplar listo para retiro y genera la solicitud local asociada."""
    reserva = _reserva_con_bloqueo(reserva)

    if reserva.estado != EstadoReserva.PENDIENTE:
        raise EstadoReservaInvalidoError("La reserva debe estar pendiente.")

    validar_socio_habilitado(socio=reserva.socio)
    validar_sede_activa(sede=reserva.sede_retiro)

    ejemplar = _ejemplar_con_bloqueo(ejemplar.pk)

    disponible = (
        ejemplar.estado == EstadoEjemplar.DISPONIBLE
        and ejemplar.condicion_fisica == CondicionFisica.APTO
        and ejemplar.sede_actual_id == ejemplar.sede_propietaria_id
    )
    if not disponible:
        raise EjemplarNoDisponibleError(
            "Elegí un ejemplar disponible en la sede de retiro."
        )
    if ejemplar.libro_id != reserva.libro_id:
        raise EjemplarNoCorrespondeError("El ejemplar no corresponde al libro reservado.")
    if ejemplar.sede_actual_id != reserva.sede_retiro_id:
        raise EjemplarEnOtraSedeError("El ejemplar no está en la sede de retiro.")

    if fecha_limite_retiro is None:
        raise FechaLimiteRetiroInvalidaError(
            "Ingresá explícitamente una fecha límite futura.",
            campo="fecha_limite_retiro",
        )
    if fecha_limite_retiro <= timezone.now():
        raise FechaLimiteRetiroInvalidaError(
            "Ingresá explícitamente una fecha límite futura.",
            campo="fecha_limite_retiro",
        )

    reservado_por_otra = Reserva.objects.filter(
        ejemplar_asignado=ejemplar,
        estado__in=(EstadoReserva.PENDIENTE, EstadoReserva.LISTA_PARA_RETIRO),
    ).exclude(pk=reserva.pk)
    if reservado_por_otra.exists():
        raise EjemplarNoDisponibleError(
            "El ejemplar ya está reservado para otro retiro vigente."
        )

    reserva.ejemplar_asignado_id = ejemplar.pk
    reserva.fecha_limite_retiro = fecha_limite_retiro
    reserva.estado = EstadoReserva.LISTA_PARA_RETIRO
    reserva.save(update_fields=["ejemplar_asignado", "fecha_limite_retiro", "estado"])

    ejemplar.estado = EstadoEjemplar.LISTO_PARA_ENTREGA
    ejemplar.save(update_fields=["estado"])

    SolicitudPrestamo.objects.create(
        socio=reserva.socio,
        libro=reserva.libro,
        ejemplar=ejemplar,
        sede_origen=ejemplar.sede_propietaria,
        sede_destino=reserva.sede_retiro,
        reserva=reserva,
        tipo=TipoSolicitud.LOCAL,
        estado=EstadoSolicitud.LISTA_PARA_ENTREGA,
    )

    return reserva


@transaction.atomic
def cancelar_reserva(*, reserva: Reserva) -> Reserva:
    reserva = _reserva_con_bloqueo(reserva)

    if reserva.estado not in (EstadoReserva.PENDIENTE, EstadoReserva.LISTA_PARA_RETIRO):
        raise EstadoReservaInvalidoError("La reserva ya está cerrada.")

    return _cerrar_reserva(reserva=reserva, estado_final=EstadoReserva.CANCELADA)


@transaction.atomic
def expirar_reserva(*, reserva: Reserva) -> Reserva:
    reserva = _reserva_con_bloqueo(reserva)

    if reserva.estado not in (EstadoReserva.PENDIENTE, EstadoReserva.LISTA_PARA_RETIRO):
        raise EstadoReservaInvalidoError("La reserva ya está cerrada.")

    vencio = (
        reserva.estado == EstadoReserva.LISTA_PARA_RETIRO
        and reserva.fecha_limite_retiro is not None
        and reserva.fecha_limite_retiro < timezone.now()
    )
    if not vencio:
        raise EstadoReservaInvalidoError("Todavía no venció el plazo de retiro.")

    return _cerrar_reserva(reserva=reserva, estado_final=EstadoReserva.EXPIRADA)
