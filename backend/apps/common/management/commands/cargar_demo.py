"""Datos estables y no destructivos para la demostración y los cuatro reportes."""

from datetime import datetime

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.catalogo.models import Ejemplar, Libro
from apps.circulacion.models import Prestamo, Reserva, SolicitudPrestamo
from apps.logistica.models import DetalleRemito, EventoRemito, Remito
from apps.sedes.models import Sede
from apps.socios.models import Socio


def momento(dia):
    return timezone.make_aware(datetime(2026, 10, dia, 12))


class Command(BaseCommand):
    help = "Carga ejemplos del grupo 85 una sola vez, sin borrar ni restablecer datos."

    @transaction.atomic
    def handle(self, *args, **options):
        usuario, creado = get_user_model().objects.get_or_create(
            username="biblioteca",
            defaults={"first_name": "Personal de biblioteca", "is_staff": True},
        )
        if creado:
            usuario.set_password("demo")
            usuario.save(update_fields=["password"])
            self.stdout.write("Cuenta de demostración creada: biblioteca / demo.")
        if Ejemplar.objects.filter(codigo_inventario="EXPO-001").exists():
            self.stdout.write("Se conserva el catálogo preparado para la exposición.")
            return
        if Sede.objects.filter(nombre="Demo · Central").exists():
            self.stdout.write("La demostración ya fue cargada; se conservan sus cambios.")
            return

        def sede(nombre, estado="ACTIVA"):
            return Sede.objects.create(
                nombre=f"Demo · {nombre}",
                direccion=f"Calle {nombre} 85",
                contacto="biblioteca@example.test",
                horarios="Lunes a viernes de 8 a 18",
                estado=estado,
            )

        central, norte = sede("Central"), sede("Norte")
        sede("Cerrada", "BAJA")
        socios = [
            Socio.objects.create(
                numero_socio=f"DEMO-{i}",
                documento=f"DEMO-DOC-{i}",
                nombre=nombre,
                contacto="lector@example.test",
                estado="INHABILITADO" if i == 3 else "HABILITADO",
            )
            for i, nombre in enumerate(["Ana Demo", "Luis Demo", "Socio inhabilitado Demo"], 1)
        ]
        libros = [
            Libro.objects.create(
                titulo=titulo,
                autor=autor,
                editorial="Demostración",
                edicion="1",
            )
            for titulo, autor in [
                ("Demo · Rayuela", "Julio Cortázar"),
                ("Demo · Ficciones", "Jorge Luis Borges"),
            ]
        ]

        def ejemplar(n, libro, propietaria, estado="DISPONIBLE", actual=None, condicion="APTO"):
            return Ejemplar.objects.create(
                codigo_inventario=f"DEMO-EJ-{n}",
                libro=libro,
                sede_propietaria=propietaria,
                sede_actual=actual or propietaria,
                estado=estado,
                condicion_fisica=condicion,
            )

        ejemplar(1, libros[0], central)
        ejemplar(2, libros[0], norte)
        prestado = ejemplar(3, libros[0], central, "PRESTADO")
        ejemplar(4, libros[1], central)
        ejemplar(5, libros[1], norte, "EN_REVISION", condicion="NO_APTO")
        transito = ejemplar(6, libros[1], central, "EN_TRANSITO")
        transito.sede_actual = None
        transito.save(update_fields=["sede_actual"])
        recibido = ejemplar(7, libros[1], central, "EN_REVISION", actual=norte)

        def solicitud(libro, origen, destino, estado, copia=None):
            return SolicitudPrestamo.objects.create(
                socio=socios[0],
                libro=libro,
                sede_origen=origen,
                sede_destino=destino,
                tipo="LOCAL" if origen == destino else "INTERBIBLIOTECARIO",
                estado=estado,
                ejemplar=copia,
                fecha_solicitud=momento(1),
            )

        local = solicitud(libros[0], central, central, "CUMPLIDA", prestado)
        Prestamo.objects.create(
            solicitud=local,
            fecha_entrega=momento(1),
            fecha_vencimiento=momento(8),
        )
        solicitud(libros[0], norte, central, "PENDIENTE")
        solicitud(libros[0], norte, central, "CANCELADA")
        envio = solicitud(libros[1], central, norte, "EN_TRASLADO", transito)
        Reserva.objects.create(socio=socios[1], libro=libros[1], sede_retiro=central)

        for numero, estado, despacho, recepcion, copia, pedido in [
            ("DEMO-RECIBIDO", "RECIBIDO", 5, 7, recibido, None),
            ("DEMO-TRANSITO", "EN_TRANSITO", 10, None, transito, envio),
        ]:
            remito = Remito.objects.create(
                numero=numero,
                sede_origen=central,
                sede_destino=norte,
                estado=estado,
                fecha_creacion=momento(1),
                fecha_despacho=momento(despacho),
                fecha_recepcion=momento(recepcion) if recepcion else None,
            )
            DetalleRemito.objects.create(
                remito=remito,
                ejemplar=copia,
                solicitud=pedido,
                condicion_salida="APTO",
                condicion_recepcion="APTO" if recepcion else None,
            )
            previo = None
            for nuevo, dia in [
                ("EN_PREPARACION", 1),
                ("EMPAQUETADO", despacho),
                ("EN_TRANSITO", despacho),
                *([("RECIBIDO", recepcion)] if recepcion else []),
            ]:
                EventoRemito.objects.create(
                    remito=remito,
                    estado_anterior=previo,
                    estado_nuevo=nuevo,
                    fecha_hora=momento(dia),
                    responsable="Personal Demo",
                    observacion="Datos de demostración",
                )
                previo = nuevo
        self.stdout.write(
            self.style.SUCCESS(
                "Demostración cargada: 3 sedes, 3 socios, 2 libros, 7 ejemplares. "
                "Reportes de referencia: 1–20/10/2026."
            )
        )
