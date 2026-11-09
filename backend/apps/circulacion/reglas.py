"""Reglas de negocio parametrizables de la circulación."""

from datetime import datetime, timedelta
from decimal import Decimal

from django.utils import timezone

#: Plazo sugerido para un préstamo nuevo.
PLAZO_PRESTAMO_DIAS = 14
#: Plazo máximo que admite el sistema entre entrega y vencimiento.
PLAZO_MAXIMO_DIAS = 60
#: Multa por cada día calendario de atraso en la devolución.
MULTA_DIARIA = Decimal("150.00")


def dias_atraso(*, fecha_vencimiento: datetime, fecha_devolucion: datetime | None, al=None) -> int:
    """Días calendario entre el vencimiento y la devolución (o la fecha de corte)."""
    fin = fecha_devolucion or al or timezone.now()
    if hasattr(fin, "hour"):
        fin = timezone.localdate(fin) if timezone.is_aware(fin) else fin.date()
    vencimiento = timezone.localdate(fecha_vencimiento)
    return max(0, (fin - vencimiento).days)


def multa(dias: int) -> Decimal:
    return MULTA_DIARIA * dias


def vencimiento_sugerido(fecha_entrega: datetime) -> datetime:
    return fecha_entrega + timedelta(days=PLAZO_PRESTAMO_DIAS)
