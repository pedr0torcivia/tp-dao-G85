from rest_framework import serializers

from apps.sedes.models import Sede

from .models import Ejemplar, Libro


class LibroSerializer(serializers.ModelSerializer):
    class Meta:
        model = Libro
        fields = [
            "id",
            "isbn",
            "titulo",
            "autor",
            "editorial",
            "edicion",
        ]
        read_only_fields = ["id"]

    def validate_isbn(self, value):
        if value is None:
            return None

        return value.strip() or None


class EjemplarSerializer(serializers.ModelSerializer):
    libro_id = serializers.PrimaryKeyRelatedField(
        source="libro",
        queryset=Libro.objects.all(),
    )
    sede_propietaria_id = serializers.PrimaryKeyRelatedField(
        source="sede_propietaria",
        queryset=Sede.objects.all(),
    )
    sede_actual_id = serializers.IntegerField(
        read_only=True,
    )

    class Meta:
        model = Ejemplar
        fields = [
            "id",
            "codigo_inventario",
            "libro_id",
            "sede_propietaria_id",
            "sede_actual_id",
            "estado",
            "condicion_fisica",
        ]
        read_only_fields = [
            "id",
            "sede_actual_id",
            "estado",
        ]