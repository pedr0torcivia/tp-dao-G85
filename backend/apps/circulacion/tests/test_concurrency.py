from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest import skipUnless

from django.db import close_old_connections, connection
from django.test import TransactionTestCase

from apps.circulacion.exceptions import EjemplarNoDisponibleError
from apps.circulacion.models import EstadoSolicitud, TipoSolicitud
from apps.circulacion.services import asignar_ejemplar, crear_solicitud

from .factories import crear_ejemplar, crear_libro, crear_sede, crear_socio


@skipUnless(
    connection.vendor == "postgresql",
    "La semántica de select_for_update debe probarse con PostgreSQL.",
)
class AsignacionConcurrenteTest(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        self.sede = crear_sede()
        self.libro = crear_libro()
        self.ejemplar = crear_ejemplar(libro=self.libro, sede=self.sede)
        self.socio_uno = crear_socio(numero="SOC-001", documento="11111111")
        self.socio_dos = crear_socio(numero="SOC-002", documento="22222222")
        self.solicitud_uno = self._crear_solicitud(self.socio_uno)
        self.solicitud_dos = self._crear_solicitud(self.socio_dos)

    def _crear_solicitud(self, socio):
        return crear_solicitud(
            socio=socio,
            libro=self.libro,
            sede_origen=self.sede,
            sede_destino=self.sede,
            tipo=TipoSolicitud.LOCAL,
        )

    def test_un_ejemplar_no_se_asigna_a_dos_solicitudes(self):
        barrera = Barrier(2)

        def intentar(solicitud_id):
            close_old_connections()
            barrera.wait()
            try:
                asignar_ejemplar(
                    solicitud=type(self.solicitud_uno)(pk=solicitud_id),
                    ejemplar=type(self.ejemplar)(pk=self.ejemplar.pk),
                )
                return "asignada"
            except EjemplarNoDisponibleError:
                return "rechazada"
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as ejecutor:
            resultados = list(
                ejecutor.map(
                    intentar,
                    [self.solicitud_uno.pk, self.solicitud_dos.pk],
                )
            )

        self.assertCountEqual(resultados, ["asignada", "rechazada"])
        asignadas = (
            type(self.solicitud_uno)
            .objects.filter(
                estado=EstadoSolicitud.ASIGNADA,
                ejemplar=self.ejemplar,
            )
            .count()
        )
        self.assertEqual(asignadas, 1)
