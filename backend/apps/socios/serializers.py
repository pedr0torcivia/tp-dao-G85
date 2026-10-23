from rest_framework import serializers

from .models import Socio


class SocioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Socio
        fields = [
            "id",
            "numero_socio",
            "documento",
            "nombre",
            "contacto",
            "estado",
        ]
        read_only_fields = ["id", "estado"]

    def validate(self, attrs):
        campos = ["numero_socio", "documento", "nombre", "contacto"]

        for campo in campos:
            if campo not in attrs:
                continue

            valor = attrs[campo].strip()
            if not valor:
                raise serializers.ValidationError(
                    {campo: "Este campo no puede contener solo espacios."}
                )

            attrs[campo] = valor

        for campo in ["numero_socio", "documento"]:
            if campo not in attrs:
                continue

            socios = Socio.objects.filter(**{f"{campo}__iexact": attrs[campo]})
            if self.instance is not None:
                socios = socios.exclude(pk=self.instance.pk)

            if socios.exists():
                raise serializers.ValidationError(
                    {campo: f"Ya existe un socio con ese {campo.replace('_', ' ')}."}
                )

        return attrs