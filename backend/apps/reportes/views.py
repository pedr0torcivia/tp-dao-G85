from datetime import date

from django.utils.dateparse import parse_date
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from .selectors import obtener_prestamos_vencidos
from .services import demanda_interbibliotecaria, disponibilidad_catalogo, movimientos_entre_sedes


class PrestamosVencidosView(APIView):
    def get(self, request):
        crudo = request.GET.get("fecha_corte")
        if not crudo:
            raise ValidationError(
                {"fecha_corte": ["Debe indicar la fecha de corte en formato AAAA-MM-DD."]}
            )

        try:
            fecha_corte = date.fromisoformat(crudo)
        except ValueError as error:
            raise ValidationError(
                {"fecha_corte": ["El formato debe ser AAAA-MM-DD."]}
            ) from error

        sedes = obtener_prestamos_vencidos(fecha_corte=fecha_corte)

        return Response(
            {
                "fecha_corte": fecha_corte.isoformat(),
                "cantidad": sum(sede["cantidad"] for sede in sedes),
                "sedes": sedes,
            }
        )


def _fecha(request, clave: str) -> date:
    valor = parse_date(request.GET.get(clave, ""))
    if valor is None:
        raise ValidationError({clave: ["Ingresá una fecha con formato AAAA-MM-DD."]})
    return valor


@extend_schema(responses={200: OpenApiTypes.OBJECT}, summary="RP03 — movimiento entre sedes")
@api_view(["GET"])
def reportes_movimientos(request):
    desde = _fecha(request, "desde")
    hasta = _fecha(request, "hasta")

    if hasta < desde:
        raise ValidationError(
            {"hasta": ["El límite del rango no puede ser anterior al inicio."]}
        )

    sede_id = _sede_opcional(request)

    datos = movimientos_entre_sedes(desde=desde, hasta=hasta, sede_id=sede_id)
    datos["filtros"] = {"desde": desde.isoformat(), "hasta": hasta.isoformat(), "sede": sede_id}

    return Response(datos, status=status.HTTP_200_OK)


@extend_schema(
    responses={200: OpenApiTypes.OBJECT},
    summary="RP02 — demanda interbibliotecaria",
)
@api_view(["GET"])
def reportes_demanda(request):
    desde = _fecha(request, "desde")
    hasta = _fecha(request, "hasta")

    if hasta < desde:
        raise ValidationError(
            {"hasta": ["El límite del rango no puede ser anterior al inicio."]}
        )

    sede_id = _sede_opcional(request)

    datos = demanda_interbibliotecaria(desde=desde, hasta=hasta, sede_id=sede_id)
    datos["filtros"] = {"desde": desde.isoformat(), "hasta": hasta.isoformat(), "sede": sede_id}

    return Response(datos, status=status.HTTP_200_OK)


@extend_schema(
    responses={200: OpenApiTypes.OBJECT},
    summary="RP04 — disponibilidad de catálogo por sede",
)
@api_view(["GET"])
def reportes_disponibilidad(request):
    sede_id = _sede_opcional(request)

    datos = disponibilidad_catalogo(sede_id=sede_id)
    datos["filtros"] = {"sede": sede_id}

    return Response(datos, status=status.HTTP_200_OK)


def _sede_opcional(request) -> int | None:
    sede = request.GET.get("sede")
    if not sede:
        return None
    try:
        return int(sede)
    except ValueError as error:
        raise ValidationError({"sede": ["La sede es inválida."]}) from error
