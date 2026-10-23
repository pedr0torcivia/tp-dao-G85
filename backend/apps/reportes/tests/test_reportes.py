from datetime import datetime

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.catalogo.models import CondicionFisica, Ejemplar, EstadoEjemplar, Libro
from apps.circulacion.models import SolicitudPrestamo
from apps.sedes.models import EstadoSede, Sede
from apps.socios.models import Socio

from apps.reportes.services import demanda_interbibliotecaria, disponibilidad_catalogo


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
        self.socio = Socio.objects.create(
            numero_socio="SOC-001",
            documento="30111222",
            nombre="Integrante Uno",
            contacto="socio@correo.test",
        )
        self.principito = Libro.objects.create(
            isbn="9780000000001",
            titulo="El principito",
            autor="Antoine de Saint-Exupéry",
            editorial="Salamandra",
            edicion="1",
        )
        self.quijote = Libro.objects.create(
            isbn="9780000000002",
            titulo="Don Quijote",
            autor="Miguel de Cervantes",
            editorial="Austral",
            edicion="2",
        )

    def crear_solicitud(
        self,
        libro,
        sede_origen,
        sede_destino,
        tipo="INTERBIBLIOTECARIO",
        estado="ASIGNADA",
        fecha=None,
    ):
        if fecha is None:
            fecha = timezone.now()
        if timezone.is_naive(fecha):
            fecha = timezone.make_aware(fecha)

        return SolicitudPrestamo.objects.create(
            socio=self.socio,
            libro=libro,
            sede_origen=sede_origen,
            sede_destino=sede_destino,
            tipo=tipo,
            estado=estado,
            fecha_solicitud=fecha,
        )

    def crear_ejemplar(self, libro, sede, estado="DISPONIBLE", condicion="APTO", sede_actual=None):
        self.contador = getattr(self, "contador", 0) + 1
        return Ejemplar.objects.create(
            codigo_inventario=f"EJ-{self.contador:04d}",
            libro=libro,
            sede_propietaria=sede,
            sede_actual=sede_actual or sede,
            estado=estado,
            condicion_fisica=condicion,
        )


