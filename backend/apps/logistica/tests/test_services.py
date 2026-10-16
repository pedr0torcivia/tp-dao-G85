import threading
from unittest import skipIf

from django.db import connection
from django.test import TestCase, TransactionTestCase

from apps.catalogo.models import CondicionFisica, Ejemplar, EstadoEjemplar, Libro
from apps.circulacion.models import (
    EstadoSolicitud,
    SolicitudPrestamo,
    TipoSolicitud,
)
from apps.sedes.exceptions import SedeInactivaError
from apps.sedes.models import Sede
from apps.socios.models import EstadoSocio, Socio

from ..exceptions import (
    EjemplarInvalidoError,
    NumeroRemitoDuplicadoError,
    RecepcionInvalidaError,
    RemitoVacioError,
    SedesInvalidasError,
    SocioInhabilitadoError,
    TransicionInvalidaError,
)
from ..models import DetalleRemito, EstadoRemito, EventoRemito, Remito
from ..services import (
    agregar_ejemplar,
    cancelar_remito,
    crear_remito,
    despachar_remito,
    empaquetar_remito,
    recibir_remito,
    registrar_salida_remito,
)


class BaseLogisticaTest(TestCase):
    def setUp(self):
        self.central = Sede.objects.create(
            nombre="Central",
            direccion="Av. 1",
            contacto="central@biblioteca.test",
            horarios="Lunes a viernes de 8 a 18",
        )
        self.norte = Sede.objects.create(
            nombre="Norte",
            direccion="Av. 2",
            contacto="norte@biblioteca.test",
            horarios="Lunes a viernes de 8 a 18",
        )
        self.libro = Libro.objects.create(
            titulo="Rayuela",
            autor="Cortázar",
            editorial="Sudamericana",
            edicion="1",
        )
        self.socio = Socio.objects.create(
            numero_socio="1001",
            documento="30111222",
            nombre="Ana López",
            contacto="ana@test.ar",
        )

    def crear_ejemplar(self, codigo="E-0001", estado=EstadoEjemplar.DISPONIBLE, **cambios):
        datos = {
            "codigo_inventario": codigo,
            "libro": self.libro,
            "sede_propietaria": self.central,
            "sede_actual": self.central,
            "estado": estado,
            "condicion_fisica": CondicionFisica.APTO,
        }
        datos.update(cambios)
        return Ejemplar.objects.create(**datos)

    def crear_solicitud_asignada(self, ejemplar, destino=None):
        return SolicitudPrestamo.objects.create(
            socio=self.socio,
            libro=self.libro,
            ejemplar=ejemplar,
            sede_origen=self.central,
            sede_destino=destino or self.norte,
            tipo=TipoSolicitud.INTERBIBLIOTECARIO,
            estado=EstadoSolicitud.ASIGNADA,
        )


class CrearRemitoTest(BaseLogisticaTest):
    def test_crea_en_preparacion_con_evento_inicial(self):
        remito = crear_remito(
            numero="REM-0001",
            sede_origen_id=self.central.id,
            sede_destino_id=self.norte.id,
        )

        self.assertEqual(remito.estado, EstadoRemito.EN_PREPARACION)
        evento = EventoRemito.objects.get(remito=remito)
        self.assertEqual(evento.estado_nuevo, EstadoRemito.EN_PREPARACION)
        self.assertIsNone(evento.estado_anterior)
        self.assertEqual(evento.observacion, "Remito registrado.")

    def test_normaliza_el_numero(self):
        remito = crear_remito(
            numero="  REM-0002  ",
            sede_origen_id=self.central.id,
            sede_destino_id=self.norte.id,
        )

        self.assertEqual(remito.numero, "REM-0002")

    def test_rechaza_numero_duplicado_sin_distincion_de_mayusculas(self):
        crear_remito(
            numero="REM-0001", sede_origen_id=self.central.id, sede_destino_id=self.norte.id
        )

        with self.assertRaises(NumeroRemitoDuplicadoError):
            crear_remito(
                numero="rem-0001",
                sede_origen_id=self.central.id,
                sede_destino_id=self.norte.id,
            )

    def test_rechaza_origen_igual_al_destino(self):
        with self.assertRaises(SedesInvalidasError):
            crear_remito(
                numero="REM-0003",
                sede_origen_id=self.central.id,
                sede_destino_id=self.central.id,
            )

    def test_rechaza_sede_de_baja(self):
        from apps.sedes.services import dar_de_baja_sede

        dar_de_baja_sede(sede=self.norte)

        with self.assertRaises(SedeInactivaError):
            crear_remito(
                numero="REM-0004",
                sede_origen_id=self.central.id,
                sede_destino_id=self.norte.id,
            )


