from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.functions import Lower
from django.utils import timezone


class CondicionFisica(models.TextChoices):
    APTO = "APTO", "Apto para préstamo"
    NO_APTO = "NO_APTO", "No apto para préstamo"


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

    class Meta:
        constraints = [
            models.UniqueConstraint(
                Lower("titulo"),
                Lower("autor"),
                Lower("editorial"),
                Lower("edicion"),
                condition=models.Q(isbn__isnull=True),
                name="libro_sin_isbn_edicion_unica",
            )
        ]

    def __str__(self) -> str:
        return self.titulo

    def clean(self):
        super().clean()
        if self.isbn:
            return
        campos = ("titulo", "autor", "editorial", "edicion")
        identidad = tuple(str(getattr(self, campo) or "").strip().casefold() for campo in campos)
        candidatos = (
            Libro.objects.filter(isbn__isnull=True).exclude(pk=self.pk).values_list(*campos)
        )
        if any(
            tuple(valor.strip().casefold() for valor in fila) == identidad for fila in candidatos
        ):
            raise ValidationError({"titulo": "Ya existe esa edición sin ISBN en el catálogo."})


class Ejemplar(models.Model):
    fecha_alta = models.DateTimeField(default=timezone.now, db_index=True, editable=False)
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
    condicion_fisica = models.CharField(
        max_length=80,
        choices=CondicionFisica.choices,
        default=CondicionFisica.APTO,
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(estado__in=EstadoEjemplar.values),
                name="ejemplar_estado_valido",
            ),
            models.CheckConstraint(
                condition=models.Q(condicion_fisica__in=CondicionFisica.values),
                name="ejemplar_condicion_valida",
            ),
        ]

    def __str__(self) -> str:
        return self.codigo_inventario
