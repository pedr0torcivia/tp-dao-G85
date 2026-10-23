from datetime import datetime

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.logistica.models import EstadoRemito, Remito
from apps.sedes.models import Sede


def _momento(dia: int, hora: int = 12) -> datetime:
    return timezone.make_aware(datetime(2026, 10, dia, hora))


class BaseReportesTest(TestCase):
    def setUp(self):
        self.central = Sede.objects.create(
            nombre="Central",
            direccion="Av. 1",
            contacto="c@sede.test",
            horarios="Lunes a viernes de 8 a 18",
        )
        self.norte = Sede.objects.create(
            nombre="Norte",
            direccion="Av. 2",
            contacto="n@sede.test",
            horarios="Lunes a viernes de 8 a 18",
        )
        self.sur = Sede.objects.create(
            nombre="Sur",
            direccion="Av. 3",
            contacto="s@sede.test",
            horarios="Lunes a viernes de 8 a 18",
        )

    def crear_envio(
        self,
        numero: str,
        origen: Sede,
        destino: Sede,
        despacho: datetime | None = None,
        recepcion: datetime | None = None,
    ) -> Remito:
        if despacho is None:
            estado = EstadoRemito.EN_PREPARACION
        elif recepcion is None:
            estado = EstadoRemito.EN_TRANSITO
        else:
            estado = EstadoRemito.RECIBIDO
        return Remito.objects.create(
            numero=numero,
            sede_origen=origen,
            sede_destino=destino,
            estado=estado,
            fecha_despacho=despacho,
            fecha_recepcion=recepcion,
        )


class MovimientosTest(APITestCase, BaseReportesTest):
    """Fixture con resultado esperado calculado a mano (exigencia de la consigna)."""

    def preparar_fixture(self):
        # Central → Norte: 2 despachados, 2 recibidos; tránsitos de 2 y 1 día → promedio 1,50
        self.crear_envio("REM-001", self.central, self.norte, _momento(3), _momento(5))
        self.crear_envio("REM-002", self.central, self.norte, _momento(4), _momento(5))
        # Central → Sur: 1 despachado, sin recibir → sin promedio
        self.crear_envio("REM-003", self.central, self.sur, _momento(5), None)
        # Sur → Central: 1 despachado y recibido en 1 día → promedio 1,00
        self.crear_envio("REM-004", self.sur, self.central, _momento(2), _momento(3))
        # Despachado fuera del rango (fecha de despacho posterior al corte)
        self.crear_envio("REM-005", self.central, self.norte, _momento(20), _momento(20))
        # Creado y nunca despachado → no entra en el reporte
        self.crear_envio("REM-006", self.central, self.sur, None, None)

    def test_calcula_trayectos_con_valores_precalculados(self):
        self.preparar_fixture()

        response = self.client.get(
            reverse("reportes-movimientos"),
            {"desde": "2026-10-01", "hasta": "2026-10-09"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["reporte"], "RP03")
        self.assertEqual(response.data["resumen"], "4 envíos despachados")
        self.assertEqual(
            response.data["filas"],
            [
                {
                    "sede_origen_id": self.central.id,
                    "sede_destino_id": self.norte.id,
                    "despachados": 2,
                    "recibidos": 2,
                    "dias_transito_promedio": 1.5,
                },
                {
                    "sede_origen_id": self.central.id,
                    "sede_destino_id": self.sur.id,
                    "despachados": 1,
                    "recibidos": 0,
                    "dias_transito_promedio": None,
                },
                {
                    "sede_origen_id": self.sur.id,
                    "sede_destino_id": self.central.id,
                    "despachados": 1,
                    "recibidos": 1,
                    "dias_transito_promedio": 1.0,
                },
            ],
        )

    def test_filtra_por_sede_participante(self):
        self.preparar_fixture()

        response = self.client.get(
            reverse("reportes-movimientos"),
            {"desde": "2026-10-01", "hasta": "2026-10-09", "sede": self.sur.id},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["resumen"], "2 envíos despachados")
        # Sur coincide como destino (Central → Sur, sin recibir) y como origen (Sur → Central)
        trayectos = [(f["sede_origen_id"], f["sede_destino_id"]) for f in response.data["filas"]]
        esperados = [(self.central.id, self.sur.id), (self.sur.id, self.central.id)]
        self.assertEqual(trayectos, esperados)

    def test_maneja_resultados_vacios(self):
        response = self.client.get(
            reverse("reportes-movimientos"),
            {"desde": "2026-10-01", "hasta": "2026-10-09"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["filas"], [])
        self.assertEqual(response.data["resumen"], "0 envíos despachados")

    def test_rechaza_parametros_invalidos(self):
        sin_fechas = self.client.get(reverse("reportes-movimientos"))
        self.assertEqual(sin_fechas.status_code, status.HTTP_400_BAD_REQUEST)

        rango_invertido = self.client.get(
            reverse("reportes-movimientos"),
            {"desde": "2026-10-09", "hasta": "2026-10-01"},
        )
        self.assertEqual(rango_invertido.status_code, status.HTTP_400_BAD_REQUEST)

        sede_invalida = self.client.get(
            reverse("reportes-movimientos"),
            {"desde": "2026-10-01", "hasta": "2026-10-09", "sede": "no-soy-un-id"},
        )
        self.assertEqual(sede_invalida.status_code, status.HTTP_400_BAD_REQUEST)
