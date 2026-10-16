from datetime import date

from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from .selectors import obtener_prestamos_vencidos


class PrestamosVencidosView(APIView):
    def get(self, request):
        fecha_corte = date.fromisoformat(fecha_corte)
        
        if not fecha_corte:
            raise ValidationError(
                {"fecha_corte": ["Debe indicar la fecha de corte en formato AAAA-MM-DD."]}
            )

        try:
            fecha_corte = __import__("datetime").date.fromisoformat(fecha_corte)
        except ValueError as error:
            raise ValidationError(
                {"fecha_corte": ["El formato debe ser AAAA-MM-DD."]}
            ) from error

        sedes = obtener_prestamos_vencidos(fecha_corte=fecha_corte)

        return Response(
            {
                "fecha_corte": fecha_corte,
                "cantidad": sum(sede["cantidad"] for sede in sedes),
                "sedes": sedes,
            }
        )