class AgregarEjemplarTest(BaseLogisticaTest):
    def preparado(self, numero="REM-0010"):
        return crear_remito(
            numero=numero,
            sede_origen_id=self.central.id,
            sede_destino_id=self.norte.id,
        )

    def test_agrega_ejemplar_disponible(self):
        remito = self.preparado()
        ejemplar = self.crear_ejemplar()

        detalle = agregar_ejemplar(remito=remito, ejemplar_id=ejemplar.id)

        self.assertIsNone(detalle.solicitud)
        self.assertEqual(detalle.condicion_salida, CondicionFisica.APTO)
        ejemplar.refresh_from_db()
        self.assertEqual(ejemplar.estado, EstadoEjemplar.ASIGNADO)

    def test_rechaza_remito_no_en_preparacion(self):
        remito = self.preparado()
        agregar_ejemplar(remito=remito, ejemplar_id=self.crear_ejemplar().id)
        empaquetar_remito(remito=remito)
        otro = self.crear_ejemplar(codigo="E-0005")

        with self.assertRaises(TransicionInvalidaError):
            agregar_ejemplar(remito=remito, ejemplar_id=otro.id)

    def test_rechaza_ejemplar_de_otra_sede_o_ubicado_en_otra(self):
        remito = self.preparado()
        ajeno = self.crear_ejemplar(
            codigo="E-0002",
            sede_propietaria=self.norte,
            sede_actual=self.norte,
        )
        ausente = self.crear_ejemplar(codigo="E-0003", sede_actual=self.norte)

        with self.assertRaises(EjemplarInvalidoError):
            agregar_ejemplar(remito=remito, ejemplar_id=ajeno.id)
        with self.assertRaises(EjemplarInvalidoError):
            agregar_ejemplar(remito=remito, ejemplar_id=ausente.id)

    def test_rechaza_ejemplar_en_otro_remito_vigente(self):
        remito_uno = self.preparado("REM-0011")
        remito_dos = self.preparado("REM-0012")
        ejemplar = self.crear_ejemplar()
        agregar_ejemplar(remito=remito_uno, ejemplar_id=ejemplar.id)

        with self.assertRaises(EjemplarInvalidoError):
            agregar_ejemplar(remito=remito_dos, ejemplar_id=ejemplar.id)

    def test_rechaza_ejemplar_no_apto(self):
        remito = self.preparado()
        roto = self.crear_ejemplar(
            codigo="E-0004",
            estado=EstadoEjemplar.EN_REVISION,
            condicion_fisica=CondicionFisica.NO_APTO,
        )

        with self.assertRaises(EjemplarInvalidoError):
            agregar_ejemplar(remito=remito, ejemplar_id=roto.id)

    def test_admite_ejemplar_de_solicitud_interbibliotecaria_hacia_el_destino(self):
        remito = self.preparado()
        ejemplar = self.crear_ejemplar(estado=EstadoEjemplar.ASIGNADO)
        solicitud = self.crear_solicitud_asignada(ejemplar)

        detalle = agregar_ejemplar(remito=remito, ejemplar_id=ejemplar.id)

        self.assertEqual(detalle.solicitud, solicitud)
        ejemplar.refresh_from_db()
        self.assertEqual(ejemplar.estado, EstadoEjemplar.ASIGNADO)

    def test_rechaza_solicitud_interbibliotecaria_con_otro_destino(self):
        sur = Sede.objects.create(
            nombre="Sur",
            direccion="Av. 3",
            contacto="sur@biblioteca.test",
            horarios="Lunes a viernes de 8 a 18",
        )
        remito = self.preparado()
        ejemplar = self.crear_ejemplar(estado=EstadoEjemplar.ASIGNADO)
        self.crear_solicitud_asignada(ejemplar, destino=sur)

        with self.assertRaises(EjemplarInvalidoError):
            agregar_ejemplar(remito=remito, ejemplar_id=ejemplar.id)


