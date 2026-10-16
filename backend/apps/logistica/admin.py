from django.contrib import admin

from .models import DetalleRemito, EventoRemito, Remito


@admin.register(Remito)
class RemitoAdmin(admin.ModelAdmin):
    list_display = ["id", "numero", "sede_origen", "sede_destino", "estado"]
    list_filter = ["estado"]
    search_fields = ["numero"]
    ordering = ["numero"]

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(DetalleRemito)
class DetalleRemitoAdmin(admin.ModelAdmin):
    list_display = ["id", "remito", "ejemplar", "condicion_salida", "condicion_recepcion"]
    ordering = ["remito"]

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(EventoRemito)
class EventoRemitoAdmin(admin.ModelAdmin):
    list_display = ["id", "remito", "estado_anterior", "estado_nuevo", "responsable", "fecha_hora"]
    list_filter = ["estado_nuevo"]
    ordering = ["remito", "fecha_hora", "id"]

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False
