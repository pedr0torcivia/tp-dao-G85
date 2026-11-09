from datetime import date, timedelta
from io import StringIO

from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APITestCase

from apps.catalogo.models import Ejemplar, Libro
from apps.circulacion.models import Prestamo
from apps.circulacion.tests.factories import crear_ejemplar, crear_libro, crear_sede, crear_socio
from apps.common.testing import autenticar_personal
from apps.logistica.models import EventoRemito
from apps.reportes.selectors import obtener_prestamos_vencidos
from apps.reportes.services import (
    demanda_interbibliotecaria,
    disponibilidad_catalogo,
    movimientos_entre_sedes,
)


class CircuitoCompletoTest(APITestCase):
    def test_disponibilidad_no_cuenta_material_no_apto_fuera_de_sede_o_sede_de_baja(self):
        respuesta = self.client.get("/api/disponibilidad/")
        self.assertEqual(respuesta.data[0]["disponibles"], 1)
        self.ejemplar.condicion_fisica = "NO_APTO"
        self.ejemplar.save()
        self.assertEqual(self.client.get("/api/disponibilidad/").data[0]["disponibles"], 0)
        self.ejemplar.condicion_fisica = "APTO"
        self.ejemplar.sede_actual = self.norte
        self.ejemplar.save()
        self.assertEqual(self.client.get("/api/disponibilidad/").data[0]["disponibles"], 0)
        self.ejemplar.sede_actual = self.central
        self.ejemplar.save()
        self.central.estado = "BAJA"
        self.central.save()
        self.assertEqual(self.client.get("/api/disponibilidad/").data[0]["disponibles"], 0)

    def test_reportes_rechazan_fechas_invalidas_sin_error_interno(self):
        for ruta in ["reportes/movimientos", "reportes/demanda-interbibliotecaria"]:
            respuesta = self.client.get(
                f"/api/{ruta}/",
                {
                    "desde": "2026-10-01",
                    "hasta": "2026-99-99",
                },
            )
            self.assertEqual(respuesta.status_code, 400)

    def setUp(self):
        autenticar_personal(self.client)
        self.central = crear_sede(nombre="Central")
        self.norte = crear_sede(nombre="Norte")
        self.socio = crear_socio()
        self.libro = crear_libro()
        self.ejemplar = crear_ejemplar(libro=self.libro, sede=self.central)

    def post(self, ruta, datos=None):
        respuesta = self.client.post(f"/api/{ruta}/", datos or {}, format="json")
        self.assertIn(respuesta.status_code, (200, 201), respuesta.data)
        return respuesta.data

    def trasladar(self, origen, destino, numero):
        remito = self.post(
            "remitos",
            {
                "numero": numero,
                "sede_origen_id": origen.id,
                "sede_destino_id": destino.id,
            },
        )
        ruta = f"remitos/{remito['id']}"
        self.post(f"{ruta}/asignar", {"ejemplar_id": self.ejemplar.id})
        for accion in ["empaquetar", "despachar"]:
            self.post(f"{ruta}/{accion}")
        self.post(
            f"{ruta}/recibir",
            {
                "verificados": [self.ejemplar.id],
                "responsable": "Personal de prueba",
            },
        )
        self.assertEqual(EventoRemito.objects.filter(remito_id=remito["id"]).count(), 4)

    def circuito(self, condicion):
        solicitud = self.post(
            "solicitudes",
            {
                "socio_id": self.socio.id,
                "libro_id": self.libro.id,
                "sede_origen_id": self.central.id,
                "sede_destino_id": self.norte.id,
                "tipo": "INTERBIBLIOTECARIO",
            },
        )
        ruta = f"solicitudes/{solicitud['id']}"
        self.post(f"{ruta}/asignar", {"ejemplar_id": self.ejemplar.id})
        self.trasladar(self.central, self.norte, "IDA")
        prestamo = self.post(
            f"{ruta}/entregar",
            {
                "fecha_entrega": "2026-10-10T12:00:00-03:00",
                "fecha_vencimiento": "2026-10-24T12:00:00-03:00",
            },
        )
        self.post(
            f"prestamos/{prestamo['id']}/devolver",
            {
                "fecha_devolucion": "2026-10-15T12:00:00-03:00",
                "condicion_devolucion": condicion,
            },
        )
        # Un préstamo devuelto puede volver a su propietaria, incluso si está dañado.
        self.trasladar(self.norte, self.central, "VUELTA")
        self.ejemplar.refresh_from_db()
        self.assertEqual(self.ejemplar.sede_actual_id, self.central.id)
        self.assertEqual(self.ejemplar.estado, "EN_REVISION")
        respuesta = self.client.post(
            f"/api/ejemplares/{self.ejemplar.id}/aprobar-disponibilidad/", {}, format="json"
        )
        self.assertEqual(respuesta.status_code, 200 if condicion == "APTO" else 400)
        self.ejemplar.refresh_from_db()
        self.assertEqual(
            self.ejemplar.estado, "DISPONIBLE" if condicion == "APTO" else "EN_REVISION"
        )

    def test_interbibliotecario_hasta_retornar_y_recuperar_disponibilidad(self):
        self.circuito("APTO")

    def test_material_danado_retorna_sin_habilitarse(self):
        self.circuito("NO_APTO")

    def test_reserva_local_hasta_devolucion(self):
        ahora = timezone.now()
        reserva = self.post(
            "reservas",
            {
                "socio_id": self.socio.id,
                "libro_id": self.libro.id,
                "sede_retiro_id": self.central.id,
            },
        )
        self.post(
            f"reservas/{reserva['id']}/asignar-reserva",
            {
                "ejemplar_id": self.ejemplar.id,
                "fecha_limite_retiro": (ahora + timedelta(days=2)).isoformat(),
            },
        )
        solicitud = self.client.get("/api/solicitudes/").data["results"][0]
        prestamo = self.post(
            f"solicitudes/{solicitud['id']}/entregar",
            {
                "fecha_entrega": ahora.isoformat(),
                "fecha_vencimiento": (ahora + timedelta(days=14)).isoformat(),
            },
        )
        self.post(
            f"prestamos/{prestamo['id']}/devolver",
            {
                "fecha_devolucion": (ahora + timedelta(hours=1)).isoformat(),
                "condicion_devolucion": "APTO",
            },
        )
        self.post(f"ejemplares/{self.ejemplar.id}/aprobar-disponibilidad")
        self.assertEqual(
            self.client.get(f"/api/reservas/{reserva['id']}/").data["estado"], "CUMPLIDA"
        )

    def test_cancelar_retorno_conserva_revision_y_rechaza_tercera_sede(self):
        self.ejemplar.sede_actual = self.norte
        self.ejemplar.estado = "EN_REVISION"
        self.ejemplar.save()
        tercera = crear_sede(nombre="Sur")
        invalido = self.post(
            "remitos",
            {
                "numero": "TERCERA",
                "sede_origen_id": self.norte.id,
                "sede_destino_id": tercera.id,
            },
        )
        error = self.client.post(
            f"/api/remitos/{invalido['id']}/asignar/",
            {
                "ejemplar_id": self.ejemplar.id,
            },
            format="json",
        )
        self.assertEqual(error.status_code, 400)
        retorno = self.post(
            "remitos",
            {
                "numero": "RETORNO",
                "sede_origen_id": self.norte.id,
                "sede_destino_id": self.central.id,
            },
        )
        self.post(f"remitos/{retorno['id']}/asignar", {"ejemplar_id": self.ejemplar.id})
        self.post(f"remitos/{retorno['id']}/cancelar")
        self.ejemplar.refresh_from_db()
        self.assertEqual(self.ejemplar.estado, "EN_REVISION")
        self.assertEqual(self.ejemplar.sede_actual_id, self.norte.id)

    def test_duplicado_sin_isbn_se_rechaza_por_api_sin_error_interno(self):
        datos = {
            "titulo": "Edición sin ISBN",
            "autor": "Autora",
            "editorial": "Editorial",
            "edicion": "1",
        }
        self.post("libros", datos)
        datos["titulo"] = "EDICIÓN SIN ISBN"
        respuesta = self.client.post("/api/libros/", datos, format="json")
        self.assertEqual(respuesta.status_code, 400)
        self.assertEqual(Libro.objects.filter(isbn__isnull=True).count(), 1)


