from rest_framework import serializers


class DemandaInterbibliotecariaFiltrosSerializer(serializers.Serializer):
    fecha_desde = serializers.DateField(required=False)
    fecha_hasta = serializers.DateField(required=False)
    sede_id = serializers.IntegerField(required=False, min_value=1)

    def validate(self, attrs):
        fecha_desde = attrs.get("fecha_desde")
        fecha_hasta = attrs.get("fecha_hasta")
        if fecha_desde and fecha_hasta and fecha_desde > fecha_hasta:
            raise serializers.ValidationError(
                "La fecha desde no puede ser posterior a la fecha hasta."
            )
        return attrs


class DemandaInterbibliotecariaItemSerializer(serializers.Serializer):
    libro_id = serializers.IntegerField()
    titulo = serializers.CharField()
    cantidad = serializers.IntegerField()


class DemandaInterbibliotecariaRespuestaSerializer(serializers.Serializer):
    criterio = serializers.CharField()
    filtros = serializers.DictField()
    total_solicitudes = serializers.IntegerField()
    resultados = DemandaInterbibliotecariaItemSerializer(many=True)
