from types import SimpleNamespace

from django.test import TestCase

from apps.logistica import states
from apps.logistica.exceptions import RemitoVacioError, TransicionInvalidaError
from apps.logistica.models import EstadoRemito


class DetallesFalsos:
    def __init__(self, cantidad: int):
        self._cantidad = cantidad

    def exists(self) -> bool:
        return self._cantidad > 0


def remito_falso(estado: str, detalles: int = 0) -> SimpleNamespace:
    """Sustituto de Remito para probar las clases de estado sin base de datos."""
    return SimpleNamespace(estado=estado, detalles=DetallesFalsos(detalles))


TRANSICIONES = ("empaquetar", "despachar", "registrar_salida", "recibir", "cancelar")


class RegistroEstadosTest(TestCase):
    def test_hay_una_clase_por_estado_persistido(self):
        self.assertEqual(len(states.ESTADOS_REMITO), len(EstadoRemito.values))

    def test_cada_clase_declara_su_valor_persistido(self):
        for valor, clase in states.ESTADOS_REMITO.items():
            self.assertEqual(clase.nombre, valor)

    def test_estado_actual_devuelve_la_clase_del_estado(self):
        remito = remito_falso(EstadoRemito.EMPAQUETADO)
        self.assertIsInstance(states.estado_actual(remito), states.Empaquetado)


class EmpaquetarTest(TestCase):
    def test_preparacion_con_detalles_transiciona_a_empaquetado(self):
        remito = remito_falso(EstadoRemito.EN_PREPARACION, detalles=2)

        destino = states.estado_actual(remito).empaquetar(remito)

        self.assertEqual(destino, EstadoRemito.EMPAQUETADO)

    def test_preparacion_sin_detalles_se_rechaza(self):
        remito = remito_falso(EstadoRemito.EN_PREPARACION, detalles=0)

        with self.assertRaises(RemitoVacioError):
            states.estado_actual(remito).empaquetar(remito)

    def test_empaquetado_y_otros_estados_no_aceptan_reempaquetar(self):
        for estado in EstadoRemito.values:
            if estado == EstadoRemito.EN_PREPARACION:
                continue
            remito = remito_falso(estado, detalles=3)

            with self.assertRaises(TransicionInvalidaError):
                states.estado_actual(remito).empaquetar(remito)


class DespacharTest(TestCase):
    def test_empaquetado_con_detalles_transiciona_a_despachado(self):
        remito = remito_falso(EstadoRemito.EMPAQUETADO, detalles=1)

        destino = states.estado_actual(remito).despachar(remito)

        self.assertEqual(destino, EstadoRemito.DESPACHADO)

    def test_empaquetado_sin_detalles_se_rechaza(self):
        remito = remito_falso(EstadoRemito.EMPAQUETADO, detalles=0)

        with self.assertRaises(RemitoVacioError):
            states.estado_actual(remito).despachar(remito)

    def test_la_preparacion_no_despacha_directamente(self):
        remito = remito_falso(EstadoRemito.EN_PREPARACION, detalles=5)

        with self.assertRaises(TransicionInvalidaError):
            states.estado_actual(remito).despachar(remito)


class RegistrarSalidaTest(TestCase):
    def test_solo_despachado_registra_salida(self):
        remito = remito_falso(EstadoRemito.DESPACHADO)

        destino = states.estado_actual(remito).registrar_salida(remito)

        self.assertEqual(destino, EstadoRemito.EN_TRANSITO)


class RecibirTest(TestCase):
    def test_solo_en_transito_recibe(self):
        remito = remito_falso(EstadoRemito.EN_TRANSITO)

        destino = states.estado_actual(remito).recibir(remito)

        self.assertEqual(destino, EstadoRemito.RECIBIDO)


class CancelarTest(TestCase):
    def test_se_cancela_en_preparacion_y_empaquetado(self):
        for estado in (EstadoRemito.EN_PREPARACION, EstadoRemito.EMPAQUETADO):
            remito = remito_falso(estado)

            destino = states.estado_actual(remito).cancelar(remito)

            self.assertEqual(destino, EstadoRemito.CANCELADO)

    def test_no_se_cancela_despues_de_despachar(self):
        for estado in (
            EstadoRemito.DESPACHADO,
            EstadoRemito.EN_TRANSITO,
            EstadoRemito.RECIBIDO,
            EstadoRemito.CANCELADO,
        ):
            remito = remito_falso(estado)

            with self.assertRaises(TransicionInvalidaError):
                states.estado_actual(remito).cancelar(remito)


class EstadosTerminalesTest(TestCase):
    def test_recibido_y_cancelado_rechazan_todas_las_transiciones(self):
        for estado in (EstadoRemito.RECIBIDO, EstadoRemito.CANCELADO):
            remito = remito_falso(estado)
            clase = states.estado_actual(remito)

            for transicion in TRANSICIONES:
                with self.assertRaises(TransicionInvalidaError, msg=transicion):
                    getattr(clase, transicion)(remito)


class AsignarEjemplarTest(TestCase):
    def test_solo_la_preparacion_admite_asignar(self):
        for estado in EstadoRemito.values:
            remito = remito_falso(estado)
            esperado = estado == EstadoRemito.EN_PREPARACION

            self.assertIs(states.estado_actual(remito).admite_asignar(), esperado)
