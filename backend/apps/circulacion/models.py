from django.db import models
from django.db.models import F, Q
from django.utils import timezone


class TipoSolicitud(models.TextChoices):
    LOCAL = "LOCAL", "Local"
    INTERBIBLIOTECARIA = "INTERBIBLIOTECARIA", "Interbibliotecaria"


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
    estado = models.CharField(max_length=30)


class SolicitudPrestamo(models.Model):
    socio = models.ForeignKey("socios.Socio", on_delete=models.PROTECT, related_name="solicitudes")
    libro = models.ForeignKey("catalogo.Libro", on_delete=models.PROTECT, related_name="solicitudes")
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
    estado = models.CharField(max_length=30)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=(
                    Q(tipo=TipoSolicitud.LOCAL, sede_origen=F("sede_destino"))
                    | (Q(tipo=TipoSolicitud.INTERBIBLIOTECARIA) & ~Q(sede_origen=F("sede_destino")))
                ),
                name="solicitud_tipo_sedes_coherentes",
            )
        ]


class Prestamo(models.Model):
    solicitud = models.OneToOneField(
        SolicitudPrestamo, on_delete=models.PROTECT, related_name="prestamo"
    )
    fecha_entrega = models.DateField()
    fecha_vencimiento = models.DateField()
    fecha_devolucion = models.DateField(null=True, blank=True)
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
        ]
