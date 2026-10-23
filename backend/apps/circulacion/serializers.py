from rest_framework import serializers

from apps.catalogo.models import (
    CondicionFisica,
    Ejemplar,
    Libro,
)
from apps.sedes.models import Sede
from apps.socios.models import Socio

from .models import Prestamo, Reserva, SolicitudPrestamo


class SolicitudPrestamoSerializer(serializers.ModelSerializer):
    socio_id = serializers.IntegerField(read_only=True)
    libro_id = serializers.IntegerField(read_only=True)
    ejemplar_id = serializers.IntegerField(read_only=True, allow_null=True)
    sede_origen_id = serializers.IntegerField(read_only=True)
    sede_destino_id = serializers.IntegerField(read_only=True)
    reserva_id = serializers.IntegerField(read_only=True, allow_null=True)

    class Meta:
        model = SolicitudPrestamo
        fields = [
            "id",
            "socio_id",
            "libro_id",
            "ejemplar_id",
            "sede_origen_id",
            "sede_destino_id",
            "reserva_id",
            "fecha_solicitud",
            "tipo",
            "estado",
        ]
        read_only_fields = fields


class CrearSolicitudLocalSerializer(serializers.Serializer):
    socio_id = serializers.PrimaryKeyRelatedField(
        source="socio",
        queryset=Socio.objects.all(),
    )
    libro_id = serializers.PrimaryKeyRelatedField(
        source="libro",
        queryset=Libro.objects.all(),
    )
    sede_origen_id = serializers.PrimaryKeyRelatedField(
        source="sede_origen",
        queryset=Sede.objects.all(),
    )
    sede_destino_id = serializers.PrimaryKeyRelatedField(
        source="sede_destino",
        queryset=Sede.objects.all(),
    )


class AsignarEjemplarSerializer(serializers.Serializer):
    ejemplar_id = serializers.PrimaryKeyRelatedField(
        source="ejemplar",
        queryset=Ejemplar.objects.all(),
    )


class EntregarSolicitudSerializer(serializers.Serializer):
    fecha_entrega = serializers.DateTimeField()
    fecha_vencimiento = serializers.DateTimeField()


class PrestamoSerializer(serializers.ModelSerializer):
    solicitud_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = Prestamo
        fields = [
            "id",
            "solicitud_id",
            "fecha_entrega",
            "fecha_vencimiento",
            "fecha_devolucion",
            "condicion_devolucion",
        ]
        read_only_fields = fields


class DevolverPrestamoSerializer(serializers.Serializer):
    fecha_devolucion = serializers.DateTimeField()
    condicion_devolucion = serializers.ChoiceField(
        choices=CondicionFisica.choices
    )


class AccionVaciaSerializer(serializers.Serializer):
    pass


class ReservaSerializer(serializers.ModelSerializer):
    socio_id = serializers.IntegerField(read_only=True)
    libro_id = serializers.IntegerField(read_only=True)
    sede_retiro_id = serializers.IntegerField(read_only=True)
    ejemplar_asignado_id = serializers.IntegerField(read_only=True, allow_null=True)

    class Meta:
        model = Reserva
        fields = [
            "id",
            "socio_id",
            "libro_id",
            "sede_retiro_id",
            "ejemplar_asignado_id",
            "fecha_reserva",
            "fecha_limite_retiro",
            "estado",
        ]
        read_only_fields = fields


class CrearReservaSerializer(serializers.Serializer):
    socio_id = serializers.PrimaryKeyRelatedField(
        source="socio",
        queryset=Socio.objects.all(),
    )
    libro_id = serializers.PrimaryKeyRelatedField(
        source="libro",
        queryset=Libro.objects.all(),
    )
    sede_retiro_id = serializers.PrimaryKeyRelatedField(
        source="sede_retiro",
        queryset=Sede.objects.all(),
    )


class AsignarReservaSerializer(serializers.Serializer):
    ejemplar_id = serializers.PrimaryKeyRelatedField(
        source="ejemplar",
        queryset=Ejemplar.objects.all(),
    )
    fecha_limite_retiro = serializers.DateTimeField()