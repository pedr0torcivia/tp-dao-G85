from datetime import date

from django.utils.dateparse import parse_date
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from .selectors import obtener_prestamos_vencidos
from .services import (
    demanda_interbibliotecaria,
    disponibilidad_catalogo,
    movimientos_entre_sedes,
    operaciones_abmc,
)

FILTRO_SEDE = OpenApiParameter(
    "sede", OpenApiTypes.INT, description="ID de sede; vacío incluye todas"
)
FILTROS_PERIODO = [
    OpenApiParameter("desde", OpenApiTypes.DATE, required=True),
    OpenApiParameter("hasta", OpenApiTypes.DATE, required=True),
    FILTRO_SEDE,
]


class PrestamosVencidosView(APIView):
    @extend_schema(responses={200: OpenApiTypes.OBJECT}, parameters=FILTROS_PERIODO)
    def get(self, request):
        desde, hasta = _periodo(request)
        sede = _sede_opcional(request)
        sedes = obtener_prestamos_vencidos(fecha_corte=hasta, desde=desde, sede_id=sede)
        return Response(
            {
                "fecha_corte": hasta.isoformat(),
                "filtros": {"desde": desde.isoformat(), "hasta": hasta.isoformat(), "sede": sede},
                "cantidad": sum(sede["cantidad"] for sede in sedes),
                "sedes": sedes,
            }
        )


def _fecha(request, clave: str) -> date:
    try:
        valor = parse_date(request.GET.get(clave, ""))
    except ValueError:
        valor = None
    if valor is None:
        raise ValidationError({clave: ["Ingresá una fecha con formato AAAA-MM-DD."]})
    return valor


@extend_schema(
    responses={200: OpenApiTypes.OBJECT},
    summary="RP03 — movimiento entre sedes",
    parameters=FILTROS_PERIODO,
)
@api_view(["GET"])
def reportes_movimientos(request):
    desde = _fecha(request, "desde")
    hasta = _fecha(request, "hasta")

    if hasta < desde:
        raise ValidationError({"hasta": ["El límite del rango no puede ser anterior al inicio."]})

    sede_id = _sede_opcional(request)

    datos = movimientos_entre_sedes(desde=desde, hasta=hasta, sede_id=sede_id)
    datos["filtros"] = {"desde": desde.isoformat(), "hasta": hasta.isoformat(), "sede": sede_id}

    return Response(datos, status=status.HTTP_200_OK)


@extend_schema(
    responses={200: OpenApiTypes.OBJECT},
    summary="RP02 — demanda interbibliotecaria",
    parameters=FILTROS_PERIODO,
)
@api_view(["GET"])
def reportes_demanda(request):
    desde = _fecha(request, "desde")
    hasta = _fecha(request, "hasta")

    if hasta < desde:
        raise ValidationError({"hasta": ["El límite del rango no puede ser anterior al inicio."]})

    sede_id = _sede_opcional(request)

    datos = demanda_interbibliotecaria(desde=desde, hasta=hasta, sede_id=sede_id)
    datos["filtros"] = {"desde": desde.isoformat(), "hasta": hasta.isoformat(), "sede": sede_id}

    return Response(datos, status=status.HTTP_200_OK)


@extend_schema(
    responses={200: OpenApiTypes.OBJECT},
    summary="RP04 — disponibilidad de catálogo por sede",
    parameters=FILTROS_PERIODO,
)
@api_view(["GET"])
def reportes_disponibilidad(request):
    sede_id = _sede_opcional(request)

    desde, hasta = _periodo(request)
    datos = disponibilidad_catalogo(sede_id=sede_id, desde=desde, hasta=hasta)
    datos["filtros"] = {"sede": sede_id, "desde": desde.isoformat(), "hasta": hasta.isoformat()}

    return Response(datos, status=status.HTTP_200_OK)


def _sede_opcional(request) -> int | None:
    sede = request.GET.get("sede")
    if not sede:
        return None
    try:
        return int(sede)
    except ValueError as error:
        raise ValidationError({"sede": ["La sede es inválida."]}) from error


def _periodo(request):
    desde, hasta = _fecha(request, "desde"), _fecha(request, "hasta")
    if hasta < desde:
        raise ValidationError({"hasta": ["El límite del rango no puede ser anterior al inicio."]})
    return desde, hasta


@extend_schema(
    responses={200: OpenApiTypes.OBJECT},
    summary="RP05 — comprobación de operaciones ABMC",
    parameters=FILTROS_PERIODO,
)
@api_view(["GET"])
def reportes_operaciones(request):
    desde, hasta = _periodo(request)
    sede = _sede_opcional(request)
    datos = operaciones_abmc(desde=desde, hasta=hasta, sede_id=sede)
    datos["filtros"] = {"desde": desde.isoformat(), "hasta": hasta.isoformat(), "sede": sede}
    return Response(datos)
