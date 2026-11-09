from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError as ApiValidationError
from rest_framework.response import Response

from apps.sedes.exceptions import SedeInactivaError

from .exceptions import LogisticaError
from .models import DetalleRemito, EstadoRemito, EventoRemito, Remito
from .serializers import (
    DetalleRemitoSerializer,
    EventoRemitoSerializer,
    PrepararRetornoSerializer,
    RemitoAccionSerializer,
    RemitoAsignarSerializer,
    RemitoRecibirSerializer,
    RemitoSerializer,
)
from .services import (
    agregar_ejemplar,
    cancelar_remito,
    crear_remito,
    despachar_remito,
    empaquetar_remito,
    preparar_retorno,
    quitar_ejemplar,
    reabrir_remito,
    recibir_remito,
)

ERRORES_CON_CAMPO = {
    "NumeroRemitoDuplicadoError": "numero",
    "SedesInvalidasError": "sede_destino_id",
    "EjemplarInvalidoError": "ejemplar_id",
}


def _mapear_error_dominio(error: LogisticaError) -> ApiValidationError:
    """Traduce un error de dominio al formato de errores de la API."""
    campo = ERRORES_CON_CAMPO.get(type(error).__name__)

    if campo:
        raise ApiValidationError({campo: [str(error)]}) from error
    raise ApiValidationError({"detail": str(error)}) from error


def _ejecutar_comando(remito: Remito, operacion, **argumentos) -> Remito:
    """Corre la operación de dominio y traduce sus errores al formato de la API."""
    try:
        return operacion(remito=remito, **argumentos)
    except LogisticaError as error:
        _mapear_error_dominio(error)
    except SedeInactivaError as error:
        raise ApiValidationError({"detail": "La sede debe estar activa."}) from error


