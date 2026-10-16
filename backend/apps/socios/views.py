from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError as ApiValidationError
from rest_framework.response import Response

from .exceptions import (
    SocioDuplicadoError,
    SocioYaHabilitadoError,
    SocioYaInhabilitadoError,
)
from .models import EstadoSocio
from .selectors import buscar_socios
from .serializers import SocioSerializer
from .services import (
    actualizar_socio,
    crear_socio,
    habilitar_socio,
    inhabilitar_socio,
)


class SocioViewSet(viewsets.ModelViewSet):
    serializer_class = SocioSerializer
    http_method_names = ["get", "post", "put", "patch", "head", "options"]

    def get_queryset(self):
        estado = self.request.query_params.get("estado")
        busqueda = self.request.query_params.get("search")

        if estado:
            estado = estado.upper()
            if estado not in EstadoSocio.values:
                raise ApiValidationError(
                    {"estado": ["El estado debe ser HABILITADO o INHABILITADO."]}
                )

        return buscar_socios(busqueda=busqueda, estado=estado)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            socio = crear_socio(**serializer.validated_data)
        except SocioDuplicadoError as error:
            raise ApiValidationError({"detalle": [str(error)]}) from error

        return Response(
            self.get_serializer(socio).data,
            status=status.HTTP_201_CREATED,
        )

    def update(self, request, *args, **kwargs):
        parcial = kwargs.pop("partial", False)
        socio = self.get_object()
        serializer = self.get_serializer(
            socio,
            data=request.data,
            partial=parcial,
        )
        serializer.is_valid(raise_exception=True)

        try:
            socio = actualizar_socio(
                socio=socio,
                **serializer.validated_data,
            )
        except SocioDuplicadoError as error:
            raise ApiValidationError({"detalle": [str(error)]}) from error

        return Response(self.get_serializer(socio).data)

    @action(detail=True, methods=["post"])
    def habilitar(self, request, pk=None):
        try:
            socio = habilitar_socio(socio=self.get_object())
        except SocioYaHabilitadoError as error:
            raise ApiValidationError({"estado": [str(error)]}) from error

        return Response(self.get_serializer(socio).data)

    @action(detail=True, methods=["post"])
    def inhabilitar(self, request, pk=None):
        try:
            socio = inhabilitar_socio(socio=self.get_object())
        except SocioYaInhabilitadoError as error:
            raise ApiValidationError({"estado": [str(error)]}) from error

        return Response(self.get_serializer(socio).data)