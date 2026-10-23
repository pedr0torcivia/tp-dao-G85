from datetime import timedelta

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.circulacion.models import EstadoReserva, EstadoSolicitud

from .factories import crear_ejemplar, crear_libro, crear_sede, crear_socio


class CirculacionApiTest(APITestCase):
    def setUp(self):
        self.sede = crear_sede()
        self.socio = crear_socio()
        self.libro = crear_libro()
        self.ejemplar = crear_ejemplar(libro=self.libro, sede=self.sede)

    def test_flujo_local_por_api(self):
        respuesta = self.client.post(
            reverse("solicitud-list"),
            {
                "socio_id": self.socio.pk,
                "libro_id": self.libro.pk,
                "sede_origen_id": self.sede.pk,
                "sede_destino_id": self.sede.pk,
                "tipo": "LOCAL",
            },
            format="json",
        )
        self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED)
        solicitud_id = respuesta.data["id"]

        respuesta = self.client.post(
            reverse("solicitud-asignar", args=[solicitud_id]),
            {"ejemplar_id": self.ejemplar.pk},
            format="json",
        )
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)

        respuesta = self.client.post(
            reverse("solicitud-preparar-entrega", args=[solicitud_id]),
            {},
            format="json",
        )
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)

        ahora = timezone.now()
        respuesta = self.client.post(
            reverse("solicitud-entregar", args=[solicitud_id]),
            {
                "fecha_entrega": ahora.isoformat(),
                "fecha_vencimiento": (ahora + timedelta(days=14)).isoformat(),
            },
            format="json",
        )
        self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED)

        respuesta = self.client.post(
            reverse("prestamo-devolver", args=[respuesta.data["id"]]),
            {
                "fecha_devolucion": (ahora + timedelta(days=1)).isoformat(),
                "condicion_devolucion": "APTO",
            },
            format="json",
        )
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)

    def test_api_no_expone_patch_de_solicitud(self):
        respuesta = self.client.post(
            reverse("solicitud-list"),
            {
                "socio_id": self.socio.pk,
                "libro_id": self.libro.pk,
                "sede_origen_id": self.sede.pk,
                "sede_destino_id": self.sede.pk,
                "tipo": "LOCAL",
            },
            format="json",
        )
        detalle = reverse("solicitud-detail", args=[respuesta.data["id"]])
        respuesta = self.client.patch(detalle, {"estado": "CUMPLIDA"}, format="json")
        self.assertEqual(
            respuesta.status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    def test_crear_solicitud_exige_tipo_explicito(self):
        respuesta = self.client.post(
            reverse("solicitud-list"),
            {
                "socio_id": self.socio.pk,
                "libro_id": self.libro.pk,
                "sede_origen_id": self.sede.pk,
                "sede_destino_id": self.sede.pk,
            },
            format="json",
        )

        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("tipo", respuesta.data["error"]["detail"])

    def test_flujo_reserva_por_api(self):
        respuesta = self.client.post(
            reverse("reserva-list"),
            {
                "socio_id": self.socio.pk,
                "libro_id": self.libro.pk,
                "sede_retiro_id": self.sede.pk,
            },
            format="json",
        )
        self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED)
        reserva_id = respuesta.data["id"]

        respuesta = self.client.post(
            reverse("reserva-asignar-reserva", args=[reserva_id]),
            {
                "ejemplar_id": self.ejemplar.pk,
                "fecha_limite_retiro": (timezone.now() + timedelta(days=2)).isoformat(),
            },
            format="json",
        )
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(respuesta.data["estado"], EstadoReserva.LISTA_PARA_RETIRO)

    def test_rechazar_solicitud(self):
        respuesta = self.client.post(
            reverse("solicitud-list"),
            {
                "socio_id": self.socio.pk,
                "libro_id": self.libro.pk,
                "sede_origen_id": self.sede.pk,
                "sede_destino_id": self.sede.pk,
                "tipo": "LOCAL",
            },
            format="json",
        )
        respuesta = self.client.post(
            reverse("solicitud-rechazar", args=[respuesta.data["id"]]),
            {},
            format="json",
        )
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(respuesta.data["estado"], EstadoSolicitud.RECHAZADA)

    def test_crear_solicitud_interbibliotecaria(self):
        destino = crear_sede(nombre="Destino")
        respuesta = self.client.post(
            reverse("solicitud-list"),
            {
                "socio_id": self.socio.pk,
                "libro_id": self.libro.pk,
                "sede_origen_id": self.sede.pk,
                "sede_destino_id": destino.pk,
                "tipo": "INTERBIBLIOTECARIO",
            },
            format="json",
        )
        self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED)
        self.assertEqual(respuesta.data["tipo"], "INTERBIBLIOTECARIO")

    def test_interbibliotecaria_no_admite_preparacion_local(self):
        destino = crear_sede(nombre="Destino")
        respuesta = self.client.post(
            reverse("solicitud-list"),
            {
                "socio_id": self.socio.pk,
                "libro_id": self.libro.pk,
                "sede_origen_id": self.sede.pk,
                "sede_destino_id": destino.pk,
                "tipo": "INTERBIBLIOTECARIO",
            },
            format="json",
        )
        solicitud_id = respuesta.data["id"]
        self.client.post(
            reverse("solicitud-asignar", args=[solicitud_id]),
            {"ejemplar_id": self.ejemplar.pk},
            format="json",
        )
        respuesta = self.client.post(
            reverse("solicitud-preparar-entrega", args=[solicitud_id]),
            {},
            format="json",
        )
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
