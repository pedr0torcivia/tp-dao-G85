from django.contrib import admin

from .models import Prestamo, Reserva, SolicitudPrestamo


@admin.register(SolicitudPrestamo)
class SolicitudPrestamoAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "socio",
        "libro",
        "tipo",
        "estado",
        "sede_origen",
        "sede_destino",
        "fecha_solicitud",
    ]
    list_filter = ["tipo", "estado", "sede_origen", "sede_destino"]
    search_fields = [
        "socio__nombre",
        "socio__numero_socio",
        "libro__titulo",
    ]


@admin.register(Prestamo)
class PrestamoAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "solicitud",
        "fecha_entrega",
        "fecha_vencimiento",
        "fecha_devolucion",
    ]
    list_filter = ["fecha_entrega", "fecha_vencimiento"]


@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "socio",
        "libro",
        "sede_retiro",
        "estado",
        "fecha_reserva",
    ]
    list_filter = ["estado", "sede_retiro"]
