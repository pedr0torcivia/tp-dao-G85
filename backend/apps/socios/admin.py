from django.contrib import admin

from .models import Socio
from .services import habilitar_socio, inhabilitar_socio


@admin.register(Socio)
class SocioAdmin(admin.ModelAdmin):
    list_display = ["numero_socio", "nombre", "documento", "estado"]
    list_filter = ["estado"]
    search_fields = ["numero_socio", "documento", "nombre", "contacto"]
    readonly_fields = ["estado"]
    actions = ["habilitar_seleccionados", "inhabilitar_seleccionados"]

    @admin.action(description="Habilitar socios seleccionados")
    def habilitar_seleccionados(self, request, queryset):
        for socio in queryset.exclude(estado="HABILITADO"):
            habilitar_socio(socio=socio)

    @admin.action(description="Inhabilitar socios seleccionados")
    def inhabilitar_seleccionados(self, request, queryset):
        for socio in queryset.exclude(estado="INHABILITADO"):
            inhabilitar_socio(socio=socio)