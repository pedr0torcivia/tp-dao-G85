from django.test import TestCase

from apps.catalogo.exceptions import (
    CodigoInventarioDuplicadoError,
    EjemplarNoAsignadoError,
    EjemplarNoDisponibleError,
    SedePropietariaInactivaError,
)
from apps.catalogo.models import CondicionFisica, Ejemplar, EstadoEjemplar
from apps.catalogo.services import (
    aprobar_disponibilidad_ejemplar,
    actualizar_condicion_ejemplar,
    actualizar_libro,
    asignar_ejemplar,
    crear_ejemplar,
    crear_libro,
    dar_de_baja_ejemplar,
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
            "condicion_fisica": CondicionFisica.APTO,
        }
        datos.update(cambios)

        return crear_ejemplar(**datos)

    def test_crear_ejemplar_comienza_disponible(self):
        ejemplar = self.crear_ejemplar()

        self.assertEqual(ejemplar.estado, EstadoEjemplar.DISPONIBLE)
        self.assertEqual(ejemplar.sede_propietaria, self.sede)
        self.assertEqual(ejemplar.sede_actual, self.sede)
        self.assertEqual(ejemplar.condicion_fisica, CondicionFisica.APTO)

    def test_crear_ejemplar_limpia_espacios(self):
        """
        La condición física es texto normalizado, por lo que se recorta
        el espacio sobrante de las puntas.
        """
        ejemplar = self.crear_ejemplar(
            codigo_inventario="  EJ-0002  ",
            condicion_fisica="  APTO  ",
        )

        self.assertEqual(ejemplar.codigo_inventario, "EJ-0002")
        self.assertEqual(ejemplar.condicion_fisica, "APTO")

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

    def _ejemplar_en_estado(self, estado: str, condicion="APTO", sede_actual=None) -> Ejemplar:
        """Crea un ejemplar y lo coloca en el estado pedido (sin servicios)."""
        codigo = f"EJ-{Ejemplar.objects.count() + 1:04d}"
        ejemplar = Ejemplar.objects.create(
            codigo_inventario=codigo,
            libro=self.libro,
            sede_propietaria=self.sede,
            sede_actual=sede_actual or self.sede,
            estado=estado,
            condicion_fisica=condicion,
        )
        return ejemplar

    def test_no_permite_dar_de_baja_un_ejemplar_comprometido(self):
        from apps.catalogo.exceptions import EjemplarComprometidoError

        for estado in (
            EstadoEjemplar.ASIGNADO,
            EstadoEjemplar.PRESTADO,
            EstadoEjemplar.EN_TRANSITO,
        ):
            ejemplar = self._ejemplar_en_estado(estado)

            with self.assertRaises(EjemplarComprometidoError):
                dar_de_baja_ejemplar(ejemplar=ejemplar)

    def test_no_permite_dar_de_baja_dos_veces(self):
        from apps.catalogo.exceptions import EjemplarDadoDeBajaError

        ejemplar = self.crear_ejemplar()
        self.assertEqual(dar_de_baja_ejemplar(ejemplar=ejemplar).estado, EstadoEjemplar.BAJA)

        with self.assertRaises(EjemplarDadoDeBajaError):
            dar_de_baja_ejemplar(ejemplar=ejemplar)

    def test_aprobar_disponibilidad_devuelve_un_ejemplar_revisado(self):
        ejemplar = self._ejemplar_en_estado(EstadoEjemplar.EN_REVISION)

        ejemplar = aprobar_disponibilidad_ejemplar(ejemplar=ejemplar)

        self.assertEqual(ejemplar.estado, EstadoEjemplar.DISPONIBLE)

    def test_aprobar_disponibilidad_requiere_tener_estado_en_revision(self):
        from apps.catalogo.exceptions import EjemplarNoRevisadoError

        ejemplar = self.crear_ejemplar()

        with self.assertRaises(EjemplarNoRevisadoError):
            aprobar_disponibilidad_ejemplar(ejemplar=ejemplar)

    def test_aprobar_disponibilidad_requiere_condicion_apta_y_ubicacion(self):
        from apps.catalogo.exceptions import EjemplarInconsistenteError

        no_apto = self._ejemplar_en_estado(
            EstadoEjemplar.EN_REVISION,
            condicion=CondicionFisica.NO_APTO,
        )
        en_otra_sede = self._ejemplar_en_estado(
            EstadoEjemplar.EN_REVISION,
            sede_actual=Sede.objects.create(
                nombre="Biblioteca Norte",
                direccion="Av. Norte 456",
                contacto="norte@biblioteca.test",
                horarios="Lunes a viernes",
            ),
        )

        with self.assertRaises(EjemplarInconsistenteError):
            aprobar_disponibilidad_ejemplar(ejemplar=no_apto)

        with self.assertRaises(EjemplarInconsistenteError):
            aprobar_disponibilidad_ejemplar(ejemplar=en_otra_sede)

    def test_aprobar_disponibilidad_requiere_sede_activa(self):
        from apps.sedes.services import dar_de_baja_sede

        ejemplar = self._ejemplar_en_estado(EstadoEjemplar.EN_REVISION)
        dar_de_baja_sede(sede=self.sede)

        with self.assertRaises(SedePropietariaInactivaError):
            aprobar_disponibilidad_ejemplar(ejemplar=ejemplar)

    def test_actualizar_condicion_fisica(self):
        ejemplar = self.crear_ejemplar()

        ejemplar = actualizar_condicion_ejemplar(
            ejemplar=ejemplar,
            condicion_fisica=CondicionFisica.NO_APTO,
        )

        self.assertEqual(ejemplar.condicion_fisica, CondicionFisica.NO_APTO)

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
