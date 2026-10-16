from rest_framework import serializers

from .models import Libro


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