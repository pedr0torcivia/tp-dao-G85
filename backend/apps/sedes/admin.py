from django.contrib import admin

from .models import Sede


@admin.register(Sede)
class SedeAdmin(admin.ModelAdmin):
    list_display = ["id", "nombre", "direccion", "estado"]
    list_filter = ["estado"]
    search_fields = ["nombre", "direccion", "contacto"]
    ordering = ["nombre"]
    readonly_fields = ["estado"]

    def has_delete_permission(self, request, obj=None):
        return False