class DemandaTest(APITestCase, BaseReportesTest):
    """Fixture con resultado esperado calculado a mano."""

    def preparar_fixture(self):
        # El principito ← Norte: 3 solicitudes válidas (origen es la propietaria)
        self.crear_solicitud(self.principito, self.central, self.norte, fecha=datetime(2026, 10, 1))
        self.crear_solicitud(self.principito, self.central, self.norte, fecha=datetime(2026, 10, 3))
        self.crear_solicitud(
            self.principito, self.central, self.norte, fecha=datetime(2026, 10, 5, 23, 59)
        )
        # Don Quijote ← Norte: 2 solicitudes válidas
        self.crear_solicitud(self.quijote, self.central, self.norte, fecha=datetime(2026, 10, 4))
        self.crear_solicitud(self.quijote, self.central, self.norte, fecha=datetime(2026, 10, 8))
        # Rechazadas y canceladas: NO cuentan (1 y 1)
        self.crear_solicitud(
            self.principito, self.central, self.norte,
            estado="RECHAZADA", fecha=datetime(2026, 10, 2),
        )
        self.crear_solicitud(
            self.quijote, self.central, self.norte,
            estado="CANCELADA", fecha=datetime(2026, 10, 6),
        )
        # Fuera del rango: no cuenta
        self.crear_solicitud(
            self.quijote, self.central, self.norte, fecha=datetime(2026, 9, 20)
        )
        # Local: no entra al reporte de demanda interbibliotecaria
        self.crear_solicitud(
            self.quijote, self.norte, self.norte,
            tipo="LOCAL", fecha=datetime(2026, 10, 7),
        )

    def test_ranking_con_valores_precalculados(self):
        self.preparar_fixture()

        datos = demanda_interbibliotecaria(
            desde=datetime(2026, 10, 1).date(),
            hasta=datetime(2026, 10, 8).date(),
        )

        self.assertEqual(datos["reporte"], "RP02")
        self.assertEqual(datos["resumen"], "5 solicitudes válidas")
        filas = datos["filas"]
        self.assertEqual(len(filas), 2)
        # 3 del principito, 2 del quijote; orden por cantidad descendente
        self.assertEqual(filas[0]["libro"], "El principito")
        self.assertEqual(filas[0]["cantidad"], 3)
        self.assertEqual(filas[1]["libro"], "Don Quijote")
        self.assertEqual(filas[1]["cantidad"], 2)

    def test_filtrar_por_sede_solicitante(self):
        self.preparar_fixture()
        self.crear_solicitud(self.quijote, self.central, self.norte, fecha=datetime(2026, 10, 4))

        datos = demanda_interbibliotecaria(
            desde=datetime(2026, 10, 1).date(),
            hasta=datetime(2026, 10, 8).date(),
            sede_id=self.norte.pk,
        )
        self.assertEqual(datos["resumen"], "6 solicitudes válidas")

        datos = demanda_interbibliotecaria(
            desde=datetime(2026, 10, 1).date(),
            hasta=datetime(2026, 10, 8).date(),
            sede_id=self.central.pk,
        )
        self.assertEqual(datos["resumen"], "0 solicitudes válidas")

    def test_rango_incluye_bordes_del_dia_y_resultado_vacio(self):
        self.crear_solicitud(
            self.principito, self.central, self.norte, fecha=datetime(2026, 10, 5)
        )

        datos = demanda_interbibliotecaria(
            desde=datetime(2026, 10, 5).date(),
            hasta=datetime(2026, 10, 5).date(),
        )
        self.assertEqual(datos["resumen"], "1 solicitudes válidas")

        datos = demanda_interbibliotecaria(
            desde=datetime(2026, 10, 6).date(),
            hasta=datetime(2026, 10, 6).date(),
        )
        self.assertEqual(datos["filas"], [])

    def test_endpoint_http(self):
        self.preparar_fixture()

        response = self.client.get(
            reverse("reportes-demanda-interbibliotecaria"),
            {"desde": "2026-10-01", "hasta": "2026-10-08"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["filas"][0]["cantidad"], 3)
        self.assertEqual(response.data["filtros"]["sede"], None)

    def test_endpoint_requiere_fechas_validas(self):
        response = self.client.get(reverse("reportes-demanda-interbibliotecaria"))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response = self.client.get(
            reverse("reportes-demanda-interbibliotecaria"),
            {"desde": "2026-10-10", "hasta": "2026-10-01"},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("hasta", response.data["error"]["detail"])


class DisponibilidadTest(APITestCase, BaseReportesTest):
    """Fixture con resultado esperado calculado a mano."""

    def preparar_fixture(self):
        # El principito @ Central: 3 ejemplares, 1 disponible
        self.crear_ejemplar(self.principito, self.central)  # DISPONIBLE + APTO + en su sede
        self.crear_ejemplar(
            self.principito, self.central,
            estado=EstadoEjemplar.PRESTADO,
            sede_actual=self.norte,
        )
        self.crear_ejemplar(
            self.principito, self.central,
            condicion=CondicionFisica.NO_APTO,
            estado=EstadoEjemplar.EN_REVISION,
        )
        # Don Quijote @ Central: 2 ejemplares, 0 disponibles (en tránsito y en otra sede)
        self.crear_ejemplar(
            self.quijote, self.central,
            estado=EstadoEjemplar.EN_TRANSITO,
            sede_actual=None,
        )
        self.crear_ejemplar(
            self.quijote, self.central,
            sede_actual=self.norte,
        )
        # Don Quijote @ Norte: 1 ejemplar disponible en sede activa
        self.crear_ejemplar(self.quijote, self.norte)

    def test_agrupacion_y_proporcion_precalculadas(self):
        self.preparar_fixture()

        datos = disponibilidad_catalogo()

        self.assertEqual(datos["reporte"], "RP04")
        self.assertEqual(datos["resumen"], "2 de 6 ejemplares disponibles")

        filas = datos["filas"]
        self.assertEqual(len(filas), 3)

        # Ordenado por (libro, sede): "Don Quijote" . Central, "Don Quijote" . Norte, "El principito" . Central
        quijote_central = filas[0]
        self.assertEqual(quijote_central["libro"], "Don Quijote")
        self.assertEqual(quijote_central["total"], 2)
        self.assertEqual(quijote_central["disponibles"], 0)
        # El ejemplar en la otra sede cuenta en el total, no como disponible
        self.assertEqual(quijote_central["por_estado"].get("DISPONIBLE"), 1)

        quijote_norte = filas[1]
        self.assertEqual(quijote_norte["disponibles"], 1)
        self.assertEqual(quijote_norte["proporcion_porcentaje"], 100)

        principito_central = filas[2]
        self.assertEqual(principito_central["libro"], "El principito")
        self.assertEqual(principito_central["total"], 3)
        self.assertEqual(principito_central["disponibles"], 1)
        self.assertEqual(principito_central["proporcion_porcentaje"], 33)
        self.assertEqual(principito_central["por_estado"].get("PRESTADO"), 1)

    def test_no_cuenta_disponibles_si_la_sede_esta_de_baja(self):
        self.preparar_fixture()
        Sede.objects.filter(pk=self.norte.pk).update(estado=EstadoSede.BAJA)

        datos = disponibilidad_catalogo()
        quijote_norte = datos["filas"][1]
        self.assertEqual(quijote_norte["total"], 1)
        self.assertEqual(quijote_norte["disponibles"], 0)
        self.assertEqual(datos["resumen"], "1 de 6 ejemplares disponibles")

    def test_filtro_por_sede_propietaria(self):
        self.preparar_fixture()

        datos = disponibilidad_catalogo(sede_id=self.norte.pk)
        self.assertEqual(datos["resumen"], "1 de 1 ejemplares disponibles")

        datos = disponibilidad_catalogo(sede_id=self.central.pk)
        self.assertEqual(datos["resumen"], "1 de 5 ejemplares disponibles")

    def test_ejemplar_en_ubicacion_correcta_pero_no_apto_no_cuenta(self):
        self.crear_ejemplar(
            self.principito, self.central,
            condicion=CondicionFisica.NO_APTO,
            estado=EstadoEjemplar.DISPONIBLE,
        )

        datos = disponibilidad_catalogo()
        self.assertEqual(datos["resumen"], "0 de 1 ejemplares disponibles")

    def test_endpoint_http(self):
        self.preparar_fixture()

        response = self.client.get(reverse("reportes-disponibilidad"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["filas"]), 3)

        response = self.client.get(
            reverse("reportes-disponibilidad"), {"sede": self.norte.pk}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["resumen"], "1 de 1 ejemplares disponibles")

        response = self.client.get(reverse("reportes-disponibilidad"), {"sede": "xyz"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