class EmpaquetarTest(BaseLogisticaTest):
    def test_transiciona_y_registra_evento(self):
        remito = crear_remito(
            numero="REM-0020",
            sede_origen_id=self.central.id,
            sede_destino_id=self.norte.id,
        )
        agregar_ejemplar(remito=remito, ejemplar_id=self.crear_ejemplar().id)

        remito = empaquetar_remito(
            remito=remito,
            responsable="Martín",
            observacion="Cerrado con cinta",
        )

        self.assertEqual(remito.estado, EstadoRemito.EMPAQUETADO)
        eventos = EventoRemito.objects.filter(remito=remito).order_by("fecha_hora", "id")
        self.assertEqual(eventos.count(), 2)
        ultimo = eventos.last()
        self.assertEqual(ultimo.estado_anterior, EstadoRemito.EN_PREPARACION)
        self.assertEqual(ultimo.estado_nuevo, EstadoRemito.EMPAQUETADO)
        self.assertEqual(ultimo.responsable, "Martín")
        self.assertEqual(ultimo.observacion, "Cerrado con cinta")

    def test_rechaza_remito_vacio_sin_dejar_evento(self):
        remito = crear_remito(
            numero="REM-0021",
            sede_origen_id=self.central.id,
            sede_destino_id=self.norte.id,
        )

        with self.assertRaises(RemitoVacioError):
            empaquetar_remito(remito=remito)

        self.assertEqual(EventoRemito.objects.filter(remito=remito).count(), 1)
        remito.refresh_from_db()
        self.assertEqual(remito.estado, EstadoRemito.EN_PREPARACION)

    def test_rechaza_con_sede_de_baja(self):
        from apps.sedes.services import dar_de_baja_sede

        remito = crear_remito(
            numero="REM-0022",
            sede_origen_id=self.central.id,
            sede_destino_id=self.norte.id,
        )
        agregar_ejemplar(remito=remito, ejemplar_id=self.crear_ejemplar().id)
        dar_de_baja_sede(sede=self.norte)

        with self.assertRaises(SedeInactivaError):
            empaquetar_remito(remito=remito)


class CancelarRemitoTest(BaseLogisticaTest):
    def preparado(self, numero="REM-0030"):
        remito = crear_remito(
            numero=numero,
            sede_origen_id=self.central.id,
            sede_destino_id=self.norte.id,
        )
        agregar_ejemplar(remito=remito, ejemplar_id=self.crear_ejemplar().id)
        agregado = self.crear_ejemplar(codigo="E-0009")
        agregar_ejemplar(remito=remito, ejemplar_id=agregado.id)
        return remito

    def test_cancela_libera_ejemplares_sin_solicitud_y_registra_evento(self):
        remito = self.preparado()

        remito = cancelar_remito(remito=remito, responsable="Ana", observacion="Error de carga")

        self.assertEqual(remito.estado, EstadoRemito.CANCELADO)
        for detalle in remito.detalles.select_related("ejemplar"):
            self.assertEqual(detalle.ejemplar.estado, EstadoEjemplar.DISPONIBLE)
        ultimo = EventoRemito.objects.filter(remito=remito).order_by("id").last()
        self.assertEqual(ultimo.estado_nuevo, EstadoRemito.CANCELADO)

    def test_mantiene_ejemplares_vinculados_a_solicitudes(self):
        remito = crear_remito(
            numero="REM-0031",
            sede_origen_id=self.central.id,
            sede_destino_id=self.norte.id,
        )
        ejemplar = self.crear_ejemplar(estado=EstadoEjemplar.ASIGNADO)
        self.crear_solicitud_asignada(ejemplar)
        agregar_ejemplar(remito=remito, ejemplar_id=ejemplar.id)

        cancelar_remito(remito=remito)

        ejemplar.refresh_from_db()
        self.assertEqual(ejemplar.estado, EstadoEjemplar.ASIGNADO)

    def test_no_se_cancela_despues_de_despachar(self):
        remito = self.preparado()
        Remito.objects.filter(pk=remito.pk).update(estado=EstadoRemito.DESPACHADO)
        remito.refresh_from_db()

        with self.assertRaises(TransicionInvalidaError):
            cancelar_remito(remito=remito)

    def test_cancela_aunque_las_sedes_esten_de_baja(self):
        from apps.sedes.services import dar_de_baja_sede

        remito = self.preparado()
        dar_de_baja_sede(sede=self.central)

        remito = cancelar_remito(remito=remito)

        self.assertEqual(remito.estado, EstadoRemito.CANCELADO)


