"""Pruebas del patrón State: cada clase concreta admite sólo sus operaciones."""

from django.test import TestCase

from apps.catalogo.models import CondicionFisica, Ejemplar, EstadoEjemplar, Libro
from apps.logistica import states
from apps.logistica.exceptions import RemitoVacioError, TransicionInvalidaError
from apps.logistica.models import EstadoRemito, EventoRemito, Remito
from apps.sedes.models import Sede

ESPERADAS = {
    EstadoRemito.EN_PREPARACION: ["agregar", "quitar", "empaquetar", "cancelar"],
    EstadoRemito.EMPAQUETADO: ["reabrir", "despachar", "cancelar"],
    EstadoRemito.EN_TRANSITO: ["recibir"],
    EstadoRemito.RECIBIDO: [],
    EstadoRemito.RECIBIDO_CON_INCIDENCIAS: [],
    EstadoRemito.CANCELADO: [],
}


class RegistroEstadosTest(TestCase):
    def test_hay_una_clase_por_estado_persistido(self):
        self.assertEqual(set(states.ESTADOS_REMITO), set(EstadoRemito.values))

    def test_cada_clase_declara_su_valor_persistido(self):
        for valor, objeto in states.ESTADOS_REMITO.items():
            self.assertEqual(objeto.codigo, valor)
            self.assertIsInstance(objeto, states.EstadoRemitoBase)

    def test_cada_estado_expone_exactamente_sus_operaciones(self):
        for valor, esperadas in ESPERADAS.items():
            self.assertEqual(
                states.ESTADOS_REMITO[valor].operaciones_admitidas(), esperadas, msg=valor
            )

    def test_los_estados_finales_se_declaran_como_tales(self):
        finales = {v for v, o in states.ESTADOS_REMITO.items() if o.es_final}
        self.assertEqual(
            finales,
            {
                EstadoRemito.RECIBIDO,
                EstadoRemito.RECIBIDO_CON_INCIDENCIAS,
                EstadoRemito.CANCELADO,
            },
        )


class TransicionesTest(TestCase):
    def setUp(self):
        self.central = Sede.objects.create(
            nombre="Central", direccion="A", contacto="c", horarios="h"
        )
        self.norte = Sede.objects.create(nombre="Norte", direccion="B", contacto="n", horarios="h")
        libro = Libro.objects.create(titulo="Ficciones", autor="Borges", editorial="E", edicion="1")
        self.ejemplar = Ejemplar.objects.create(
            codigo_inventario="E-1",
            libro=libro,
            sede_propietaria=self.central,
            sede_actual=self.central,
            estado=EstadoEjemplar.ASIGNADO,
            condicion_fisica=CondicionFisica.APTO,
        )

    def remito(self, estado, con_detalle=True):
        remito = Remito.objects.create(
            numero=f"R-{estado}", sede_origen=self.central, sede_destino=self.norte, estado=estado
        )
        if con_detalle:
            remito.detalles.create(ejemplar=self.ejemplar, condicion_salida=CondicionFisica.APTO)
        return remito

    def test_el_contexto_delega_en_la_clase_de_su_estado(self):
        remito = self.remito(EstadoRemito.EMPAQUETADO)
        self.assertIsInstance(remito.comportamiento, states.Empaquetado)

    def test_empaquetar_cambia_el_estado_y_deja_evento(self):
        remito = self.remito(EstadoRemito.EN_PREPARACION)
        remito.comportamiento.empaquetar(remito, responsable="Ana")
        self.assertEqual(remito.estado, EstadoRemito.EMPAQUETADO)
        evento = EventoRemito.objects.get(remito=remito)
        self.assertEqual(
            (evento.estado_anterior, evento.estado_nuevo, evento.responsable),
            (EstadoRemito.EN_PREPARACION, EstadoRemito.EMPAQUETADO, "Ana"),
        )

    def test_no_se_empaqueta_un_remito_vacio(self):
        remito = self.remito(EstadoRemito.EN_PREPARACION, con_detalle=False)
        with self.assertRaises(RemitoVacioError):
            remito.comportamiento.empaquetar(remito, responsable="Ana")

    def test_reabrir_vuelve_a_preparacion(self):
        remito = self.remito(EstadoRemito.EMPAQUETADO)
        remito.comportamiento.reabrir(remito, responsable="Ana")
        self.assertEqual(remito.estado, EstadoRemito.EN_PREPARACION)

    def test_despachar_pone_el_material_en_transito(self):
        remito = self.remito(EstadoRemito.EMPAQUETADO)
        remito.comportamiento.despachar(remito, responsable="Ana")
        self.assertEqual(remito.estado, EstadoRemito.EN_TRANSITO)
        self.assertIsNotNone(remito.fecha_despacho)
        self.ejemplar.refresh_from_db()
        self.assertEqual(self.ejemplar.estado, EstadoEjemplar.EN_TRANSITO)
        self.assertIsNone(self.ejemplar.sede_actual)

    def test_cada_estado_rechaza_lo_que_no_admite(self):
        llamadas = {
            "empaquetar": lambda e, r: e.empaquetar(r, responsable="x"),
            "reabrir": lambda e, r: e.reabrir(r, responsable="x"),
            "despachar": lambda e, r: e.despachar(r, responsable="x"),
            "cancelar": lambda e, r: e.cancelar(r, responsable="x"),
            "recibir": lambda e, r: e.recibir(r, resultados={}, responsable="x"),
        }
        for valor, admitidas in ESPERADAS.items():
            for operacion, llamar in llamadas.items():
                if operacion in admitidas:
                    continue
                remito = Remito(estado=valor)
                with self.assertRaises(TransicionInvalidaError, msg=f"{valor}.{operacion}"):
                    llamar(states.ESTADOS_REMITO[valor], remito)
