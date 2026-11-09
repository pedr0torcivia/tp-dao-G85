from rest_framework import serializers

from apps.sedes.models import Sede

from .models import DetalleRemito, EventoRemito, Remito, ResultadoRecepcion


class RemitoAccionSerializer(serializers.Serializer):
    responsable = serializers.CharField(required=False, allow_blank=True)
    observacion = serializers.CharField(required=False, allow_blank=True)


class RemitoAsignarSerializer(serializers.Serializer):
    ejemplar_id = serializers.IntegerField(min_value=1)


class PrepararRetornoSerializer(serializers.Serializer):
    ejemplar_id = serializers.IntegerField(min_value=1)


class RemitoRecibirSerializer(RemitoAccionSerializer):
    responsable = serializers.CharField()
    verificados = serializers.ListField(
        child=serializers.IntegerField(min_value=1), required=False, default=list
    )
    resultados = serializers.DictField(
        child=serializers.ChoiceField(choices=ResultadoRecepcion.choices),
        required=False,
        default=dict,
        help_text="Mapa ejemplar_id → CONFORME | DANADO | EXTRAVIADO.",
    )


class RemitoSerializer(serializers.ModelSerializer):
    numero = serializers.CharField(required=False, allow_blank=True, max_length=40)
    sede_origen_id = serializers.PrimaryKeyRelatedField(
        source="sede_origen", queryset=Sede.objects.all()
    )
    sede_destino_id = serializers.PrimaryKeyRelatedField(
        source="sede_destino", queryset=Sede.objects.all()
    )
    estado_clase = serializers.SerializerMethodField(
        help_text="Clase State que gobierna el remito en su estado actual."
    )
    estado_descripcion = serializers.SerializerMethodField()
    acciones = serializers.SerializerMethodField(
        help_text="Operaciones que admite el estado actual (patrón State)."
    )

    class Meta:
        model = Remito
        fields = [
            "id",
            "numero",
            "sede_origen_id",
            "sede_destino_id",
            "estado",
            "estado_clase",
            "estado_descripcion",
            "acciones",
            "fecha_creacion",
            "fecha_despacho",
            "fecha_recepcion",
        ]
        read_only_fields = ["id", "estado", "fecha_creacion", "fecha_despacho", "fecha_recepcion"]

    def get_estado_clase(self, remito: Remito) -> str:
        return type(remito.comportamiento).__name__

    def get_estado_descripcion(self, remito: Remito) -> str:
        return remito.comportamiento.descripcion

    def get_acciones(self, remito: Remito) -> list[str]:
        return remito.comportamiento.operaciones_admitidas()

    def validate_numero(self, value: str) -> str:
        numero = value.strip()
        if not numero:
            return ""
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
            "resultado_recepcion",
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
