"""Escenario estable: obras reales, personas e inventario ficticios para la defensa."""

import json
from datetime import datetime, timedelta
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.catalogo.models import Ejemplar, Libro
from apps.circulacion import services as circulacion
from apps.circulacion.models import Prestamo, Reserva, SolicitudPrestamo
from apps.common.models import Operacion
from apps.logistica import services as logistica
from apps.logistica.models import DetalleRemito, EventoRemito, Remito, ResultadoRecepcion
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
                contacto=f"socio{i}@example.test",
            )
            for i, nombre in enumerate(
                [
                    "Torcivia Pedro",
                    "Maretto Agustin",
                    "Fanfliet Juan Ignacio",
                    "Dalmazzo Francisco Gaston",
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
            solicitud=vigente,
            fecha_entrega=fecha(28),
            # Relativo a hoy: el caso vigente no debe vencer antes de la defensa.
            fecha_vencimiento=max(fecha(11, 11), timezone.now() + timedelta(days=14)),
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
            socio=socios[3], libro=libros[2], sede_retiro=central, fecha_reserva=fecha(26)
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
                resultado_recepcion=ResultadoRecepcion.CONFORME if recepcion else None,
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
        self.casos_de_prueba(libros, copias, socios, central, norte)
        Operacion.objects.create(
            entidad="escenario",
            registro_id=1,
            accion="OPERACION",
            usuario="preparacion",
            descripcion=f"Carga inicial: {len(libros)} obras reales, {len(copias)} copias, "
            "3 sedes y 4 socios. La bitácora de ABMC comienza a partir de esta preparación.",
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"Exposición preparada: {len(libros)} libros, {len(copias)} ejemplares "
                f"({Ejemplar.objects.filter(estado='DISPONIBLE').count()} disponibles), "
                f"3 sedes, 4 socios, {SolicitudPrestamo.objects.count()} solicitudes, "
                f"{Prestamo.objects.count()} préstamos, {Reserva.objects.count()} reservas y "
                f"{Remito.objects.count()} remitos."
            )
        )

    def casos_de_prueba(self, libros, copias, socios, central, norte):
        """Un caso por estado relevante, generado con los servicios reales.

        Usa los libros 31 a 41 (cómics agregados). Cada uno tiene las copias
        3n-2 y 3n-1 en Central y 3n en Norte. Torcivia (socio 1) es el socio
        moroso: con préstamos vencidos no puede iniciar circuitos nuevos, por eso
        no participa de los casos generados con servicios.
        """
        libro = {n: libros[n - 1] for n in range(31, len(libros) + 1)}

        def copia(n, sede):
            return copias[3 * n - 3] if sede == "central" else copias[3 * n - 1]

        def pedido(n, socio, origen, destino):
            return circulacion.crear_solicitud(
                socio=socios[socio - 1],
                libro=libro.get(n) or libros[n - 1],
                sede_origen=origen,
                sede_destino=destino,
                tipo="LOCAL" if origen == destino else "INTERBIBLIOTECARIO",
            )

        def asignado(n, socio, origen, destino):
            solicitud = pedido(n, socio, origen, destino)
            sede = "central" if origen == central else "norte"
            return circulacion.asignar_ejemplar(solicitud=solicitud, ejemplar=copia(n, sede))

        def preparado(n, socio, origen, destino):
            solicitud = circulacion.preparar_entrega(solicitud=asignado(n, socio, origen, destino))
            remito = None
            if origen != destino:
                remito = Remito.objects.get(detalles__solicitud=solicitud)
            return solicitud, remito

        ahora = timezone.now()
        responsable = "Personal de biblioteca"

        # Sin City: viaja Central → Norte y llega dañado (RECIBIDO_CON_INCIDENCIAS).
        # La solicitud vuelve a PENDIENTE para asignar otra copia.
        _, incidencia = preparado(35, 3, central, norte)
        logistica.empaquetar_remito(remito=incidencia, responsable=responsable)
        logistica.despachar_remito(remito=incidencia, responsable=responsable)
        logistica.recibir_remito(
            remito=incidencia,
            responsable=responsable,
            resultados={copia(35, "central").pk: ResultadoRecepcion.DANADO},
            observacion="La tapa llegó doblada y con humedad.",
        )
        self.fechar(incidencia, ahora - timedelta(days=6), ahora - timedelta(days=3))

        # The Eternaut: envío Norte → Central anulado antes de salir (CANCELADO).
        eternauta, cancelado = preparado(37, 4, norte, central)
        logistica.empaquetar_remito(remito=cancelado, responsable=responsable)
        logistica.cancelar_remito(
            remito=cancelado, responsable=responsable, observacion="El socio desistió del pedido."
        )
        circulacion.cancelar_solicitud(solicitud=eternauta)

        # The Walking Dead: paquete cerrado Norte → Central esperando transporte.
        _, empaquetado = preparado(33, 2, norte, central)
        logistica.empaquetar_remito(remito=empaquetado, responsable=responsable)

        # Hellboy: envío Central → Norte todavía abierto (EN_PREPARACION).
        preparado(34, 4, central, norte)

        # Saga (local) y Persepolis (interbibliotecaria): asignadas, para mostrar
        # que el mismo botón «Preparar entrega» actúa distinto según la estrategia.
        asignado(31, 2, central, central)
        asignado(32, 3, norte, central)

        # Demanda inter-sedes repetida para que RP02 muestre un ranking real:
        # Saga y Persepolis quedan con más pedidos que el resto.
        pedido(31, 4, central, norte)
        pedido(31, 3, central, norte)
        pedido(32, 4, norte, central)

        # Akira: pedido local pendiente en Norte. Maus: pedido rechazado.
        pedido(36, 4, norte, norte)
        circulacion.rechazar_solicitud(solicitud=pedido(18, 2, norte, norte))

        # Bone: préstamo vigente en Norte.
        bone, _ = preparado(40, 3, norte, norte)
        circulacion.entregar_solicitud(
            solicitud=bone,
            fecha_entrega=ahora - timedelta(days=3),
            fecha_vencimiento=ahora + timedelta(days=11),
        )

        # Arkham Asylum: devuelto dañado; la copia queda NO_APTO en revisión.
        arkham, _ = preparado(39, 4, central, central)
        prestamo = circulacion.entregar_solicitud(
            solicitud=arkham,
            fecha_entrega=ahora - timedelta(days=12),
            fecha_vencimiento=ahora + timedelta(days=2),
        )
        circulacion.registrar_devolucion(
            prestamo=prestamo,
            fecha_devolucion=ahora - timedelta(days=1),
            condicion_devolucion="NO_APTO",
        )

        # Calvin and Hobbes: reserva con copia separada, lista para retirar.
        reserva = circulacion.crear_reserva(socio=socios[1], libro=libro[41], sede_retiro=central)
        circulacion.asignar_reserva(
            reserva=reserva,
            ejemplar=copia(41, "central"),
            fecha_limite_retiro=ahora + timedelta(days=5),
        )
        # Akira en Central: reserva cancelada por el socio.
        circulacion.cancelar_reserva(
            reserva=circulacion.crear_reserva(socio=socios[2], libro=libro[36], sede_retiro=central)
        )

        # Y: The Last Man: segundo préstamo vencido de Torcivia, en Norte (multa).
        y_copia = copia(38, "norte")
        y_copia.estado = "PRESTADO"
        y_copia.save(update_fields=["estado"])
        vencida = SolicitudPrestamo.objects.create(
            libro=libro[38],
            socio=socios[0],
            sede_origen=norte,
            sede_destino=norte,
            fecha_solicitud=fecha(10),
            estado="CUMPLIDA",
            ejemplar=y_copia,
            tipo="LOCAL",
        )
        Prestamo.objects.create(
            solicitud=vencida, fecha_entrega=fecha(10), fecha_vencimiento=fecha(24)
        )

    @staticmethod
    def fechar(remito, despacho, recepcion):
        """Ubica el viaje en días distintos para que RP03 muestre tránsito real."""
        Remito.objects.filter(pk=remito.pk).update(
            fecha_creacion=despacho - timedelta(days=1),
            fecha_despacho=despacho,
            fecha_recepcion=recepcion,
        )
        momentos = {
            "EN_PREPARACION": despacho - timedelta(days=1),
            "EMPAQUETADO": despacho,
            "EN_TRANSITO": despacho,
        }
        for evento in EventoRemito.objects.filter(remito=remito):
            EventoRemito.objects.filter(pk=evento.pk).update(
                fecha_hora=momentos.get(evento.estado_nuevo, recepcion)
            )