class DespacharTest(BaseLogisticaTest):
    def preparado(self, numero="REM-0040"):
        remito = crear_remito(
            numero=numero,
            sede_origen_id=self.central.id,
            sede_destino_id=self.norte.id,
        )
        agregar_ejemplar(remito=remito, ejemplar_id=self.crear_ejemplar().id)
        empaquetar_remito(remito=remito)
        return remito

    def test_despacha_y_manda_ejemplares_en_transito(self):
        remito = self.preparado()
        detalle = remito.detalles.first()
        detalle.solicitud = self.crear_solicitud_asignada(detalle.ejemplar)
        detalle.save()

        remito = despachar_remito(remito=remito, responsable="Logística")

        self.assertEqual(remito.estado, EstadoRemito.DESPACHADO)
        self.assertIsNotNone(remito.fecha_despacho)
        detalle.ejemplar.refresh_from_db()
        self.assertEqual(detalle.ejemplar.estado, EstadoEjemplar.EN_TRANSITO)
        self.assertIsNone(detalle.ejemplar.sede_actual)
        detalle.solicitud.refresh_from_db()
        self.assertEqual(detalle.solicitud.estado, EstadoSolicitud.EN_TRASLADO)

    def test_rechaza_con_socio_inhabilitado_y_no_deja_cambios(self):
        remito = self.preparado()
        detalle = remito.detalles.first()
        detalle.solicitud = self.crear_solicitud_asignada(detalle.ejemplar)
        detalle.save()
        self.socio.estado = EstadoSocio.INHABILITADO
        self.socio.save()

        with self.assertRaises(SocioInhabilitadoError):
            despachar_remito(remito=remito)

        detalle.ejemplar.refresh_from_db()
        self.assertEqual(detalle.ejemplar.estado, EstadoEjemplar.ASIGNADO)
        self.assertIsNotNone(detalle.ejemplar.sede_actual)

    def test_rechaza_con_sede_de_baja(self):
        from apps.sedes.services import dar_de_baja_sede

        remito = self.preparado()
        dar_de_baja_sede(sede=self.norte)

        with self.assertRaises(SedeInactivaError):
            despachar_remito(remito=remito)


class RegistrarSalidaTest(BaseLogisticaTest):
    def test_solo_despues_de_despachar(self):
        remito = crear_remito(
            numero="REM-0050",
            sede_origen_id=self.central.id,
            sede_destino_id=self.norte.id,
        )
        agregar_ejemplar(remito=remito, ejemplar_id=self.crear_ejemplar().id)
        empaquetar_remito(remito=remito)

        with self.assertRaises(TransicionInvalidaError):
            registrar_salida_remito(remito=remito)

        despachar_remito(remito=remito)
        remito = registrar_salida_remito(remito=remito, responsable="Transporte")

        self.assertEqual(remito.estado, EstadoRemito.EN_TRANSITO)