class DatosDemoTest(TestCase):
    def test_corte_historico_incluye_devolucion_posterior_y_filtro_de_sede(self):
        call_command("cargar_demo", stdout=StringIO())
        prestamo = Prestamo.objects.get()
        prestamo.fecha_devolucion = prestamo.fecha_vencimiento + timedelta(days=14)
        prestamo.condicion_devolucion = "APTO"
        prestamo.save()
        self.assertEqual(len(obtener_prestamos_vencidos(fecha_corte=date(2026, 10, 20))), 1)
        self.assertEqual(obtener_prestamos_vencidos(fecha_corte=date(2026, 10, 23)), [])
        self.assertEqual(
            obtener_prestamos_vencidos(
                fecha_corte=date(2026, 10, 20),
                sede_id=999,
            ),
            [],
        )

    def test_carga_idempotente_y_reportes_con_resultado_independiente(self):
        salida = StringIO()
        call_command("cargar_demo", stdout=salida)
        call_command("cargar_demo", stdout=salida)
        self.assertEqual(Libro.objects.count(), 2)
        self.assertEqual(Ejemplar.objects.count(), 7)
        vencidos = obtener_prestamos_vencidos(fecha_corte=date(2026, 10, 20))
        self.assertEqual(vencidos[0]["cantidad"], 1)
        self.assertEqual(vencidos[0]["prestamos"][0]["dias_atraso"], 12)
        rango = {"desde": date(2026, 10, 1), "hasta": date(2026, 10, 20)}
        demanda = demanda_interbibliotecaria(**rango)
        self.assertEqual(sum(f["cantidad"] for f in demanda["filas"]), 2)
        movimientos = movimientos_entre_sedes(**rango)["filas"][0]
        self.assertEqual(movimientos["despachados"], 2)
        self.assertEqual(movimientos["recibidos"], 1)
        self.assertEqual(movimientos["dias_transito_promedio"], 2)
        disponibilidad = disponibilidad_catalogo()["filas"]
        self.assertEqual(sum(f["total"] for f in disponibilidad), 7)
        self.assertEqual(sum(f["disponibles"] for f in disponibilidad), 3)
