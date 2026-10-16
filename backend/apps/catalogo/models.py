from django.db import models


class EstadoEjemplar(models.TextChoices):
    DISPONIBLE = "DISPONIBLE", "Disponible"
    ASIGNADO = "ASIGNADO", "Asignado"
    EN_TRANSITO = "EN_TRANSITO", "En tránsito"
    LISTO_PARA_ENTREGA = "LISTO_PARA_ENTREGA", "Listo para entrega"
    PRESTADO = "PRESTADO", "Prestado"
    EN_REVISION = "EN_REVISION", "En revisión"
    BAJA = "BAJA", "Dado de baja"


class Libro(models.Model):
    isbn = models.CharField(max_length=20, unique=True, null=True, blank=True)
    titulo = models.CharField(max_length=255)
    autor = models.CharField(max_length=255)
    editorial = models.CharField(max_length=255)
    edicion = models.CharField(max_length=100)

    def __str__(self) -> str:
        return self.titulo


class Ejemplar(models.Model):
    codigo_inventario = models.CharField(max_length=80, unique=True)
    libro = models.ForeignKey(Libro, on_delete=models.PROTECT, related_name="ejemplares")
    sede_propietaria = models.ForeignKey(
        "sedes.Sede", on_delete=models.PROTECT, related_name="ejemplares_propios"
    )
    sede_actual = models.ForeignKey(
        "sedes.Sede",
        on_delete=models.PROTECT,
        related_name="ejemplares_presentes",
        null=True,
        blank=True,
    )
    estado = models.CharField(
        max_length=20,
        choices=EstadoEjemplar.choices,
        default=EstadoEjemplar.DISPONIBLE,
    )
    condicion_fisica = models.CharField(max_length=80)

    def __str__(self) -> str:
        return self.codigo_inventario
