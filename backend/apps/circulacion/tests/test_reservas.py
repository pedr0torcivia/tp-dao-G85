from datetime import datetime

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.catalogo.models import CondicionFisica, Ejemplar, EstadoEjemplar, Libro
from apps.circulacion.models import EstadoReserva, EstadoSolicitud, Reserva, SolicitudPrestamo
from apps.circulacion.services import (
    asignar_reserva,
    cancelar_reserva,
    crear_reserva,
    expirar_reserva,
)
from apps.sedes.models import EstadoSede, Sede
from apps.socios.models import EstadoSocio, Socio


def _momento(dia: int, hora: int = 12) -> datetime:
    return timezone.make_aware(datetime(2026, 10, dia, hora))


def _futuro() -> datetime:
    return timezone.now() + timezone.timedelta(days=5)


class BaseReservasTest(TestCase):
    def setUp(self):
        self.central = Sede.objects.create(
            nombre="Central",
            direccion="Av. 1",
            contacto="c@sede.test",
            horarios="Lunes a viernes de 8 a 18",
        )
        self.norte = Sede.objects.create(
            nombre="Norte",
            direccion="Av. 2",
            contacto="n@sede.test",
            horarios="Lunes a viernes de 8 a 18",
        )
        self.socio = Socio.objects.create(
            numero_socio="SOC-001",
            documento="30111222",
            nombre="Agustín Pereira",
            contacto="socio@correo.test",
        )
        self.libro = Libro.objects.create(
            isbn="9780000000001",
            titulo="El principito",
            autor="Antoine de Saint-Exupéry",
            editorial="Salamandra",
            edicion="1",
        )
        self.ejemplar = Ejemplar.objects.create(
            codigo_inventario="EJ-0001",
            libro=self.libro,
            sede_propietaria=self.central,
            sede_actual=self.central,
        )

    def crear_reserva(self, **cambios):
        datos = {
            "socio": self.socio,
            "libro": self.libro,
            "sede_retiro": self.central,
        }
        datos.update(cambios)
        return crear_reserva(**datos)

    def crear_ejemplar(self, sede_actual=None) -> Ejemplar:
        codigo = f"EJ-{Ejemplar.objects.count() + 1:04d}"
        return Ejemplar.objects.create(
            codigo_inventario=codigo,
            libro=self.libro,
            sede_propietaria=self.central,
            sede_actual=sede_actual or self.central,
        )


