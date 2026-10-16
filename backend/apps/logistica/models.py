from django.db import models
from django.db.models import F, Q
from django.utils import timezone


class EstadoRemito(models.TextChoices):
    EN_PREPARACION = "EN_PREPARACION", "En preparación"
    EMPAQUETADO = "EMPAQUETADO", "Empaquetado"
    DESPACHADO = "DESPACHADO", "Despachado"
    EN_TRANSITO = "EN_TRANSITO", "En tránsito"
    RECIBIDO = "RECIBIDO", "Recibido"
    CANCELADO = "CANCELADO", "Cancelado"


class Remito(models.Model):
    numero = models.CharField(max_length=40, unique=True)
    sede_origen = models.ForeignKey(
        "sedes.Sede", on_delete=models.PROTECT, related_name="remitos_enviados"
    )
    sede_destino = models.ForeignKey(
        "sedes.Sede", on_delete=models.PROTECT, related_name="remitos_recibidos"
    )
    estado = models.CharField(
        max_length=20,
        choices=EstadoRemito.choices,
        default=EstadoRemito.EN_PREPARACION,
    )
    fecha_creacion = models.DateTimeField(default=timezone.now)
    fecha_despacho = models.DateTimeField(null=True, blank=True)
    fecha_recepcion = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=~Q(sede_origen=F("sede_destino")),
                name="remito_sedes_diferentes",
            ),
            models.CheckConstraint(
                condition=Q(fecha_recepcion__isnull=True)
                | Q(fecha_despacho__isnull=False, fecha_recepcion__gte=F("fecha_despacho")),
                name="remito_recepcion_no_anterior_despacho",
            ),
        ]


class DetalleRemito(models.Model):
    remito = models.ForeignKey(Remito, on_delete=models.PROTECT, related_name="detalles")
    ejemplar = models.ForeignKey(
        "catalogo.Ejemplar", on_delete=models.PROTECT, related_name="detalles_remito"
    )
    solicitud = models.ForeignKey(
        "circulacion.SolicitudPrestamo",
        on_delete=models.PROTECT,
        related_name="detalles_remito",
        null=True,
        blank=True,
    )
    condicion_salida = models.CharField(max_length=80)
    condicion_recepcion = models.CharField(max_length=80, null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["remito", "ejemplar"], name="detalle_remito_ejemplar_unico"
            )
        ]


class EventoRemito(models.Model):
    remito = models.ForeignKey(Remito, on_delete=models.PROTECT, related_name="eventos")
    fecha_hora = models.DateTimeField(default=timezone.now)
    estado_anterior = models.CharField(max_length=20, null=True, blank=True)
    estado_nuevo = models.CharField(max_length=20, choices=EstadoRemito.choices)
    responsable = models.CharField(max_length=150)
    observacion = models.TextField(blank=True)

    class Meta:
        ordering = ["fecha_hora", "id"]
