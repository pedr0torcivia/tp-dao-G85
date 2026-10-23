from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from apps.catalogo.models import EstadoEjemplar
from apps.circulacion.exceptions import (
    EjemplarEnOtraSedeError,
    EjemplarNoDisponibleError,
    EstadoSolicitudInvalidoError,
    FechaPrestamoInvalidaError,
    PrestamoYaDevueltoError,
    SocioInhabilitadoError,
)
from apps.circulacion.models import EstadoSolicitud, TipoSolicitud
from apps.circulacion.services import (
    asignar_ejemplar,
    cancelar_solicitud,
    crear_solicitud,
    entregar_solicitud,
    preparar_entrega,
    rechazar_solicitud,
    registrar_devolucion,
)
from apps.socios.models import EstadoSocio

from .factories import crear_ejemplar, crear_libro, crear_sede, crear_socio


class ReglasCirculacionTest(TestCase):
    def setUp(self):
        self.sede = crear_sede()
        self.otra_sede = crear_sede(nombre="Otra")
        self.socio = crear_socio()
        self.libro = crear_libro()
        self.ejemplar = crear_ejemplar(
            libro=self.libro,
            sede=self.sede,
        )

    def crear_local(self):
        return crear_solicitud(
            socio=self.socio,
            libro=self.libro,
            sede_origen=self.sede,
            sede_destino=self.sede,
            tipo=TipoSolicitud.LOCAL,
        )

    def test_socio_inhabilitado_no_puede_solicitar(self):
        self.socio.estado = EstadoSocio.INHABILITADO
        self.socio.save(update_fields=["estado"])
        with self.assertRaises(SocioInhabilitadoError):
            self.crear_local()

    def test_no_asigna_ejemplar_no_disponible(self):
        solicitud = self.crear_local()
        self.ejemplar.estado = EstadoEjemplar.PRESTADO
        self.ejemplar.save(update_fields=["estado"])
        with self.assertRaises(EjemplarNoDisponibleError):
            asignar_ejemplar(solicitud=solicitud, ejemplar=self.ejemplar)

    def test_no_entrega_ejemplar_en_otra_sede(self):
        solicitud = self.crear_local()
        asignar_ejemplar(solicitud=solicitud, ejemplar=self.ejemplar)
        preparar_entrega(solicitud=solicitud)
        self.ejemplar.sede_actual = self.otra_sede
        self.ejemplar.save(update_fields=["sede_actual"])
        ahora = timezone.now()
        with self.assertRaises(EjemplarEnOtraSedeError):
            entregar_solicitud(
                solicitud=solicitud,
                fecha_entrega=ahora,
                fecha_vencimiento=ahora + timedelta(days=14),
            )

    def test_vencimiento_debe_ser_posterior_a_entrega(self):
        solicitud = self.crear_local()
        asignar_ejemplar(solicitud=solicitud, ejemplar=self.ejemplar)
        preparar_entrega(solicitud=solicitud)
        ahora = timezone.now()
        with self.assertRaises(FechaPrestamoInvalidaError):
            entregar_solicitud(
                solicitud=solicitud,
                fecha_entrega=ahora,
                fecha_vencimiento=ahora,
            )

    def test_no_permite_doble_devolucion(self):
        solicitud = self.crear_local()
        asignar_ejemplar(solicitud=solicitud, ejemplar=self.ejemplar)
        preparar_entrega(solicitud=solicitud)
        ahora = timezone.now()
        prestamo = entregar_solicitud(
            solicitud=solicitud,
            fecha_entrega=ahora,
            fecha_vencimiento=ahora + timedelta(days=14),
        )
        registrar_devolucion(
            prestamo=prestamo,
            fecha_devolucion=ahora + timedelta(days=1),
            condicion_devolucion="APTO",
        )
        with self.assertRaises(PrestamoYaDevueltoError):
            registrar_devolucion(
                prestamo=prestamo,
                fecha_devolucion=ahora + timedelta(days=2),
                condicion_devolucion="APTO",
            )

    def test_devolucion_permitida_con_socio_inhabilitado(self):
        solicitud = self.crear_local()
        asignar_ejemplar(solicitud=solicitud, ejemplar=self.ejemplar)
        preparar_entrega(solicitud=solicitud)
        ahora = timezone.now()
        prestamo = entregar_solicitud(
            solicitud=solicitud,
            fecha_entrega=ahora,
            fecha_vencimiento=ahora + timedelta(days=14),
        )
        self.socio.estado = EstadoSocio.INHABILITADO
        self.socio.save(update_fields=["estado"])
        registrar_devolucion(
            prestamo=prestamo,
            fecha_devolucion=ahora + timedelta(days=1),
            condicion_devolucion="APTO",
        )
        prestamo.refresh_from_db()
        self.assertIsNotNone(prestamo.fecha_devolucion)

    def test_cancelar_libera_el_ejemplar(self):
        solicitud = self.crear_local()
        asignar_ejemplar(solicitud=solicitud, ejemplar=self.ejemplar)
        cancelar_solicitud(solicitud=solicitud)
        self.ejemplar.refresh_from_db()
        self.assertEqual(self.ejemplar.estado, EstadoEjemplar.DISPONIBLE)

    def test_rechazar_solo_solicitud_pendiente(self):
        solicitud = self.crear_local()
        rechazar_solicitud(solicitud=solicitud)
        solicitud.refresh_from_db()
        self.assertEqual(solicitud.estado, EstadoSolicitud.RECHAZADA)
        with self.assertRaises(EstadoSolicitudInvalidoError):
            rechazar_solicitud(solicitud=solicitud)
