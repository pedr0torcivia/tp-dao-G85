from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from apps.sedes.exceptions import SedeInactivaError

from .exceptions import ErrorCirculacion
from .models import Prestamo, Reserva, SolicitudPrestamo
from .selectors import listar_prestamos, listar_solicitudes, listar_reservas
from .serializers import (
    AccionVaciaSerializer,
    AsignarEjemplarSerializer,
    AsignarReservaSerializer,
    CrearReservaSerializer,
    CrearSolicitudLocalSerializer,
    DevolverPrestamoSerializer,
    EntregarSolicitudSerializer,
    PrestamoSerializer,
    ReservaSerializer,
    SolicitudPrestamoSerializer,
)
from .services import (
    asignar_ejemplar,
    asignar_reserva,
    cancelar_reserva,
    cancelar_solicitud,
    crear_reserva,
    crear_solicitud_local,
    entregar_solicitud,
    expirar_reserva,
    preparar_entrega,
    registrar_devolucion,
)


def ejecutar_operacion(operacion, **datos):
    try:
        return operacion(**datos)
    except (ErrorCirculacion, SedeInactivaError) as error:
        campo = getattr(error, "campo", None)
        if campo:
            raise ValidationError({campo: [str(error)]}) from error
        raise ValidationError(
            {"non_field_errors": [str(error)]}
        ) from error


class SolicitudPrestamoViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = listar_solicitudes()
    serializer_class = SolicitudPrestamoSerializer

    def get_serializer_class(self):
        serializers_por_accion = {
            "create": CrearSolicitudLocalSerializer,
            "asignar": AsignarEjemplarSerializer,
            "preparar_entrega": AccionVaciaSerializer,
            "entregar": EntregarSolicitudSerializer,
            "cancelar": AccionVaciaSerializer,
        }
        return serializers_por_accion.get(
            self.action,
            SolicitudPrestamoSerializer,
        )

    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        solicitud = ejecutar_operacion(
            crear_solicitud_local,
            **serializer.validated_data,
        )

        return Response(
            SolicitudPrestamoSerializer(solicitud).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"])
    def asignar(self, request, pk=None):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        solicitud = ejecutar_operacion(
            asignar_ejemplar,
            solicitud=self.get_object(),
            **serializer.validated_data,
        )

        return Response(
            SolicitudPrestamoSerializer(solicitud).data
        )

    @action(
        detail=True,
        methods=["post"],
        url_path="preparar-entrega",
    )
    def preparar_entrega(self, request, pk=None):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        solicitud = ejecutar_operacion(
            preparar_entrega,
            solicitud=self.get_object(),
        )

        return Response(
            SolicitudPrestamoSerializer(solicitud).data
        )

    @action(detail=True, methods=["post"])
    def entregar(self, request, pk=None):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        prestamo = ejecutar_operacion(
            entregar_solicitud,
            solicitud=self.get_object(),
            **serializer.validated_data,
        )

        return Response(
            PrestamoSerializer(prestamo).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"])
    def cancelar(self, request, pk=None):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        solicitud = ejecutar_operacion(
            cancelar_solicitud,
            solicitud=self.get_object(),
        )

        return Response(
            SolicitudPrestamoSerializer(solicitud).data
        )


class ReservaViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = listar_reservas()
    serializer_class = ReservaSerializer

    def get_serializer_class(self):
        serializers_por_accion = {
            "create": CrearReservaSerializer,
            "asignar": AsignarReservaSerializer,
            "cancelar": AccionVaciaSerializer,
            "expirar": AccionVaciaSerializer,
        }
        return serializers_por_accion.get(self.action, ReservaSerializer)

    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        reserva = ejecutar_operacion(
            crear_reserva,
            **serializer.validated_data,
        )

        return Response(
            ReservaSerializer(reserva).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"], url_path="asignar-reserva")
    def asignar(self, request, pk=None):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        reserva = ejecutar_operacion(
            asignar_reserva,
            reserva=self.get_object(),
            **serializer.validated_data,
        )

        return Response(ReservaSerializer(reserva).data)

    @action(detail=True, methods=["post"])
    def cancelar(self, request, pk=None):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        reserva = ejecutar_operacion(
            cancelar_reserva,
            reserva=self.get_object(),
        )

        return Response(ReservaSerializer(reserva).data)

    @action(detail=True, methods=["post"])
    def expirar(self, request, pk=None):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        reserva = ejecutar_operacion(
            expirar_reserva,
            reserva=self.get_object(),
        )

        return Response(ReservaSerializer(reserva).data)


class PrestamoViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = listar_prestamos()
    serializer_class = PrestamoSerializer

    def get_serializer_class(self):
        if self.action == "devolver":
            return DevolverPrestamoSerializer

        return PrestamoSerializer

    @action(detail=True, methods=["post"])
    def devolver(self, request, pk=None):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        prestamo = ejecutar_operacion(
            registrar_devolucion,
            prestamo=self.get_object(),
            **serializer.validated_data,
        )

        return Response(
            PrestamoSerializer(prestamo).data
        )