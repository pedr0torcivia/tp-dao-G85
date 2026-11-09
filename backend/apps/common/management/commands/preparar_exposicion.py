"""Escenario estable: obras reales, personas e inventario ficticios para la defensa."""

import json
from datetime import datetime
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.catalogo.models import Ejemplar, Libro
from apps.circulacion.models import Prestamo, Reserva, SolicitudPrestamo
from apps.common.models import Operacion
from apps.logistica.models import DetalleRemito, EventoRemito, Remito
from apps.sedes.models import Sede
from apps.socios.models import Socio

# Títulos y créditos contrastados con editoriales; referencias en docs/catalogo-exposicion.md.
CATALOGO = [
    (fila["titulo"], fila["autor"], fila["editorial"], fila["edicion"], fila["isbn"])
    for fila in json.loads(
        (Path(__file__).resolve().parents[2] / "data/catalogo_exposicion.json").read_text(
            encoding="utf-8"
        )
    )
]


def fecha(dia, mes=10):
    return timezone.make_aware(datetime(2026, mes, dia, 12))


class Command(BaseCommand):
    help = "Prepara la exposición. --reiniciar reemplaza SOLO datos de biblioteca y bitácora."

    def add_arguments(self, parser):
        parser.add_argument("--reiniciar", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        if not options["reiniciar"] and Libro.objects.exists():
            if Ejemplar.objects.filter(codigo_inventario="EXPO-001").exists():
                self.stdout.write("El escenario ya está preparado; se conservan los cambios.")
                return
            raise CommandError(
                "La base contiene libros. Usar --reiniciar para reemplazar el escenario."
            )
        if options["reiniciar"]:
            # Orden explícito de dependencias; no toca usuarios, claves ni sesiones.
            for modelo in (
                Operacion,
                EventoRemito,
                DetalleRemito,
                Remito,
                Prestamo,
                SolicitudPrestamo,
                Reserva,
                Ejemplar,
                Libro,
                Socio,
                Sede,
            ):
                modelo.objects.all().delete()
        user, creado = get_user_model().objects.get_or_create(
            username="biblioteca",
            defaults={"is_staff": True, "first_name": "Personal de biblioteca"},
        )
        if creado:
            user.set_password("demo")
            user.save(update_fields=["password"])
        central, norte, sur = [
            Sede.objects.create(
                nombre=nombre,
                direccion=direccion,
                contacto="biblioteca@example.test",
                horarios="Lunes a viernes, 8 a 18",
                estado=estado,
            )
            for nombre, direccion, estado in [
                ("Biblioteca Central", "Av. Colón 100, Córdoba", "ACTIVA"),
                ("Biblioteca Norte", "Av. Monseñor Pablo Cabrera 200, Córdoba", "ACTIVA"),
                ("Biblioteca Sur", "Av. Vélez Sarsfield 300, Córdoba", "BAJA"),
            ]
        ]
        socios = [
            Socio.objects.create(
                numero_socio=f"SOC-{i:03}",
                documento=f"EXPO-{i:03}",
                nombre=nombre,
                contacto=f"lector{i}@example.test",
                estado="INHABILITADO" if i == 6 else "HABILITADO",
            )
            for i, nombre in enumerate(
                [
                    "Ana Rojas",
                    "Bruno Medina",
                    "Carla Suárez",
                    "Diego Paz",
                    "Lucía Campos",
                    "Tomás Vera",
                ],
                1,
            )
        ]
        libros, copias = [], []
        for titulo, autor, editorial, edicion, isbn in CATALOGO:
            libro = Libro.objects.create(
                titulo=titulo, autor=autor, editorial=editorial, edicion=edicion, isbn=isbn
            )
            libros.append(libro)
            for sede in (central, central, norte):
                numero = len(copias) + 1
                copias.append(
                    Ejemplar.objects.create(
                        codigo_inventario=f"EXPO-{numero:03}",
                        libro=libro,
                        sede_propietaria=sede,
                        sede_actual=sede,
                        fecha_alta=fecha(1),
                        estado="DISPONIBLE",
                        condicion_fisica="APTO",
                    )
                )

        def estado(numero, valor, actual=None, condicion="APTO"):
            copia = copias[numero - 1]
            copia.estado, copia.condicion_fisica = valor, condicion
            if actual is not None:
                copia.sede_actual = actual
            copia.save()
            return copia

        def solicitud(libro, socio, origen, destino, dia, valor, copia=None):
            return SolicitudPrestamo.objects.create(
                libro=libros[libro - 1],
                socio=socios[socio - 1],
                sede_origen=origen,
                sede_destino=destino,
                fecha_solicitud=fecha(dia),
                estado=valor,
                ejemplar=copia,
                tipo="LOCAL" if origen == destino else "INTERBIBLIOTECARIO",
            )

        vencido = solicitud(1, 1, central, central, 5, "CUMPLIDA", estado(2, "PRESTADO"))
        Prestamo.objects.create(
            solicitud=vencido, fecha_entrega=fecha(5), fecha_vencimiento=fecha(12)
        )
        vigente = solicitud(6, 2, central, central, 28, "CUMPLIDA", estado(17, "PRESTADO"))
        Prestamo.objects.create(
            solicitud=vigente, fecha_entrega=fecha(28), fecha_vencimiento=fecha(11, 11)
        )
        transito = estado(9, "EN_TRANSITO")
        transito.sede_actual = None
        transito.save(update_fields=["sede_actual"])
        ped_transito = solicitud(3, 3, norte, central, 10, "EN_TRASLADO", transito)
        recibido = estado(12, "LISTO_PARA_ENTREGA", central)
        ped_recibido = solicitud(4, 2, norte, central, 8, "LISTA_PARA_ENTREGA", recibido)
        retorno = estado(23, "EN_REVISION", norte)
        ped_retorno = solicitud(8, 4, central, norte, 1, "CUMPLIDA", retorno)
        Prestamo.objects.create(
            solicitud=ped_retorno,
            fecha_entrega=fecha(6),
            fecha_vencimiento=fecha(20),
            fecha_devolucion=fecha(18),
            condicion_devolucion="APTO",
        )
        solicitud(1, 3, norte, central, 25, "PENDIENTE")
        solicitud(3, 3, norte, central, 15, "CANCELADA")
        Reserva.objects.create(
            socio=socios[4], libro=libros[2], sede_retiro=central, fecha_reserva=fecha(26)
        )
        estado(14, "EN_REVISION", condicion="NO_APTO")
        estado(20, "BAJA")

        for numero, origen, destino, copia, pedido, despacho, recepcion in [
            ("ENV-2026-001", norte, central, transito, ped_transito, 20, None),
            ("ENV-2026-002", norte, central, recibido, ped_recibido, 10, 12),
            ("ENV-2026-003", central, norte, retorno, ped_retorno, 3, 5),
        ]:
            remito = Remito.objects.create(
                numero=numero,
                sede_origen=origen,
                sede_destino=destino,
                estado="RECIBIDO" if recepcion else "EN_TRANSITO",
                fecha_creacion=fecha(1),
                fecha_despacho=fecha(despacho),
                fecha_recepcion=fecha(recepcion) if recepcion else None,
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
                    fecha_hora=fecha(dia),
                    responsable="Personal de biblioteca",
                    observacion="Escenario de exposición; operaciones ficticias.",
                )
                previo = nuevo
        Operacion.objects.create(
            entidad="escenario",
            registro_id=1,
            accion="OPERACION",
            usuario="preparacion",
            descripcion="Carga inicial: 30 obras reales, 90 copias, 3 sedes y 6 socios ficticios. "
            "La bitácora de ABMC comienza a partir de esta preparación.",
        )
        self.stdout.write(
            self.style.SUCCESS(
                "Exposición preparada: 30 libros, 90 ejemplares (83 disponibles), "
                "3 sedes, 6 socios, "
                "7 solicitudes, 3 préstamos, 1 reserva y 3 remitos. Referencia: 01–31/10/2026."
            )
        )
