from django.test import TestCase

from apps.sedes.exceptions import (
    NombreSedeDuplicadoError,
    SedeInactivaError,
    SedeYaActivaError,
    SedeYaDadaDeBajaError,
)
from apps.sedes.models import EstadoSede
from apps.sedes.services import (
    crear_sede,
    dar_de_baja_sede,
    reactivar_sede,
    validar_sede_activa,
)


class SedeServicesTest(TestCase):
    def crear_sede(self, nombre="Biblioteca Central"):
        return crear_sede(
            nombre=nombre,
            direccion="Av. Siempre Viva 123",
            contacto="central@biblioteca.test",
            horarios="Lunes a viernes de 8 a 18",
        )

    def test_crear_sede_normaliza_espacios(self):
        sede = crear_sede(
            nombre="  Biblioteca Central  ",
            direccion="  Av. Siempre Viva 123  ",
            contacto="  central@biblioteca.test  ",
            horarios="  Lunes a viernes de 8 a 18  ",
        )

        self.assertEqual(sede.nombre, "Biblioteca Central")
        self.assertEqual(sede.direccion, "Av. Siempre Viva 123")

    def test_crear_sede_rechaza_nombre_duplicado(self):
        self.crear_sede("Biblioteca Central")

        with self.assertRaises(NombreSedeDuplicadoError):
            self.crear_sede("biblioteca central")

    def test_dar_de_baja_cambia_estado(self):
        sede = dar_de_baja_sede(sede=self.crear_sede())

        self.assertEqual(sede.estado, EstadoSede.BAJA)

    def test_no_permite_dar_de_baja_dos_veces(self):
        sede = dar_de_baja_sede(sede=self.crear_sede())

        with self.assertRaises(SedeYaDadaDeBajaError):
            dar_de_baja_sede(sede=sede)

    def test_reactivar_sede(self):
        sede = dar_de_baja_sede(sede=self.crear_sede())
        sede = reactivar_sede(sede=sede)

        self.assertEqual(sede.estado, EstadoSede.ACTIVA)

    def test_no_permite_reactivar_sede_activa(self):
        sede = self.crear_sede()

        with self.assertRaises(SedeYaActivaError):
            reactivar_sede(sede=sede)

    def test_validar_sede_activa_rechaza_sede_de_baja(self):
        sede = dar_de_baja_sede(sede=self.crear_sede())

        with self.assertRaises(SedeInactivaError):
            validar_sede_activa(sede=sede)
