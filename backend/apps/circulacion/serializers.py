from django.utils import timezone
from rest_framework import serializers

from apps.catalogo.models import (
    CondicionFisica,
    Ejemplar,
    Libro,
)
from apps.sedes.models import Sede
from apps.socios.models import Socio

from .models import Prestamo, Reserva, SolicitudPrestamo, TipoSolicitud
from .strategies import obtener_estrategia


class SolicitudPrestamoSerializer(serializers.ModelSerializer):
    socio_id = serializers.IntegerField(read_only=True)
    libro_id = serializers.IntegerField(read_only=True)
    ejemplar_id = serializers.IntegerField(read_only=True, allow_null=True)
    sede_origen_id = serializers.IntegerField(read_only=True)
    sede_destino_id = serializers.IntegerField(read_only=True)
    reserva_id = serializers.IntegerField(read_only=True, allow_null=True)
    estrategia = serializers.SerializerMethodField(
        help_text="Clase Strategy que tramita la solicitud según su tipo."
    )
    estrategia_descripcion = serializers.SerializerMethodField()
    recorrido = serializers.SerializerMethodField()
    acciones = serializers.SerializerMethodField()
    remito_id = serializers.SerializerMethodField()

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
            "estrategia",
            "estrategia_descripcion",
            "recorrido",
            "acciones",
            "remito_id",
        ]
        read_only_fields = fields

    def get_estrategia(self, solicitud) -> str:
        return type(obtener_estrategia(solicitud.tipo)).__name__

    def get_estrategia_descripcion(self, solicitud) -> str:
        return obtener_estrategia(solicitud.tipo).descripcion_preparacion

    def get_recorrido(self, solicitud) -> list[str]:
        return list(obtener_estrategia(solicitud.tipo).recorrido)

    def _en_remito_vigente(self, solicitud) -> bool:
        valor = getattr(solicitud, "en_remito_vigente", None)
        if valor is None:
            valor = solicitud.detalles_remito.filter(
                remito__estado__in=("EN_PREPARACION", "EMPAQUETADO", "EN_TRANSITO")
            ).exists()
        return valor

    def get_acciones(self, solicitud) -> list[str]:
        from .services import acciones_solicitud

        if hasattr(solicitud, "remito_vigente_estado"):
            estado_remito = solicitud.remito_vigente_estado
        else:
            detalle = (
                solicitud.detalles_remito.filter(
                    remito__estado__in=("EN_PREPARACION", "EMPAQUETADO", "EN_TRANSITO")
                )
                .select_related("remito")
                .first()
            )
            estado_remito = detalle.remito.estado if detalle else None
        return acciones_solicitud(
            solicitud,
            en_remito_vigente=self._en_remito_vigente(solicitud),
            remito_estado=estado_remito,
        )

    def get_remito_id(self, solicitud) -> int | None:
        if hasattr(solicitud, "ultimo_remito_id"):
            return solicitud.ultimo_remito_id
        detalle = solicitud.detalles_remito.order_by("-id").first()
        return detalle.remito_id if detalle else None


class CrearSolicitudSerializer(serializers.Serializer):
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
    tipo = serializers.ChoiceField(choices=TipoSolicitud.choices)


# Alias temporal para no romper importaciones externas del primer incremento.
CrearSolicitudLocalSerializer = CrearSolicitudSerializer


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
    dias_atraso = serializers.SerializerMethodField()
    estado = serializers.SerializerMethodField(help_text="ACTIVO, VENCIDO o DEVUELTO.")
    multa = serializers.SerializerMethodField(help_text="Multa acumulada en pesos.")

    class Meta:
        model = Prestamo
        fields = [
            "id",
            "solicitud_id",
            "fecha_entrega",
            "fecha_vencimiento",
            "fecha_devolucion",
            "condicion_devolucion",
            "estado",
            "dias_atraso",
            "multa",
        ]
        read_only_fields = fields

    def get_estado(self, prestamo) -> str:
        if prestamo.fecha_devolucion is not None:
            return "DEVUELTO"
        return "VENCIDO" if prestamo.fecha_vencimiento < timezone.now() else "ACTIVO"

    def get_dias_atraso(self, prestamo) -> int:
        return prestamo.dias_atraso()

    def get_multa(self, prestamo) -> float:
        return float(prestamo.multa())


class DevolverPrestamoSerializer(serializers.Serializer):
    fecha_devolucion = serializers.DateTimeField()
    condicion_devolucion = serializers.ChoiceField(choices=CondicionFisica.choices)


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
