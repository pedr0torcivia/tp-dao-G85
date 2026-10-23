from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.circulacion.selectors import listar_reservas_vencidas
from apps.circulacion.services import expirar_reserva


class Command(BaseCommand):
    help = "Expira reservas cuyo plazo de retiro ya finalizó."

    def handle(self, *args, **options):
        fecha_actual = timezone.now()
        reservas = list(listar_reservas_vencidas(fecha_actual=fecha_actual))

        for reserva in reservas:
            expirar_reserva(reserva=reserva, fecha_actual=fecha_actual)

        self.stdout.write(self.style.SUCCESS(f"Reservas expiradas: {len(reservas)}"))
