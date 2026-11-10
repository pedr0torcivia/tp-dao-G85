"""Bitácora transaccional de las operaciones exitosas de la API de negocio."""

from datetime import datetime

from django.db import transaction
from django.utils import timezone

from apps.catalogo.models import Ejemplar, Libro
from apps.circulacion.models import Prestamo, Reserva, SolicitudPrestamo
from apps.logistica.models import DetalleRemito, Remito
from apps.sedes.models import Sede
from apps.socios.models import Socio

from .models import Operacion

MODELOS = {
    "libros": Libro,
    "ejemplares": Ejemplar,
    "sedes": Sede,
    "socios": Socio,
    "solicitudes": SolicitudPrestamo,
    "prestamos": Prestamo,
    "reservas": Reserva,
    "remitos": Remito,
    "detalles-remito": DetalleRemito,
}


def registrar(*, entidad, registro_id, accion, usuario, antes, despues, descripcion=None):
    campos = [k for k in despues if antes.get(k) != despues[k] and k != "id"]
    etiquetas = {
        "codigo_inventario": "Inventario",
        "fecha_alta": "Fecha de alta",
        "condicion_fisica": "Condición física",
        "sede_propietaria_id": "Propietaria (ID)",
        "sede_actual_id": "Ubicación (ID)",
        "libro_id": "Libro (ID)",
    }

    def mostrar(valor):
        if isinstance(valor, datetime):
            return timezone.localtime(valor).strftime("%d/%m/%Y %H:%M")
        return "—" if valor is None else str(valor)

    cambios = "; ".join(
        f"{etiquetas.get(k, k.replace('_', ' ').capitalize())}: "
        f"{mostrar(antes.get(k))} → {mostrar(despues[k])}"
        for k in campos
    )
    sedes = {
        v
        for d in (antes, despues)
        for k, v in d.items()
        if k.startswith("sede_") and k.endswith("_id") and v is not None
    }
    if entidad == "sedes":
        sedes.add(registro_id)
    return Operacion.objects.create(
        entidad=entidad,
        registro_id=registro_id,
        accion=accion,
        usuario=usuario,
        descripcion=descripcion or cambios or accion,
        antes=antes,
        despues=despues,
        sede_ids=sorted(sedes),
    )


# Campos binarios (fotos) no se copian a la bitácora: sólo se registra que cambiaron.
CAMPOS_BINARIOS = {"foto"}


def _instantanea(modelo, pk) -> dict:
    fila = modelo.objects.filter(pk=pk).values().first() or {}
    for campo in CAMPOS_BINARIOS & fila.keys():
        fila[campo] = "con foto" if fila[campo] else "sin foto"
    return fila


class AuditoriaMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        partes = request.path.strip("/").split("/")
        if (
            request.method not in {"POST", "PATCH", "PUT", "DELETE"}
            or len(partes) < 2
            or partes[0] != "api"
            or partes[1] not in MODELOS
        ):
            return self.get_response(request)
        entidad = partes[1]
        modelo = MODELOS[entidad]
        pk = int(partes[2]) if len(partes) > 2 and partes[2].isdigit() else None
        with transaction.atomic():
            antes = _instantanea(modelo, pk) if pk else {}
            response = self.get_response(request)
            if not (200 <= response.status_code < 300):
                return response
            if pk is None:
                pk = getattr(response, "data", {}).get("id")
            if pk is None:
                return response
            despues = _instantanea(modelo, pk)
            accion = "ALTA" if not antes else "MODIFICACION"
            if request.method == "DELETE" or (
                len(partes) > 3
                and partes[3]
                in {
                    "dar-de-baja",
                    "inhabilitar",
                }
            ):
                accion = "BAJA"
            elif len(partes) > 3:
                accion = "OPERACION"
            registrar(
                entidad=entidad,
                registro_id=pk,
                accion=accion,
                usuario=request.user.get_username(),
                antes=antes,
                despues=despues,
            )
            return response
