from django.db import models
from django.db.models.functions import Lower


class EstadoSede(models.TextChoices):
    ACTIVA = "ACTIVA", "Activa"
    BAJA = "BAJA", "Dada de baja"


class Sede(models.Model):
    nombre = models.CharField(max_length=150)
    direccion = models.CharField(max_length=255)
    contacto = models.CharField(max_length=255)
    horarios = models.TextField()
    estado = models.CharField(
        max_length=10,
        choices=EstadoSede.choices,
        default=EstadoSede.ACTIVA,
    )

    class Meta:
        ordering = ["nombre"]
        constraints = [
            models.UniqueConstraint(
                Lower("nombre"),
                name="sede_nombre_unico_sin_mayusculas",
            )
        ]

    def __str__(self) -> str:
        return self.nombre
