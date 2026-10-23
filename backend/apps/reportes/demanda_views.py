from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from .demanda_selectors import demanda_interbibliotecaria
from .demanda_serializers import (
    DemandaInterbibliotecariaFiltrosSerializer,
    DemandaInterbibliotecariaRespuestaSerializer,
)


class DemandaInterbibliotecariaView(APIView):
    serializer_class = DemandaInterbibliotecariaRespuestaSerializer

    @extend_schema(
        parameters=[DemandaInterbibliotecariaFiltrosSerializer],
        responses=DemandaInterbibliotecariaRespuestaSerializer,
    )
    def get(self, request):
        serializer = DemandaInterbibliotecariaFiltrosSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        resultados = list(demanda_interbibliotecaria(**serializer.validated_data))
        return Response(
            {
                "criterio": (
                    "Solicitudes interbibliotecarias, excluyendo rechazadas "
                    "y canceladas. La sede corresponde al destino solicitante."
                ),
                "filtros": serializer.validated_data,
                "total_solicitudes": sum(item["cantidad"] for item in resultados),
                "resultados": resultados,
            }
        )