@extend_schema_view(
    asignar=extend_schema(request=RemitoAsignarSerializer, responses=RemitoSerializer),
    empaquetar=extend_schema(request=RemitoAccionSerializer, responses=RemitoSerializer),
    despachar=extend_schema(request=RemitoAccionSerializer, responses=RemitoSerializer),
    reabrir=extend_schema(request=RemitoAccionSerializer, responses=RemitoSerializer),
    quitar=extend_schema(request=RemitoAsignarSerializer, responses=RemitoSerializer),
    preparar_retorno=extend_schema(request=PrepararRetornoSerializer, responses=RemitoSerializer),
    recibir=extend_schema(request=RemitoRecibirSerializer, responses=RemitoSerializer),
    cancelar=extend_schema(request=RemitoAccionSerializer, responses=RemitoSerializer),
)
class RemitoViewSet(viewsets.ModelViewSet):
    queryset = Remito.objects.all().order_by("id")
    serializer_class = RemitoSerializer
    http_method_names = ["get", "post", "put", "patch", "head", "options"]

    def get_queryset(self):
        queryset = super().get_queryset()
        estado = self.request.query_params.get("estado")

        if estado:
            if estado.upper() not in EstadoRemito.values:
                raise ApiValidationError({"estado": ["Estado de remito desconocido."]})
            queryset = queryset.filter(estado=estado.upper())

        return queryset

    def perform_create(self, serializer):
        try:
            remito = crear_remito(
                numero=serializer.validated_data.get("numero", ""),
                sede_origen_id=serializer.validated_data["sede_origen"].id,
                sede_destino_id=serializer.validated_data["sede_destino"].id,
            )
        except LogisticaError as error:
            _mapear_error_dominio(error)
        except SedeInactivaError as error:
            raise ApiValidationError({"detail": "La sede debe estar activa."}) from error

        serializer.instance = remito

    def perform_update(self, serializer):
        remito = serializer.instance

        if remito.estado != EstadoRemito.EN_PREPARACION:
            raise ApiValidationError("Sólo se edita un remito en preparación.")

        if remito.detalles.exists():
            raise ApiValidationError("No se edita un remito con ejemplares asignados.")

        serializer.save()

    @action(detail=True, methods=["post"])
    def asignar(self, request, pk=None):
        remito = self.get_object()

        try:
            ejemplar_id = int(request.data.get("ejemplar_id"))
        except (TypeError, ValueError) as error:
            raise ApiValidationError({"ejemplar_id": ["Elegí un ejemplar válido."]}) from error

        detalle = _ejecutar_comando(remito, agregar_ejemplar, ejemplar_id=ejemplar_id)

        return Response(DetalleRemitoSerializer(detalle).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"])
    def empaquetar(self, request, pk=None):
        remito = self.get_object()

        remito = _ejecutar_comando(
            remito,
            empaquetar_remito,
            responsable=request.data.get("responsable", ""),
            observacion=request.data.get("observacion", ""),
        )

        return Response(self.get_serializer(remito).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"])
    def reabrir(self, request, pk=None):
        remito = _ejecutar_comando(
            self.get_object(),
            reabrir_remito,
            responsable=request.data.get("responsable", ""),
            observacion=request.data.get("observacion", ""),
        )
        return Response(RemitoSerializer(remito).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"])
    def quitar(self, request, pk=None):
        try:
            ejemplar_id = int(request.data.get("ejemplar_id"))
        except (TypeError, ValueError) as error:
            raise ApiValidationError({"ejemplar_id": ["Elegí un ejemplar válido."]}) from error
        remito = _ejecutar_comando(self.get_object(), quitar_ejemplar, ejemplar_id=ejemplar_id)
        return Response(RemitoSerializer(remito).data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"], url_path="preparar-retorno")
    def preparar_retorno(self, request):
        serializer = PrepararRetornoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            remito = preparar_retorno(**serializer.validated_data)
        except LogisticaError as error:
            _mapear_error_dominio(error)
        except SedeInactivaError as error:
            raise ApiValidationError({"detail": "La sede debe estar activa."}) from error
        return Response(RemitoSerializer(remito).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"])
    def despachar(self, request, pk=None):
        remito = self.get_object()

        remito = _ejecutar_comando(
            remito,
            despachar_remito,
            responsable=request.data.get("responsable", ""),
            observacion=request.data.get("observacion", ""),
        )

        return Response(self.get_serializer(remito).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"])
    def recibir(self, request, pk=None):
        serializer = RemitoRecibirSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        datos = serializer.validated_data
        try:
            resultados = {int(k): v for k, v in datos["resultados"].items()}
        except (TypeError, ValueError) as error:
            raise ApiValidationError("Los ejemplares verificados no son válidos.") from error
        remito = _ejecutar_comando(
            self.get_object(),
            recibir_remito,
            verificados=datos["verificados"],
            resultados=resultados,
            responsable=datos["responsable"],
            observacion=datos.get("observacion", ""),
        )
        return Response(RemitoSerializer(remito).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"])
    def cancelar(self, request, pk=None):
        remito = self.get_object()

        remito = _ejecutar_comando(
            remito,
            cancelar_remito,
            responsable=request.data.get("responsable", ""),
            observacion=request.data.get("observacion", ""),
        )

        return Response(self.get_serializer(remito).data, status=status.HTTP_200_OK)


class DetalleRemitoViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = DetalleRemito.objects.all()
    serializer_class = DetalleRemitoSerializer

    def get_queryset(self):
        queryset = DetalleRemito.objects.select_related("remito", "ejemplar", "solicitud")
        remito_id = self.request.query_params.get("remito_id")

        if remito_id:
            try:
                queryset = queryset.filter(remito_id=int(remito_id))
            except ValueError as error:
                raise ApiValidationError({"remito_id": ["El remito es inválido."]}) from error

        return queryset


class EventoRemitoViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = EventoRemito.objects.all()
    serializer_class = EventoRemitoSerializer

    def get_queryset(self):
        queryset = EventoRemito.objects.select_related("remito")
        remito_id = self.request.query_params.get("remito_id")

        if remito_id:
            try:
                queryset = queryset.filter(remito_id=int(remito_id))
            except ValueError as error:
                raise ApiValidationError({"remito_id": ["El remito es inválido."]}) from error

        return queryset