class RecibirTest(BaseLogisticaTest):
    def en_transito(self, numero="REM-0060"):
        remito = crear_remito(
            numero=numero,
            sede_origen_id=self.central.id,
            sede_destino_id=self.norte.id,
        )
        agregar_ejemplar(remito=remito, ejemplar_id=self.crear_ejemplar().id)
        empaquetar_remito(remito=remito)
        despachar_remito(remito=remito)
        registrar_salida_remito(remito=remito)
        return remito

    def test_recibe_con_solicitud_y_deja_listo_para_entrega(self):
        remito = self.en_transito()
        detalle = remito.detalles.first()
        detalle.solicitud = self.crear_solicitud_asignada(detalle.ejemplar)
        detalle.save()
        despacho = EventoRemito.objects.filter(remito=remito).count()

        remito = recibir_remito(
            remito=remito, verificados=[detalle.ejemplar_id], responsable="Personal Norte"
        )

        self.assertEqual(remito.estado, EstadoRemito.RECIBIDO)
        self.assertIsNotNone(remito.fecha_recepcion)
        detalle.ejemplar.refresh_from_db()
        self.assertEqual(detalle.ejemplar.sede_actual_id, self.norte.id)
        self.assertEqual(detalle.ejemplar.sede_propietaria_id, self.central.id)
        self.assertEqual(detalle.ejemplar.estado, EstadoEjemplar.LISTO_PARA_ENTREGA)
        detalle.solicitud.refresh_from_db()
        self.assertEqual(detalle.solicitud.estado, EstadoSolicitud.LISTA_PARA_ENTREGA)
        detalle.refresh_from_db()
        self.assertEqual(detalle.condicion_recepcion, detalle.ejemplar.condicion_fisica)
        self.assertEqual(EventoRemito.objects.filter(remito=remito).count(), despacho + 1)

    def test_recibe_stock_sin_solicitud_y_queda_en_revision(self):
        remito = self.en_transito()
        detalle = remito.detalles.first()

        recibir_remito(
            remito=remito, verificados=[detalle.ejemplar_id], responsable="Personal Norte"
        )

        detalle.ejemplar.refresh_from_db()
        self.assertEqual(detalle.ejemplar.estado, EstadoEjemplar.EN_REVISION)
        self.assertEqual(detalle.ejemplar.sede_actual_id, self.norte.id)

    def test_rechaza_recepcion_incompleta_sin_dejar_cambios(self):
        remito = self.en_transito()
        detalle = remito.detalles.first()

        with self.assertRaises(RecepcionInvalidaError):
            recibir_remito(remito=remito, verificados=[], responsable="Personal Norte")

        remito.refresh_from_db()
        self.assertEqual(remito.estado, EstadoRemito.EN_TRANSITO)
        self.assertIsNone(remito.fecha_recepcion)
        detalle.ejemplar.refresh_from_db()
        self.assertEqual(detalle.ejemplar.estado, EstadoEjemplar.EN_TRANSITO)

    def test_rechaza_recepcion_sin_responsable(self):
        remito = self.en_transito()
        detalle = remito.detalles.first()

        with self.assertRaises(RecepcionInvalidaError):
            recibir_remito(remito=remito, verificados=[detalle.ejemplar_id], responsable="  ")

    def test_rechaza_recepcion_desde_empaquetado(self):
        remito = crear_remito(
            numero="REM-0061",
            sede_origen_id=self.central.id,
            sede_destino_id=self.norte.id,
        )
        agregar_ejemplar(remito=remito, ejemplar_id=self.crear_ejemplar().id)
        empaquetar_remito(remito=remito)
        detalle = remito.detalles.first()

        with self.assertRaises(TransicionInvalidaError):
            recibir_remito(
                remito=remito, verificados=[detalle.ejemplar_id], responsable="Personal Norte"
            )


