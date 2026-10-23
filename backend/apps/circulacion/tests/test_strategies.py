from django.test import TestCase

from apps.circulacion.exceptions import EstadoSolicitudInvalidoError
from apps.circulacion.models import TipoSolicitud
from apps.circulacion.strategies import (
    TramitacionInterbibliotecaria,
    TramitacionLocal,
    obtener_estrategia,
)

from .factories import crear_sede


class StrategyTest(TestCase):
    def setUp(self):
        self.origen = crear_sede(nombre="Origen")
        self.destino = crear_sede(nombre="Destino")

    def test_factory_selecciona_estrategia_local(self):
        self.assertIsInstance(
            obtener_estrategia(TipoSolicitud.LOCAL),
            TramitacionLocal,
        )

    def test_factory_selecciona_estrategia_interbibliotecaria(self):
        self.assertIsInstance(
            obtener_estrategia(TipoSolicitud.INTERBIBLIOTECARIO),
            TramitacionInterbibliotecaria,
        )

    def test_local_requiere_la_misma_sede(self):
        estrategia = obtener_estrategia(TipoSolicitud.LOCAL)
        with self.assertRaises(EstadoSolicitudInvalidoError):
            estrategia.validar_creacion(
                sede_origen=self.origen,
                sede_destino=self.destino,
            )

    def test_interbibliotecaria_requiere_sedes_diferentes(self):
        estrategia = obtener_estrategia(TipoSolicitud.INTERBIBLIOTECARIO)
        with self.assertRaises(EstadoSolicitudInvalidoError):
            estrategia.validar_creacion(
                sede_origen=self.origen,
                sede_destino=self.origen,
            )
