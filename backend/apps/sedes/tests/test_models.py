from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.sedes.models import EstadoSede, Sede


class SedeModelTest(TestCase):
    def crear_sede(self, **cambios):
        datos = {
            "nombre": "Biblioteca Central",
            "direccion": "Av. Siempre Viva 123",
            "contacto": "central@biblioteca.test",
            "horarios": "Lunes a viernes de 8 a 18",
        }
        datos.update(cambios)
        return Sede.objects.create(**datos)

    def test_sede_nueva_comienza_activa(self):
        sede = self.crear_sede()

        self.assertEqual(sede.estado, EstadoSede.ACTIVA)

    def test_str_devuelve_nombre(self):
        sede = self.crear_sede()

        self.assertEqual(str(sede), "Biblioteca Central")

    def test_nombre_es_unico_sin_distinguir_mayusculas(self):
        self.crear_sede(nombre="Biblioteca Central")

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                self.crear_sede(nombre="biblioteca central")

    def test_sedes_se_ordenan_por_nombre(self):
        self.crear_sede(nombre="Sede Norte")
        self.crear_sede(nombre="Sede Central")

        nombres = list(Sede.objects.values_list("nombre", flat=True))

        self.assertEqual(nombres, ["Sede Central", "Sede Norte"])