class ReservasServicesTest(BaseReservasTest):
    def test_la_reserva_comienza_pendiente(self):
        reserva = self.crear_reserva()

        self.assertEqual(reserva.estado, EstadoReserva.PENDIENTE)
        self.assertIsNone(reserva.ejemplar_asignado)

    def test_rechaza_sede_de_baja(self):
        Sede.objects.filter(pk=self.central.pk).update(estado=EstadoSede.BAJA)
        self.central.refresh_from_db()

        from apps.sedes.exceptions import SedeInactivaError

        with self.assertRaises(SedeInactivaError):
            self.crear_reserva()

    def test_rechaza_reserva_vigente_duplicada(self):
        from apps.circulacion.exceptions import ReservaVigenteDuplicadaError

        self.crear_reserva()

        with self.assertRaises(ReservaVigenteDuplicadaError):
            self.crear_reserva()

    def test_permite_otra_reserva_si_la_anterior_esta_cerrada(self):
        reserva = self.crear_reserva()
        cancelada = cancelar_reserva(reserva=reserva)
        self.assertEqual(cancelada.estado, EstadoReserva.CANCELADA)

        segunda = self.crear_reserva()
        self.assertEqual(segunda.estado, EstadoReserva.PENDIENTE)

    def test_asignar_deja_listo_para_retiro_y_genera_solicitud(self):
        reserva = self.crear_reserva()

        asignar_reserva(
            reserva=reserva,
            ejemplar=self.ejemplar,
            fecha_limite_retiro=_futuro(),
        )

        reserva.refresh_from_db()
        self.ejemplar.refresh_from_db()
        self.assertEqual(reserva.estado, EstadoReserva.LISTA_PARA_RETIRO)
        self.assertEqual(reserva.ejemplar_asignado, self.ejemplar)
        self.assertEqual(self.ejemplar.estado, EstadoEjemplar.LISTO_PARA_ENTREGA)

        solicitud = SolicitudPrestamo.objects.get(reserva=reserva)
        self.assertEqual(solicitud.tipo, "LOCAL")
        self.assertEqual(solicitud.estado, EstadoSolicitud.LISTA_PARA_ENTREGA)
        self.assertEqual(solicitud.sede_origen, self.central)

    def test_asignar_requiere_reserva_pendiente(self):
        from apps.circulacion.exceptions import EstadoReservaInvalidoError

        reserva = self.crear_reserva()
        cancelar_reserva(reserva=reserva)

        with self.assertRaises(EstadoReservaInvalidoError):
            asignar_reserva(
                reserva=reserva,
                ejemplar=self.ejemplar,
                fecha_limite_retiro=_futuro(),
            )

    def test_asignar_requiere_socio_habilitado(self):
        from apps.circulacion.exceptions import SocioInhabilitadoError

        reserva = self.crear_reserva()
        Socio.objects.filter(pk=self.socio.pk).update(estado=EstadoSocio.INHABILITADO)
        self.socio.refresh_from_db()

        with self.assertRaises(SocioInhabilitadoError):
            asignar_reserva(
                reserva=reserva,
                ejemplar=self.ejemplar,
                fecha_limite_retiro=_futuro(),
            )

    def test_asignar_requiere_ejemplar_disponible_y_aptos(self):
        from apps.circulacion.exceptions import EjemplarNoDisponibleError

        reserva = self.crear_reserva()
        self.ejemplar.condicion_fisica = CondicionFisica.NO_APTO
        self.ejemplar.save()

        with self.assertRaises(EjemplarNoDisponibleError):
            asignar_reserva(
                reserva=reserva,
                ejemplar=self.ejemplar,
                fecha_limite_retiro=_futuro(),
            )

    def test_asignar_requiere_ejemplar_del_libro_reservado(self):
        from apps.circulacion.exceptions import EjemplarNoCorrespondeError

        reserva = self.crear_reserva()
        otro_libro = Libro.objects.create(
            isbn="9780000000002",
            titulo="Don Quijote",
            autor="Miguel de Cervantes",
            editorial="Austral",
            edicion="2",
        )
        otro = Ejemplar.objects.create(
            codigo_inventario="EJ-0002",
            libro=otro_libro,
            sede_propietaria=self.central,
            sede_actual=self.central,
        )

        with self.assertRaises(EjemplarNoCorrespondeError):
            asignar_reserva(
                reserva=reserva,
                ejemplar=otro,
                fecha_limite_retiro=_futuro(),
            )

    def test_asignar_requiere_ejemplar_en_la_sede_de_retiro(self):
        from apps.circulacion.exceptions import EjemplarEnOtraSedeError

        # Reserva de retiro en Norte; el ejemplar apto está en su sede (Central)
        reserva = self.crear_reserva(sede_retiro=self.norte)
        en_central = self.crear_ejemplar()

        with self.assertRaises(EjemplarEnOtraSedeError):
            asignar_reserva(
                reserva=reserva,
                ejemplar=en_central,
                fecha_limite_retiro=_futuro(),
            )

    def test_asignar_requiere_ejemplar_disponible(self):
        from apps.circulacion.exceptions import EjemplarNoDisponibleError

        reserva = self.crear_reserva()
        en_otra_sede = self.crear_ejemplar(sede_actual=self.norte)  # no está en su sede

        with self.assertRaises(EjemplarNoDisponibleError):
            asignar_reserva(
                reserva=reserva,
                ejemplar=en_otra_sede,
                fecha_limite_retiro=_futuro(),
            )

    def test_asignar_requiere_fecha_limite_futura(self):
        from apps.circulacion.exceptions import FechaLimiteRetiroInvalidaError

        reserva = self.crear_reserva()

        with self.assertRaises(FechaLimiteRetiroInvalidaError):
            asignar_reserva(
                reserva=reserva,
                ejemplar=self.ejemplar,
                fecha_limite_retiro=timezone.now() - timezone.timedelta(days=1),
            )

        with self.assertRaises(FechaLimiteRetiroInvalidaError):
            asignar_reserva(
                reserva=reserva,
                ejemplar=self.ejemplar,
                fecha_limite_retiro=None,
            )

    def test_cerrar_reserva_libera_el_ejemplar_y_cancela_la_solicitud(self):
        reserva = self.crear_reserva()
        asignar_reserva(
            reserva=reserva,
            ejemplar=self.ejemplar,
            fecha_limite_retiro=_futuro(),
        )

        cancelar_reserva(reserva=reserva)

        reserva.refresh_from_db()
        self.ejemplar.refresh_from_db()
        self.assertEqual(reserva.estado, EstadoReserva.CANCELADA)
        self.assertEqual(self.ejemplar.estado, EstadoEjemplar.DISPONIBLE)
        self.assertEqual(
            SolicitudPrestamo.objects.get(reserva=reserva).estado,
            EstadoSolicitud.CANCELADA,
        )

    def test_expirar_exige_plazo_vencido(self):
        from apps.circulacion.exceptions import EstadoReservaInvalidoError

        reserva = self.crear_reserva()

        # PENDIENTE: todavía no venció el plazo (ni siquiera existe)
        with self.assertRaises(EstadoReservaInvalidoError):
            expirar_reserva(reserva=reserva)

        # Asignada con plazo futuro: tampoco
        asignar_reserva(
            reserva=reserva,
            ejemplar=self.ejemplar,
            fecha_limite_retiro=_futuro(),
        )
        with self.assertRaises(EstadoReservaInvalidoError):
            expirar_reserva(reserva=reserva)

        # Con el plazo pasado, expira y libera el ejemplar.
        # (El CHECK exige límite > fecha_reserva, así que se atrasan ambas.)
        Reserva.objects.filter(pk=reserva.pk).update(
            fecha_reserva=_momento(1),
            fecha_limite_retiro=_momento(2),
        )
        reserva.refresh_from_db()
        expirar_reserva(reserva=reserva)

        reserva.refresh_from_db()
        self.ejemplar.refresh_from_db()
        self.assertEqual(reserva.estado, EstadoReserva.EXPIRADA)
        self.assertEqual(self.ejemplar.estado, EstadoEjemplar.DISPONIBLE)


