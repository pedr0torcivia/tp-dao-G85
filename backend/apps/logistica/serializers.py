from rest_framework import serializers

from apps.sedes.models import Sede

from .models import DetalleRemito, EventoRemito, Remito


class RemitoSerializer(serializers.ModelSerializer):
    sede_origen_id = serializers.PrimaryKeyRelatedField(
        source="sede_origen", queryset=Sede.objects.all()
    )
    sede_destino_id = serializers.PrimaryKeyRelatedField(
        source="sede_destino", queryset=Sede.objects.all()
    )

    class Meta:
        model = Remito
        fields = [
            "id",
            "numero",
            "sede_origen_id",
            "sede_destino_id",
            "estado",
            "fecha_creacion",
            "fecha_despacho",
            "fecha_recepcion",
        ]
        read_only_fields = ["id", "estado", "fecha_creacion", "fecha_despacho", "fecha_recepcion"]

    def validate_numero(self, value: str) -> str:
        numero = value.strip()

        if not numero:
            raise serializers.ValidationError("El número de remito es obligatorio.")

        otros = Remito.objects.all()
        if self.instance is not None:
            otros = otros.exclude(pk=self.instance.pk)

        if otros.filter(numero__iexact=numero).exists():
            raise serializers.ValidationError("Ya existe un remito con ese número.")

        return numero


class DetalleRemitoSerializer(serializers.ModelSerializer):
    class Meta:
        model = DetalleRemito
        fields = [
            "id",
            "remito_id",
            "ejemplar_id",
            "solicitud_id",
            "condicion_salida",
            "condicion_recepcion",
        ]
        read_only_fields = fields


class EventoRemitoSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventoRemito
        fields = [
            "id",
            "remito_id",
            "fecha_hora",
            "estado_anterior",
            "estado_nuevo",
            "responsable",
            "observacion",
        ]
        read_only_fields = fields
