from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.catalogo.models import CondicionFisica, Ejemplar, Libro
from apps.sedes.models import Sede

from ..models import EstadoRemito, EventoRemito, Remito


class RemitoApiTest(APITestCase):
    def setUp(self):
        self.central = Sede.objects.create(
            nombre="Central",
            direccion="Av. 1",
            contacto="central@biblioteca.test",
            horarios="Lunes a viernes de 8 a 18",
        )
        self.norte = Sede.objects.create(
            nombre="Norte",
            direccion="Av. 2",
            contacto="norte@biblioteca.test",
            horarios="Lunes a viernes de 8 a 18",
        )
        self.libro = Libro.objects.create(
            titulo="Rayuela",
            autor="Cortázar",
            editorial="Sudamericana",
            edicion="1",
        )
        self.ejemplar = self.crear_ejemplar()

    def crear_ejemplar(self, codigo="E-0001", **cambios):
        datos = {
            "codigo_inventario": codigo,
            "libro": self.libro,
            "sede_propietaria": self.central,
            "sede_actual": self.central,
            "estado": "DISPONIBLE",
            "condicion_fisica": CondicionFisica.APTO,
        }
        datos.update(cambios)
        return Ejemplar.objects.create(**datos)

    def crear_remito(self, numero="REM-0001"):
        return self.client.post(
            reverse("remito-list"),
            {
                "numero": numero,
                "sede_origen_id": self.central.id,
                "sede_destino_id": self.norte.id,
            },
            format="json",
        )

    def test_crea_remito_con_evento_inicial(self):
        response = self.crear_remito()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["estado"], EstadoRemito.EN_PREPARACION)
        self.assertEqual(response.data["sede_origen_id"], self.central.id)
        self.assertEqual(EventoRemito.objects.filter(remito_id=response.data["id"]).count(), 1)

    def test_rechaza_numero_duplicado(self):
        self.crear_remito("REM-0001")

        response = self.crear_remito("rem-0001")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["error"]["detail"]["numero"], ["Ya existe un remito con ese número."]
        )

    def test_rechaza_origen_igual_al_destino(self):
        response = self.client.post(
            reverse("remito-list"),
            {
                "numero": "REM-0002",
                "sede_origen_id": self.central.id,
                "sede_destino_id": self.central.id,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_listar_y_consultar(self):
        self.crear_remito("REM-0001")

        lista = self.client.get(reverse("remito-list"))
        self.assertEqual(lista.status_code, status.HTTP_200_OK)
        self.assertEqual(lista.data["count"], 1)

        detalle_id = lista.data["results"][0]["id"]
        consulta = self.client.get(reverse("remito-detail", args=[detalle_id]))
        self.assertEqual(consulta.status_code, status.HTTP_200_OK)
        self.assertEqual(consulta.data["numero"], "REM-0001")

    def test_estado_no_se_modifica_directamente(self):
        creacion = self.crear_remito("REM-0001")
        remito_id = creacion.data["id"]

        response = self.client.patch(
            reverse("remito-detail", args=[remito_id]),
            {"estado": EstadoRemito.RECIBIDO},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        remito = Remito.objects.get(pk=remito_id)
        self.assertEqual(remito.estado, EstadoRemito.EN_PREPARACION)

    def test_ciclo_completo_por_http(self):
        creacion = self.crear_remito("REM-0001")
        remito_id = creacion.data["id"]

        asignacion = self.client.post(
            reverse("remito-asignar", args=[remito_id]),
            {"ejemplar_id": self.ejemplar.id},
            format="json",
        )
        self.assertEqual(asignacion.status_code, status.HTTP_200_OK)
        self.assertEqual(asignacion.data["remito_id"], remito_id)

        self.ejemplar.refresh_from_db()
        self.assertEqual(self.ejemplar.estado, "ASIGNADO")

        rutas = ["remito-empaquetar", "remito-despachar", "remito-registrar-salida"]
        for ruta in rutas:
            respuesta = self.client.post(reverse(ruta, args=[remito_id]), format="json")
            self.assertEqual(respuesta.status_code, status.HTTP_200_OK, ruta)

        parcial = self.client.post(
            reverse("remito-recibir", args=[remito_id]),
            {"responsable": "Personal Norte", "verificados": []},
            format="json",
        )
        self.assertEqual(parcial.status_code, status.HTTP_400_BAD_REQUEST)

        recepcion = self.client.post(
            reverse("remito-recibir", args=[remito_id]),
            {"responsable": "Personal Norte", "verificados": [self.ejemplar.id]},
            format="json",
        )
        self.assertEqual(recepcion.status_code, status.HTTP_200_OK)
        self.assertEqual(recepcion.data["estado"], EstadoRemito.RECIBIDO)
        self.ejemplar.refresh_from_db()
        self.assertEqual(self.ejemplar.sede_actual_id, self.norte.id)
        self.assertEqual(self.ejemplar.estado, "EN_REVISION")

        historial = self.client.get(reverse("evento-remito-list"), {"remito_id": remito_id})
        self.assertEqual(
            [evento["estado_nuevo"] for evento in historial.data["results"]],
            ["EN_PREPARACION", "EMPAQUETADO", "DESPACHADO", "EN_TRANSITO", "RECIBIDO"],
        )


class ComandoInvalidoApiTest(APITestCase):
    def setUp(self):
        self.central = Sede.objects.create(
            nombre="Central",
            direccion="Av. 1",
            contacto="central@biblioteca.test",
            horarios="Lunes a viernes de 8 a 18",
        )
        self.norte = Sede.objects.create(
            nombre="Norte",
            direccion="Av. 2",
            contacto="norte@biblioteca.test",
            horarios="Lunes a viernes de 8 a 18",
        )
        self.remito = Remito.objects.create(
            numero="REM-0001",
            sede_origen=self.central,
            sede_destino=self.norte,
        )

    def test_empaquetar_vacio_devuelve_error_con_envolvente(self):
        response = self.client.post(reverse("remito-empaquetar", args=[self.remito.pk]))

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"]["status"], 400)
        self.assertEqual(
            response.data["error"]["detail"]["detail"],
            "El remito debe contener al menos un ejemplar.",
        )

    def test_asignar_registra_condicion_de_salida(self):
        """El detalle lleva la condición física de salida del ejemplar."""
        libro = Libro.objects.create(
            titulo="Ficciones",
            autor="Borges",
            editorial="Sur",
            edicion="1",
        )
        ejemplar = Ejemplar.objects.create(
            codigo_inventario="E-0001",
            libro=libro,
            sede_propietaria=self.central,
            sede_actual=self.central,
            estado="DISPONIBLE",
            condicion_fisica=CondicionFisica.APTO,
        )

        response = self.client.post(
            reverse("remito-asignar", args=[self.remito.pk]),
            {"ejemplar_id": ejemplar.id},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["condicion_salida"], CondicionFisica.APTO)
