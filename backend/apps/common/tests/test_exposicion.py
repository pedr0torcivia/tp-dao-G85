from datetime import date, timedelta
from io import StringIO
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.utils import timezone
from rest_framework.test import APITestCase

from apps.catalogo.models import Ejemplar, Libro
from apps.common.models import Operacion
from apps.common.testing import autenticar_personal
from apps.reportes.selectors import obtener_prestamos_vencidos
from apps.reportes.services import disponibilidad_catalogo, operaciones_abmc
from apps.sedes.models import Sede


class ExposicionTest(APITestCase):
    def setUp(self):
        autenticar_personal(self.client)
        self.hoy = timezone.localdate()
        self.rango = {"desde": self.hoy.isoformat(), "hasta": self.hoy.isoformat()}

    def crear_sede(self):
        return self.client.post(
            "/api/sedes/",
            {
                "nombre": "Sede para ABMC",
                "direccion": "Calle 85",
                "contacto": "sede@example.test",
                "horarios": "8 a 18",
            },
            format="json",
        )

    def test_alta_modificacion_baja_se_comprueban_en_reporte(self):
        res = self.crear_sede()
        self.assertEqual(res.status_code, 201)
        pk = res.data["id"]
        self.assertEqual(
            self.client.patch(
                f"/api/sedes/{pk}/", {"nombre": "Sede modificada"}, format="json"
            ).status_code,
            200,
        )
        self.assertEqual(self.client.post(f"/api/sedes/{pk}/dar-de-baja/").status_code, 200)
        reporte = self.client.get("/api/reportes/operaciones/", self.rango)
        self.assertEqual(reporte.status_code, 200)
        self.assertEqual(
            reporte.data["totales"],
            {
                "ALTA": 1,
                "MODIFICACION": 1,
                "BAJA": 1,
                "OPERACION": 0,
            },
        )
        self.assertIn("Sede modificada", reporte.data["filas"][1]["descripcion"])
        self.assertEqual(reporte.data["filas"][0]["usuario"], "personal-prueba")
        self.assertEqual(Sede.objects.get(pk=pk).estado, "BAJA")
        evento = Operacion.objects.get(accion="MODIFICACION")
        self.assertEqual(evento.antes["nombre"], "Sede para ABMC")
        self.assertEqual(evento.despues["nombre"], "Sede modificada")
        otro = self.hoy - timedelta(days=1)
        self.assertEqual(operaciones_abmc(desde=otro, hasta=otro)["filas"], [])
        self.assertEqual(
            len(operaciones_abmc(desde=self.hoy, hasta=self.hoy, sede_id=pk)["filas"]), 3
        )

    def test_no_audita_consultas_ni_intentos_fallidos(self):
        self.crear_sede()
        self.crear_sede()
        self.client.get("/api/sedes/")
        self.assertEqual(Operacion.objects.count(), 1)

    def test_operacion_y_bitacora_son_atomicas(self):
        with patch(
            "apps.common.auditoria.registrar", side_effect=RuntimeError("Fallo de escritura")
        ):
            with self.assertRaises(RuntimeError):
                self.crear_sede()
        self.assertFalse(Sede.objects.exists())
        self.assertFalse(Operacion.objects.exists())

    def test_los_cinco_reportes_exigen_y_validan_desde_hasta(self):
        for ruta in [
            "prestamos-vencidos",
            "reportes/demanda-interbibliotecaria",
            "reportes/movimientos",
            "reportes/disponibilidad",
            "reportes/operaciones",
        ]:
            for filtros in [
                {},
                {"desde": "2026-11-02", "hasta": "2026-11-01"},
                {"desde": "2026-11-01", "hasta": "2026-99-99"},
            ]:
                with self.subTest(ruta=ruta, filtros=filtros):
                    self.assertEqual(self.client.get(f"/api/{ruta}/", filtros).status_code, 400)

    def preparar(self):
        call_command("preparar_exposicion", "--reiniciar", stdout=StringIO())

    def test_escenario_y_resultados_independientes(self):
        self.preparar()
        self.assertEqual(Libro.objects.count(), 44)
        self.assertEqual(Ejemplar.objects.count(), 132)
        self.assertEqual(Ejemplar.objects.filter(estado="DISPONIBLE").count(), 116)
        self.assertEqual(
            len(
                obtener_prestamos_vencidos(desde=date(2026, 10, 1), fecha_corte=date(2026, 10, 31))
            ),
            2,
        )
        vencidos = obtener_prestamos_vencidos(fecha_corte=date(2026, 10, 31))
        atrasos = sorted(p["dias_atraso"] for grupo in vencidos for p in grupo["prestamos"])
        self.assertEqual(atrasos, [7, 19])
        # Desde el 06/10 queda fuera Skywalker (entregado el 05/10); sólo Y: The Last Man.
        recientes = obtener_prestamos_vencidos(
            desde=date(2026, 10, 6), fecha_corte=date(2026, 10, 31)
        )
        self.assertEqual([len(g["prestamos"]) for g in recientes], [1])
        datos = disponibilidad_catalogo(desde=date(2026, 10, 1), hasta=date(2026, 10, 31))
        self.assertEqual(datos["resumen"], "116 de 132 ejemplares disponibles")
        self.assertEqual(
            disponibilidad_catalogo(desde=date(2026, 9, 1), hasta=date(2026, 9, 30))["filas"], []
        )

    def test_reinicio_preserva_cuentas_y_no_reintroduce_demo(self):
        user = get_user_model().objects.create_user(
            username="biblioteca", password="Clave-propia-85"
        )
        self.preparar()
        call_command("cargar_demo", stdout=StringIO())
        self.assertEqual(Libro.objects.count(), 44)
        self.preparar()
        self.assertEqual(Ejemplar.objects.count(), 132)
        self.assertEqual(Operacion.objects.count(), 1)
        user.refresh_from_db()
        self.assertTrue(user.check_password("Clave-propia-85"))

    def test_rango_de_altas_y_estado_actual_evidencian_baja(self):
        self.preparar()
        copia = Ejemplar.objects.get(codigo_inventario="EXPO-001")
        rango = {"desde": "2026-10-01", "hasta": "2026-10-31"}
        self.assertEqual(
            self.client.post(f"/api/ejemplares/{copia.pk}/dar-de-baja/").status_code, 200
        )
        datos = self.client.get("/api/reportes/disponibilidad/", rango).data
        self.assertEqual(datos["resumen"], "115 de 132 ejemplares disponibles")
        fila = next(
            f
            for f in datos["filas"]
            if f["libro_id"] == copia.libro_id
            and f["sede_propietaria_id"] == copia.sede_propietaria_id
        )
        self.assertEqual(fila["por_estado"]["BAJA"], 1)