class ReservasApiTest(APITestCase, BaseReservasTest):
    def test_flujo_completo_de_reserva_por_http(self):
        response = self.client.post(
            reverse("reserva-list"),
            {
                "socio_id": self.socio.pk,
                "libro_id": self.libro.pk,
                "sede_retiro_id": self.central.pk,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["estado"], EstadoReserva.PENDIENTE)
        reserva_id = response.data["id"]

        response = self.client.post(
            reverse("reserva-asignar", args=[reserva_id]),
            {
                "ejemplar_id": self.ejemplar.pk,
                "fecha_limite_retiro": (_futuro().isoformat()),
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["estado"], EstadoReserva.LISTA_PARA_RETIRO)

        response = self.client.post(reverse("reserva-cancelar", args=[reserva_id]), {})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["estado"], EstadoReserva.CANCELADA)

    def test_asignar_con_fecha_pasada_devuelve_error_de_campo(self):
        reserva = self.crear_reserva()

        response = self.client.post(
            reverse("reserva-asignar", args=[reserva.pk]),
            {
                "ejemplar_id": self.ejemplar.pk,
                "fecha_limite_retiro": "2020-01-01T10:00:00Z",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(
            "fecha_limite_retiro",
            response.data["error"]["detail"],
        )

    def test_duplicada_devuelve_400_por_http(self):
        self.crear_reserva()

        response = self.client.post(
            reverse("reserva-list"),
            {
                "socio_id": self.socio.pk,
                "libro_id": self.libro.pk,
                "sede_retiro_id": self.central.pk,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
