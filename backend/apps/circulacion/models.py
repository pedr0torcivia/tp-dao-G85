from django.db import models
from django.db.models import F, Q
from django.utils import timezone


class TipoSolicitud(models.TextChoices):
    LOCAL = "LOCAL", "Local"
    INTERBIBLIOTECARIO = "INTERBIBLIOTECARIO", "Interbibliotecario"


class EstadoSolicitud(models.TextChoices):
    PENDIENTE = "PENDIENTE", "Pendiente"
    RECHAZADA = "RECHAZADA", "Rechazada"
    ASIGNADA = "ASIGNADA", "Asignada"
    EN_TRASLADO = "EN_TRASLADO", "En traslado"
    LISTA_PARA_ENTREGA = "LISTA_PARA_ENTREGA", "Lista para entrega"
    CUMPLIDA = "CUMPLIDA", "Cumplida"
    CANCELADA = "CANCELADA", "Cancelada"


class EstadoReserva(models.TextChoices):
    PENDIENTE = "PENDIENTE", "Pendiente"
    LISTA_PARA_RETIRO = "LISTA_PARA_RETIRO", "Lista para retiro"
    CUMPLIDA = "CUMPLIDA", "Cumplida"
    CANCELADA = "CANCELADA", "Cancelada"
    EXPIRADA = "EXPIRADA", "Expirada"


class Reserva(models.Model):
    socio = models.ForeignKey("socios.Socio", on_delete=models.PROTECT, related_name="reservas")
    libro = models.ForeignKey("catalogo.Libro", on_delete=models.PROTECT, related_name="reservas")
    sede_retiro = models.ForeignKey(
        "sedes.Sede", on_delete=models.PROTECT, related_name="reservas_para_retiro"
    )
    ejemplar_asignado = models.ForeignKey(
        "catalogo.Ejemplar",
        on_delete=models.PROTECT,
        related_name="reservas_asignadas",
        null=True,
        blank=True,
    )
    fecha_reserva = models.DateTimeField(default=timezone.now)
    fecha_limite_retiro = models.DateTimeField(null=True, blank=True)
    estado = models.CharField(
        max_length=30,
        choices=EstadoReserva.choices,
        default=EstadoReserva.PENDIENTE,
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(estado__in=EstadoReserva.values),
                name="reserva_estado_valido",
            ),
            models.CheckConstraint(
                condition=Q(fecha_limite_retiro__isnull=True)
                | Q(fecha_limite_retiro__gt=F("fecha_reserva")),
                name="reserva_limite_posterior_a_reserva",
            ),
            models.UniqueConstraint(
                fields=["socio", "libro", "sede_retiro"],
                condition=Q(estado__in=(EstadoReserva.PENDIENTE, EstadoReserva.LISTA_PARA_RETIRO)),
                name="reserva_vigente_unica_por_socio_libro_sede",
            ),
            models.UniqueConstraint(
                fields=["ejemplar_asignado"],
                condition=Q(
                    ejemplar_asignado__isnull=False,
                    estado__in=(EstadoReserva.PENDIENTE, EstadoReserva.LISTA_PARA_RETIRO),
                ),
                name="reserva_ejemplar_asignado_unico_vigente",
            ),
        ]

    def __str__(self) -> str:
        return f"Reserva {self.id} · {self.socio} · {self.libro}"


class SolicitudPrestamo(models.Model):
    socio = models.ForeignKey("socios.Socio", on_delete=models.PROTECT, related_name="solicitudes")
    libro = models.ForeignKey(
        "catalogo.Libro", on_delete=models.PROTECT, related_name="solicitudes"
    )
    ejemplar = models.ForeignKey(
        "catalogo.Ejemplar",
        on_delete=models.PROTECT,
        related_name="solicitudes",
        null=True,
        blank=True,
    )
    sede_origen = models.ForeignKey(
        "sedes.Sede", on_delete=models.PROTECT, related_name="solicitudes_como_origen"
    )
    sede_destino = models.ForeignKey(
        "sedes.Sede", on_delete=models.PROTECT, related_name="solicitudes_como_destino"
    )
    reserva = models.OneToOneField(
        Reserva,
        on_delete=models.PROTECT,
        related_name="solicitud",
        null=True,
        blank=True,
    )
    fecha_solicitud = models.DateTimeField(default=timezone.now)
    tipo = models.CharField(max_length=20, choices=TipoSolicitud.choices)
    estado = models.CharField(
        max_length=30,
        choices=EstadoSolicitud.choices,
        default=EstadoSolicitud.PENDIENTE,
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(estado__in=EstadoSolicitud.values),
                name="solicitud_estado_valido",
            ),
            models.CheckConstraint(
                condition=(
                    Q(tipo=TipoSolicitud.LOCAL, sede_origen=F("sede_destino"))
                    | (Q(tipo=TipoSolicitud.INTERBIBLIOTECARIO) & ~Q(sede_origen=F("sede_destino")))
                ),
                name="solicitud_tipo_sedes_coherentes",
            ),
        ]

    def __str__(self) -> str:
        return f"Solicitud {self.id} · {self.tipo}"


class Prestamo(models.Model):
    solicitud = models.OneToOneField(
        SolicitudPrestamo, on_delete=models.PROTECT, related_name="prestamo"
    )
    fecha_entrega = models.DateTimeField()
    fecha_vencimiento = models.DateTimeField()
    fecha_devolucion = models.DateTimeField(null=True, blank=True)
    condicion_devolucion = models.CharField(max_length=80, null=True, blank=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(fecha_vencimiento__gt=F("fecha_entrega")),
                name="prestamo_vencimiento_posterior_entrega",
            ),
            models.CheckConstraint(
                condition=Q(fecha_devolucion__isnull=True)
                | Q(fecha_devolucion__gte=F("fecha_entrega")),
                name="prestamo_devolucion_no_anterior_entrega",
            ),
            models.CheckConstraint(
                condition=Q(fecha_devolucion__isnull=True, condicion_devolucion__isnull=True)
                | Q(
                    fecha_devolucion__isnull=False,
                    condicion_devolucion__isnull=False,
                ),
                name="prestamo_devolucion_y_condicion_juntas",
            ),
        ]

    def __str__(self) -> str:
        return f"Préstamo {self.id} · solicitud {self.solicitud_id}"
