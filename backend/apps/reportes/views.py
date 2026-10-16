from datetime import date

from django.utils.dateparse import parse_date
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.exceptions import ValidationError as ApiValidationError
from rest_framework.response import Response

from .services import movimientos_entre_sedes


def _fecha(request, clave: str) -> date:
    valor = parse_date(request.GET.get(clave, ""))
    if valor is None:
        raise ApiValidationError({clave: ["Ingresá una fecha con formato AAAA-MM-DD."]})
    return valor


@extend_schema(responses={200: OpenApiTypes.OBJECT}, summary="RP03 — movimiento entre sedes")
@api_view(["GET"])
def reportes_movimientos(request):
    desde = _fecha(request, "desde")
    hasta = _fecha(request, "hasta")

    if hasta < desde:
        raise ApiValidationError(
            {"hasta": ["El límite del rango no puede ser anterior al inicio."]}
        )

    sede = request.GET.get("sede")
    sede_id = None
    if sede:
        try:
            sede_id = int(sede)
        except ValueError as error:
            raise ApiValidationError({"sede": ["La sede es inválida."]}) from error

    datos = movimientos_entre_sedes(desde=desde, hasta=hasta, sede_id=sede_id)
    datos["filtros"] = {"desde": desde.isoformat(), "hasta": hasta.isoformat(), "sede": sede_id}

    return Response(datos, status=status.HTTP_200_OK)
