from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from apps.catalogo.models import EstadoEjemplar
from apps.circulacion.exceptions import (
    EstadoSolicitudInvalidoError,
    SolicitudEnRemitoVigenteError,
)
from apps.circulacion.models import EstadoSolicitud, TipoSolicitud
from apps.circulacion.services import (
    asignar_ejemplar,
    cancelar_solicitud,
    crear_solicitud,
    entregar_solicitud,
    preparar_entrega,
)
from apps.logistica.models import DetalleRemito, Remito

from .factories import crear_ejemplar, crear_libro, crear_sede, crear_socio


class CirculacionInterbibliotecariaTest(TestCase):
    def setUp(self):
        self.origen = crear_sede(nombre="Origen")
        self.destino = crear_sede(nombre="Destino")
        self.socio = crear_socio()
        self.libro = crear_libro()
        self.ejemplar = crear_ejemplar(
            libro=self.libro,
            sede=self.origen,
        )
        self.solicitud = crear_solicitud(
            socio=self.socio,
            libro=self.libro,
            sede_origen=self.origen,
            sede_destino=self.destino,
            tipo=TipoSolicitud.INTERBIBLIOTECARIO,
        )
        asignar_ejemplar(
            solicitud=self.solicitud,
            ejemplar=self.ejemplar,
        )

    def test_preparar_incorpora_el_ejemplar_a_un_remito_hacia_el_destino(self):
        from apps.logistica.models import DetalleRemito

        preparar_entrega(solicitud=self.solicitud)

        detalle = DetalleRemito.objects.get(solicitud=self.solicitud)
        self.assertEqual(detalle.ejemplar_id, self.ejemplar.pk)
        self.assertEqual(detalle.remito.sede_origen_id, self.origen.pk)
        self.assertEqual(detalle.remito.sede_destino_id, self.destino.pk)
        with self.assertRaises(EstadoSolicitudInvalidoError):
            preparar_entrega(solicitud=self.solicitud)

    def test_contrato_de_recepcion_habilita_la_entrega(self):
        self.solicitud.estado = EstadoSolicitud.EN_TRASLADO
        self.solicitud.save(update_fields=["estado"])
        self.ejemplar.estado = EstadoEjemplar.EN_TRANSITO
        self.ejemplar.sede_actual = None
        self.ejemplar.save(update_fields=["estado", "sede_actual"])

        # Este cambio representa el resultado contractual de recibir el remito.
        self.solicitud.estado = EstadoSolicitud.LISTA_PARA_ENTREGA
        self.solicitud.save(update_fields=["estado"])
        self.ejemplar.estado = EstadoEjemplar.LISTO_PARA_ENTREGA
        self.ejemplar.sede_actual = self.destino
        self.ejemplar.save(update_fields=["estado", "sede_actual"])

        ahora = timezone.now()
        prestamo = entregar_solicitud(
            solicitud=self.solicitud,
            fecha_entrega=ahora,
            fecha_vencimiento=ahora + timedelta(days=14),
        )
        self.assertIsNotNone(prestamo.pk)

    def _en_remito(self, estado):
        remito = Remito.objects.create(
            numero="REM-001",
            sede_origen=self.origen,
            sede_destino=self.destino,
            estado=estado,
        )
        DetalleRemito.objects.create(
            remito=remito,
            ejemplar=self.ejemplar,
            solicitud=self.solicitud,
            condicion_salida=self.ejemplar.condicion_fisica,
        )
        return remito

    def test_cancelar_quita_el_libro_del_remito_en_preparacion(self):
        remito = self._en_remito("EN_PREPARACION")

        solicitud = cancelar_solicitud(solicitud=self.solicitud)

        self.assertEqual(solicitud.estado, "CANCELADA")
        self.assertFalse(remito.detalles.exists())
        self.ejemplar.refresh_from_db()
        self.assertEqual(self.ejemplar.estado, "DISPONIBLE")

    def test_no_cancela_si_el_remito_ya_esta_empaquetado(self):
        self._en_remito("EMPAQUETADO")
        with self.assertRaises(SolicitudEnRemitoVigenteError):
            cancelar_solicitud(solicitud=self.solicitud)