class CicloCompletoTest(BaseLogisticaTest):
    """Porta el recorrido de workflows.test.ts del frontend."""

    def test_recorrido_completo_del_remito(self):
        remito = crear_remito(
            numero="REM-CICLO",
            sede_origen_id=self.central.id,
            sede_destino_id=self.norte.id,
        )
        ejemplar = self.crear_ejemplar(estado=EstadoEjemplar.ASIGNADO)
        self.crear_solicitud_asignada(ejemplar)
        agregar_ejemplar(remito=remito, ejemplar_id=ejemplar.id)

        empaquetar_remito(remito=remito)
        despachar_remito(remito=remito)

        ejemplar.refresh_from_db()
        self.assertIsNone(ejemplar.sede_actual_id)
        self.assertEqual(ejemplar.sede_propietaria_id, self.central.id)

        with self.assertRaises(TransicionInvalidaError):
            cancelar_remito(remito=remito)

        registrar_salida_remito(remito=remito)

        with self.assertRaises(RecepcionInvalidaError):
            recibir_remito(remito=remito, verificados=[], responsable="Personal Norte")

        recibir_remito(remito=remito, verificados=[ejemplar.id], responsable="Personal Sur")

        ejemplar.refresh_from_db()
        self.assertEqual(ejemplar.sede_actual_id, self.norte.id)
        self.assertEqual(ejemplar.sede_propietaria_id, self.central.id)

        estados = list(
            EventoRemito.objects.filter(remito=remito)
            .order_by("fecha_hora", "id")
            .values_list("estado_nuevo", flat=True)
        )
        self.assertEqual(
            estados,
            [
                EstadoRemito.EN_PREPARACION,
                EstadoRemito.EMPAQUETADO,
                EstadoRemito.DESPACHADO,
                EstadoRemito.EN_TRANSITO,
                EstadoRemito.RECIBIDO,
            ],
        )


@skipIf(connection.vendor == "sqlite", "El bloqueo real requiere PostgreSQL")
class ConcurrenciaTest(TransactionTestCase):
    def setUp(self):
        self.central = Sede.objects.create(
            nombre="Central",
            direccion="Av. 1",
            contacto="central@biblioteca.test",
            horarios="Lunes a viernes de 8 a 18",
        )
        self.norte = Sede.objects.create(
            nombre="Norte",
            direccion="Av. 2",
            contacto="norte@biblioteca.test",
            horarios="Lunes a viernes de 8 a 18",
        )
        libro = Libro.objects.create(
            titulo="Rayuela",
            autor="Cortázar",
            editorial="Sudamericana",
            edicion="1",
        )
        self.ejemplar = Ejemplar.objects.create(
            codigo_inventario="E-C001",
            libro=libro,
            sede_propietaria=self.central,
            sede_actual=self.central,
            estado=EstadoEjemplar.DISPONIBLE,
            condicion_fisica=CondicionFisica.APTO,
        )

    def test_dos_remitos_no_asignan_el_mismo_ejemplar(self):
        remito_uno = crear_remito(
            numero="REM-C01",
            sede_origen_id=self.central.id,
            sede_destino_id=self.norte.id,
        )
        remito_dos = crear_remito(
            numero="REM-C02",
            sede_origen_id=self.central.id,
            sede_destino_id=self.norte.id,
        )
        ejemplar = self.ejemplar
        resultados = []
        barrera = threading.Barrier(2)

        def intentar(remito):
            try:
                barrera.wait(timeout=10)
                agregar_ejemplar(remito=remito, ejemplar_id=ejemplar.id)
                resultados.append("ok")
            except Exception as error:  # noqa: BLE001
                resultados.append(error)
            finally:
                connection.close()

        hilo_uno = threading.Thread(target=intentar, args=(remito_uno,))
        hilo_dos = threading.Thread(target=intentar, args=(remito_dos,))
        hilo_uno.start()
        hilo_dos.start()
        hilo_uno.join()
        hilo_dos.join()

        self.assertEqual(resultados.count("ok"), 1, resultados)
        self.assertEqual(DetalleRemito.objects.count(), 1)
