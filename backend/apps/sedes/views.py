from django.db.models import Q
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError as ApiValidationError
from rest_framework.response import Response

from .exceptions import (
    NombreSedeDuplicadoError,
    SedeYaActivaError,
    SedeYaDadaDeBajaError,
)
from .models import EstadoSede, Sede
from .serializers import SedeSerializer
from .services import crear_sede, dar_de_baja_sede, reactivar_sede


class SedeViewSet(viewsets.ModelViewSet):
    queryset = Sede.objects.all()
    serializer_class = SedeSerializer
    http_method_names = ["get", "post", "put", "patch", "head", "options"]

    def get_queryset(self):
        queryset = super().get_queryset()
        estado = self.request.query_params.get("estado")
        busqueda = self.request.query_params.get("search")

        if estado:
            estado = estado.upper()
            if estado not in EstadoSede.values:
                raise ApiValidationError({"estado": ["El estado debe ser ACTIVA o BAJA."]})
            queryset = queryset.filter(estado=estado)

        if busqueda:
            queryset = queryset.filter(
                Q(nombre__icontains=busqueda)
                | Q(direccion__icontains=busqueda)
                | Q(contacto__icontains=busqueda)
            )

        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            sede = crear_sede(**serializer.validated_data)
        except NombreSedeDuplicadoError as error:
            raise ApiValidationError({"nombre": [str(error)]}) from error

        response_serializer = self.get_serializer(sede)

        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"], url_path="dar-de-baja")
    def dar_de_baja(self, request, pk=None):
        sede = self.get_object()

        try:
            sede = dar_de_baja_sede(sede=sede)
        except SedeYaDadaDeBajaError as error:
            raise ApiValidationError({"estado": [str(error)]}) from error

        return Response(
            self.get_serializer(sede).data,
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"])
    def reactivar(self, request, pk=None):
        sede = self.get_object()

        try:
            sede = reactivar_sede(sede=sede)
        except SedeYaActivaError as error:
            raise ApiValidationError({"estado": [str(error)]}) from error

        return Response(
            self.get_serializer(sede).data,
            status=status.HTTP_200_OK,
        )
