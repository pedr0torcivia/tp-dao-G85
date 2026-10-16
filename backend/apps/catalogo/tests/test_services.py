from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.catalogo.models import Ejemplar, EstadoEjemplar
from apps.catalogo.services import crear_ejemplar, crear_libro
from apps.sedes.exceptions import SedeInactivaError
from apps.sedes.models import EstadoSede, Sede


class EjemplarServicesTest(TestCase):
    def setUp(self):
        self.sede = Sede.objects.create(
            nombre="Biblioteca Central",
            direccion="Av. Siempre Viva 123",
            contacto="central@biblioteca.test",
            horarios="Lunes a viernes",
            estado=EstadoSede.ACTIVA,
        )

        self.libro = crear_libro(
            titulo="El principito",
            autor="Antoine de Saint-Exupéry",
            editorial="Salamandra",
            edicion="1",
            isbn="9780000000001",
        )

    def crear_ejemplar(self, **cambios):
        datos = {
            "codigo_inventario": "EJ-0001",
            "libro": self.libro,
            "sede_propietaria": self.sede,
            "condicion_fisica": "Bueno",
        }
        datos.update(cambios)

        return crear_ejemplar(**datos)

    def test_crear_ejemplar_comienza_disponible(self):
        ejemplar = self.crear_ejemplar()

        self.assertEqual(ejemplar.estado, EstadoEjemplar.DISPONIBLE)
        self.assertEqual(ejemplar.sede_propietaria, self.sede)
        self.assertEqual(ejemplar.sede_actual, self.sede)
        self.assertEqual(ejemplar.condicion_fisica, "Bueno")

    def test_crear_ejemplar_limpia_espacios(self):
        ejemplar = self.crear_ejemplar(
            codigo_inventario="  EJ-0002  ",
            condicion_fisica="  Muy bueno  ",
        )

        self.assertEqual(ejemplar.codigo_inventario, "EJ-0002")
        self.assertEqual(ejemplar.condicion_fisica, "Muy bueno")

    def test_no_permite_ejemplar_en_sede_inactiva(self):
        sede_inactiva = Sede.objects.create(
            nombre="Biblioteca Cerrada",
            direccion="Calle 123",
            contacto="cerrada@biblioteca.test",
            horarios="Sin atención",
            estado=EstadoSede.BAJA,
        )

        with self.assertRaises(SedeInactivaError):
            self.crear_ejemplar(sede_propietaria=sede_inactiva)

        self.assertEqual(Ejemplar.objects.count(), 0)

    def test_no_permite_codigo_de_inventario_duplicado(self):
        self.crear_ejemplar()

        with self.assertRaises(ValidationError):
            self.crear_ejemplar()

        self.assertEqual(Ejemplar.objects.count(), 1)