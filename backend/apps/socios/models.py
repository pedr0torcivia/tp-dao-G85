from django.db import models


class EstadoSocio(models.TextChoices):
    HABILITADO = "HABILITADO", "Habilitado"
    INHABILITADO = "INHABILITADO", "Inhabilitado"


class Socio(models.Model):
    numero_socio = models.CharField(max_length=30, unique=True)
    documento = models.CharField(max_length=30, unique=True)
    nombre = models.CharField(max_length=150)
    contacto = models.CharField(max_length=255)
    estado = models.CharField(
        max_length=13,
        choices=EstadoSocio.choices,
        default=EstadoSocio.HABILITADO,
    )

    def __str__(self) -> str:
        return f"{self.numero_socio} - {self.nombre}"
