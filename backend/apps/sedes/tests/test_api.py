from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.sedes.models import EstadoSede, Sede


class SedeApiTest(APITestCase):
    def setUp(self):
        self.datos = {
            "nombre": "Biblioteca Central",
            "direccion": "Av. Siempre Viva 123",
            "contacto": "central@biblioteca.test",
            "horarios": "Lunes a viernes de 8 a 18",
        }

    def crear_sede(self, **cambios):
        datos = self.datos.copy()
        datos.update(cambios)
        return Sede.objects.create(**datos)

    def test_crear_sede(self):
        response = self.client.post(reverse("sede-list"), self.datos, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["estado"], EstadoSede.ACTIVA)

    def test_rechazar_nombre_duplicado(self):
        self.crear_sede(nombre="Biblioteca Central")
        datos = self.datos | {"nombre": "biblioteca central"}

        response = self.client.post(reverse("sede-list"), datos, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_listar_sedes(self):
        self.crear_sede()

        response = self.client.get(reverse("sede-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

    def test_consultar_sede(self):
        sede = self.crear_sede()

        response = self.client.get(reverse("sede-detail", args=[sede.pk]))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], sede.pk)

    def test_modificar_sede(self):
        sede = self.crear_sede()

        response = self.client.patch(
            reverse("sede-detail", args=[sede.pk]),
            {"direccion": "Nueva dirección 456"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        sede.refresh_from_db()
        self.assertEqual(sede.direccion, "Nueva dirección 456")

    def test_estado_no_se_modifica_directamente(self):
        sede = self.crear_sede()

        response = self.client.patch(
            reverse("sede-detail", args=[sede.pk]),
            {"estado": EstadoSede.BAJA},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        sede.refresh_from_db()
        self.assertEqual(sede.estado, EstadoSede.ACTIVA)

    def test_dar_de_baja(self):
        sede = self.crear_sede()

        response = self.client.post(reverse("sede-dar-de-baja", args=[sede.pk]))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        sede.refresh_from_db()
        self.assertEqual(sede.estado, EstadoSede.BAJA)

    def test_no_permite_dar_de_baja_dos_veces(self):
        sede = self.crear_sede()
        url = reverse("sede-dar-de-baja", args=[sede.pk])

        self.client.post(url)
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_reactivar_sede(self):
        sede = self.crear_sede(estado=EstadoSede.BAJA)

        response = self.client.post(reverse("sede-reactivar", args=[sede.pk]))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        sede.refresh_from_db()
        self.assertEqual(sede.estado, EstadoSede.ACTIVA)

    def test_no_permite_eliminar_sede(self):
        sede = self.crear_sede()

        response = self.client.delete(reverse("sede-detail", args=[sede.pk]))

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_filtrar_por_estado(self):
        self.crear_sede(nombre="Sede Activa")
        self.crear_sede(nombre="Sede Inactiva", estado=EstadoSede.BAJA)

        response = self.client.get(reverse("sede-list"), {"estado": EstadoSede.ACTIVA})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["nombre"], "Sede Activa")

    def test_buscar_sede(self):
        self.crear_sede(nombre="Biblioteca Central")
        self.crear_sede(
            nombre="Biblioteca Norte",
            contacto="norte@biblioteca.test",
        )

        response = self.client.get(reverse("sede-list"), {"search": "central"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["nombre"], "Biblioteca Central")
