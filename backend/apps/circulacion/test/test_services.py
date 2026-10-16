from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from apps.catalogo.models import Ejemplar, EstadoEjemplar, Libro
from apps.sedes.models import Sede
from apps.socios.models import Socio

from apps.circulacion.models import EstadoSolicitud
from apps.circulacion.services import (
    asignar_ejemplar,
    crear_solicitud_local,
    entregar_solicitud,
    preparar_entrega,
    registrar_devolucion,
)


class CirculacionLocalServiceTest(TestCase):
    def setUp(self):
        self.sede = Sede.objects.create(
            nombre="Biblioteca Central",
            direccion="Calle 123",
            contacto="central@example.com",
            horarios="Lunes a viernes",
        )

        self.socio = Socio.objects.create(
            numero_socio="SOC-001",
            documento="12345678",
            nombre="Ana Pérez",
            contacto="ana@example.com",
        )

        self.libro = Libro.objects.create(
            isbn="9780000000001",
            titulo="Patrones de diseño",
            autor="Gamma",
            editorial="Editorial",
            edicion="1",
        )

        self.ejemplar = Ejemplar.objects.create(
            codigo_inventario="EJ-001",
            libro=self.libro,
            sede_propietaria=self.sede,
            sede_actual=self.sede,
        )

    def test_recorrido_local_completo(self):
        solicitud = crear_solicitud_local(
            socio=self.socio,
            libro=self.libro,
            sede_origen=self.sede,
            sede_destino=self.sede,
        )

        self.assertEqual(
            solicitud.estado,
            EstadoSolicitud.PENDIENTE,
        )

        solicitud = asignar_ejemplar(
            solicitud=solicitud,
            ejemplar=self.ejemplar,
        )

        self.assertEqual(
            solicitud.estado,
            EstadoSolicitud.ASIGNADA,
        )

        solicitud = preparar_entrega(solicitud=solicitud)

        self.assertEqual(
            solicitud.estado,
            EstadoSolicitud.LISTA_PARA_ENTREGA,
        )

        fecha_entrega = timezone.now()

        prestamo = entregar_solicitud(
            solicitud=solicitud,
            fecha_entrega=fecha_entrega,
            fecha_vencimiento=fecha_entrega + timedelta(days=14),
        )

        solicitud.refresh_from_db()
        self.ejemplar.refresh_from_db()

        self.assertEqual(
            solicitud.estado,
            EstadoSolicitud.CUMPLIDA,
        )
        self.assertEqual(
            self.ejemplar.estado,
            EstadoEjemplar.PRESTADO,
        )

        registrar_devolucion(
            prestamo=prestamo,
            fecha_devolucion=fecha_entrega + timedelta(days=7),
            condicion_devolucion="APTO",
        )

        prestamo.refresh_from_db()
        self.ejemplar.refresh_from_db()

        self.assertIsNotNone(prestamo.fecha_devolucion)
        self.assertEqual(
            self.ejemplar.estado,
            EstadoEjemplar.EN_REVISION,
        )