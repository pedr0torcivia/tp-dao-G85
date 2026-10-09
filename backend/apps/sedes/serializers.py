from rest_framework import serializers

from .models import Sede


class SedeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sede
        fields = [
            "id",
            "nombre",
            "direccion",
            "contacto",
            "horarios",
            "estado",
        ]
        read_only_fields = ["id", "estado"]

    def validate_nombre(self, value: str) -> str:
        nombre = value.strip()

        if not nombre:
            raise serializers.ValidationError("El nombre de la sede es obligatorio.")

        sedes = Sede.objects.filter(nombre__iexact=nombre)

        if self.instance is not None:
            sedes = sedes.exclude(pk=self.instance.pk)

        if sedes.exists():
            raise serializers.ValidationError("Ya existe una sede con ese nombre.")

        return nombre
