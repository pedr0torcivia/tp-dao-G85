from datetime import timedelta

from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from apps.catalogo.models import EstadoEjemplar
from apps.circulacion.exceptions import (
    ReservaDuplicadaError,
    ReservaVencidaError,
)
from apps.circulacion.models import EstadoReserva, EstadoSolicitud
from apps.circulacion.services import (
    asignar_reserva,
    cancelar_reserva,
    crear_reserva,
    entregar_solicitud,
    expirar_reserva,
)

from .factories import crear_ejemplar, crear_libro, crear_sede, crear_socio


class ReservaServiceTest(TestCase):
    def setUp(self):
        self.sede = crear_sede()
        self.socio = crear_socio()
        self.libro = crear_libro()
        self.ejemplar = crear_ejemplar(libro=self.libro, sede=self.sede)

    def crear(self):
        return crear_reserva(
            socio=self.socio,
            libro=self.libro,
            sede_retiro=self.sede,
        )

    def test_no_permite_reserva_vigente_duplicada(self):
        self.crear()
        with self.assertRaises(ReservaDuplicadaError):
            self.crear()

    def test_asignar_reserva_crea_solicitud_lista(self):
        reserva = self.crear()
        limite = timezone.now() + timedelta(days=2)
        asignar_reserva(
            reserva=reserva,
            ejemplar=self.ejemplar,
            fecha_limite_retiro=limite,
        )
        reserva.refresh_from_db()
        self.ejemplar.refresh_from_db()
        self.assertEqual(reserva.estado, EstadoReserva.LISTA_PARA_RETIRO)
        self.assertEqual(
            reserva.solicitud.estado,
            EstadoSolicitud.LISTA_PARA_ENTREGA,
        )
        self.assertEqual(
            self.ejemplar.estado,
            EstadoEjemplar.LISTO_PARA_ENTREGA,
        )

    def test_entrega_cumple_reserva(self):
        reserva = self.crear()
        ahora = timezone.now()
        asignar_reserva(
            reserva=reserva,
            ejemplar=self.ejemplar,
            fecha_limite_retiro=ahora + timedelta(days=2),
        )
        entregar_solicitud(
            solicitud=reserva.solicitud,
            fecha_entrega=ahora + timedelta(hours=1),
            fecha_vencimiento=ahora + timedelta(days=15),
        )
        reserva.refresh_from_db()
        self.assertEqual(reserva.estado, EstadoReserva.CUMPLIDA)

    def test_no_entrega_reserva_vencida(self):
        reserva = self.crear()
        ahora = timezone.now()
        asignar_reserva(
            reserva=reserva,
            ejemplar=self.ejemplar,
            fecha_limite_retiro=ahora + timedelta(hours=1),
        )
        with self.assertRaises(ReservaVencidaError):
            entregar_solicitud(
                solicitud=reserva.solicitud,
                fecha_entrega=ahora + timedelta(hours=2),
                fecha_vencimiento=ahora + timedelta(days=15),
            )

    def test_cancelar_reserva_libera_ejemplar_y_solicitud(self):
        reserva = self.crear()
        asignar_reserva(
            reserva=reserva,
            ejemplar=self.ejemplar,
            fecha_limite_retiro=timezone.now() + timedelta(days=2),
        )
        cancelar_reserva(reserva=reserva)
        reserva.refresh_from_db()
        self.ejemplar.refresh_from_db()
        reserva.solicitud.refresh_from_db()
        self.assertEqual(reserva.estado, EstadoReserva.CANCELADA)
        self.assertEqual(self.ejemplar.estado, EstadoEjemplar.DISPONIBLE)
        self.assertEqual(
            reserva.solicitud.estado,
            EstadoSolicitud.CANCELADA,
        )

    def test_expirar_antes_del_limite_es_rechazado(self):
        reserva = self.crear()
        asignar_reserva(
            reserva=reserva,
            ejemplar=self.ejemplar,
            fecha_limite_retiro=timezone.now() + timedelta(days=2),
        )
        with self.assertRaises(ReservaVencidaError):
            expirar_reserva(reserva=reserva)

    def test_comando_expira_reserva_vencida(self):
        reserva = self.crear()
        asignar_reserva(
            reserva=reserva,
            ejemplar=self.ejemplar,
            fecha_limite_retiro=timezone.now() + timedelta(hours=1),
        )
        ahora = timezone.now()
        reserva.fecha_reserva = ahora - timedelta(days=2)
        reserva.fecha_limite_retiro = ahora - timedelta(minutes=1)
        reserva.save(update_fields=["fecha_reserva", "fecha_limite_retiro"])
        call_command("expirar_reservas", verbosity=0)
        reserva.refresh_from_db()
        self.assertEqual(reserva.estado, EstadoReserva.EXPIRADA)
