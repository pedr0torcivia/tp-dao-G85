from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.utils import timezone


class Operacion(models.Model):
    fecha = models.DateTimeField(default=timezone.now, db_index=True)
    entidad = models.CharField(max_length=40)
    registro_id = models.PositiveBigIntegerField()
    accion = models.CharField(max_length=20)
    descripcion = models.TextField()
    usuario = models.CharField(max_length=150)
    sede_ids = models.JSONField(default=list)
    antes = models.JSONField(default=dict, encoder=DjangoJSONEncoder)
    despues = models.JSONField(default=dict, encoder=DjangoJSONEncoder)

    class Meta:
        ordering = ["fecha", "id"]

    def __str__(self):
        return f"{self.accion} · {self.entidad} #{self.registro_id}"
