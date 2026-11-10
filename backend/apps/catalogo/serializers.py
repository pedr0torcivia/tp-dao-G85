import re

from rest_framework import serializers

from apps.sedes.models import Sede

from .models import Ejemplar, Libro


class LibroSerializer(serializers.ModelSerializer):
    isbn = serializers.CharField(
        required=False,
        allow_null=True,
        allow_blank=True,
        max_length=20,
        help_text="13 números. Se admiten guiones o espacios, que se descartan.",
    )

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

        isbn = re.sub(r"[\s-]", "", value)
        if not isbn:
            return None
        if not re.fullmatch(r"\d{13}", isbn):
            raise serializers.ValidationError(
                "El ISBN debe tener exactamente 13 números, sin letras ni símbolos."
            )
        otros = Libro.objects.filter(isbn=isbn)
        if self.instance is not None:
            otros = otros.exclude(pk=self.instance.pk)
        if otros.exists():
            raise serializers.ValidationError("Ya existe un libro con ese ISBN.")
        return isbn


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
    tiene_foto = serializers.SerializerMethodField()

    def get_tiene_foto(self, ejemplar) -> bool:
        return bool(ejemplar.foto_tipo)

    class Meta:
        model = Ejemplar
        fields = [
            "id",
            "codigo_inventario",
            "fecha_alta",
            "libro_id",
            "sede_propietaria_id",
            "sede_actual_id",
            "estado",
            "condicion_fisica",
            "tiene_foto",
        ]
        read_only_fields = [
            "id",
            "sede_actual_id",
            "estado",
        ]


class EjemplarUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ejemplar
        fields = ["condicion_fisica"]
