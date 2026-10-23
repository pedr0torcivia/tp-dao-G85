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

    def test_no_se_prepara_como_solicitud_local(self):
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

    def test_no_cancela_solicitud_en_remito_vigente(self):
        remito = Remito.objects.create(
            numero="REM-001",
            sede_origen=self.origen,
            sede_destino=self.destino,
        )
        DetalleRemito.objects.create(
            remito=remito,
            ejemplar=self.ejemplar,
            solicitud=self.solicitud,
            condicion_salida=self.ejemplar.condicion_fisica,
        )
        with self.assertRaises(SolicitudEnRemitoVigenteError):
            cancelar_solicitud(solicitud=self.solicitud)
