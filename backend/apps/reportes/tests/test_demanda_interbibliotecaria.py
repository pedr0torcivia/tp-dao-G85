from datetime import timedelta

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.catalogo.models import Libro
from apps.circulacion.models import (
    EstadoSolicitud,
    SolicitudPrestamo,
    TipoSolicitud,
)
from apps.sedes.models import Sede
from apps.socios.models import Socio


class DemandaInterbibliotecariaTest(APITestCase):
    def setUp(self):
        self.origen = Sede.objects.create(
            nombre="Origen",
            direccion="Origen 1",
            contacto="origen@example.com",
            horarios="8 a 18",
        )
        self.destino = Sede.objects.create(
            nombre="Destino",
            direccion="Destino 1",
            contacto="destino@example.com",
            horarios="8 a 18",
        )
        self.socio = Socio.objects.create(
            numero_socio="SOC-RP02",
            documento="99999999",
            nombre="Reporte",
            contacto="reporte@example.com",
        )
        self.libro_uno = Libro.objects.create(
            isbn="9780000000011",
            titulo="Libro demandado",
            autor="Autor",
            editorial="Editorial",
            edicion="1",
        )
        self.libro_dos = Libro.objects.create(
            isbn="9780000000012",
            titulo="Libro secundario",
            autor="Autor",
            editorial="Editorial",
            edicion="1",
        )

    def crear_solicitud(self, libro, estado=EstadoSolicitud.PENDIENTE):
        return SolicitudPrestamo.objects.create(
            socio=self.socio,
            libro=libro,
            sede_origen=self.origen,
            sede_destino=self.destino,
            tipo=TipoSolicitud.INTERBIBLIOTECARIO,
            estado=estado,
        )

    def test_ranking_excluye_rechazadas_y_canceladas(self):
        self.crear_solicitud(self.libro_uno)
        self.crear_solicitud(self.libro_uno)
        self.crear_solicitud(self.libro_dos)
        self.crear_solicitud(self.libro_uno, EstadoSolicitud.RECHAZADA)
        self.crear_solicitud(self.libro_uno, EstadoSolicitud.CANCELADA)

        respuesta = self.client.get(
            reverse("demanda-interbibliotecaria"),
            {"sede_id": self.destino.pk},
        )

        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(respuesta.data["total_solicitudes"], 3)
        self.assertEqual(respuesta.data["resultados"][0]["cantidad"], 2)

    def test_filtro_de_fechas(self):
        solicitud = self.crear_solicitud(self.libro_uno)
        hace_diez_dias = timezone.now() - timedelta(days=10)
        SolicitudPrestamo.objects.filter(pk=solicitud.pk).update(fecha_solicitud=hace_diez_dias)
        respuesta = self.client.get(
            reverse("demanda-interbibliotecaria"),
            {"fecha_desde": timezone.localdate().isoformat()},
        )
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(respuesta.data["total_solicitudes"], 0)
