from django.test import TestCase

from apps.catalogo.exceptions import (
    CodigoInventarioDuplicadoError,
    EjemplarNoAsignadoError,
    EjemplarNoDisponibleError,
    SedePropietariaInactivaError,
)
from apps.catalogo.models import Ejemplar, EstadoEjemplar
from apps.catalogo.services import (
    actualizar_condicion_ejemplar,
    actualizar_libro,
    asignar_ejemplar,
    crear_ejemplar,
    crear_libro,
    liberar_ejemplar,
)
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

        with self.assertRaises(SedePropietariaInactivaError):
            self.crear_ejemplar(sede_propietaria=sede_inactiva)

        self.assertEqual(Ejemplar.objects.count(), 0)

    def test_no_permite_codigo_de_inventario_duplicado(self):
        self.crear_ejemplar()

        with self.assertRaises(CodigoInventarioDuplicadoError):
            self.crear_ejemplar()

        self.assertEqual(Ejemplar.objects.count(), 1)

    def test_actualizar_condicion_fisica(self):
        ejemplar = self.crear_ejemplar()

        ejemplar = actualizar_condicion_ejemplar(
            ejemplar=ejemplar,
            condicion_fisica="Muy bueno",
        )

        self.assertEqual(ejemplar.condicion_fisica, "Muy bueno")

    def test_asignar_y_liberar_ejemplar(self):
        ejemplar = self.crear_ejemplar()

        ejemplar = asignar_ejemplar(ejemplar=ejemplar)
        self.assertEqual(ejemplar.estado, EstadoEjemplar.ASIGNADO)

        ejemplar = liberar_ejemplar(ejemplar=ejemplar)
        self.assertEqual(ejemplar.estado, EstadoEjemplar.DISPONIBLE)

    def test_no_asigna_ejemplar_dos_veces(self):
        ejemplar = asignar_ejemplar(ejemplar=self.crear_ejemplar())

        with self.assertRaises(EjemplarNoDisponibleError):
            asignar_ejemplar(ejemplar=ejemplar)

    def test_no_libera_ejemplar_disponible(self):
        with self.assertRaises(EjemplarNoAsignadoError):
            liberar_ejemplar(ejemplar=self.crear_ejemplar())


class LibroServicesTest(TestCase):
    def test_actualizar_datos_bibliograficos(self):
        libro = crear_libro(
            titulo="El principito",
            autor="Antoine de Saint-Exupéry",
            editorial="Salamandra",
            edicion="1",
        )

        libro = actualizar_libro(
            libro=libro,
            datos={
                "titulo": "El principito actualizado",
                "autor": "Antoine de Saint-Exupéry",
            },
        )

        self.assertEqual(libro.titulo, "El principito actualizado")
