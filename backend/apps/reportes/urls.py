from django.urls import path

from . import views
from .views import PrestamosVencidosView

urlpatterns = [
    path(
        "prestamos-vencidos/",
        PrestamosVencidosView.as_view(),
        name="reporte-prestamos-vencidos",
    ),
    path("reportes/movimientos/", views.reportes_movimientos, name="reportes-movimientos"),
    path(
        "reportes/demanda-interbibliotecaria/",
        views.reportes_demanda,
        name="reportes-demanda-interbibliotecaria",
    ),
    path(
        "reportes/disponibilidad/",
        views.reportes_disponibilidad,
        name="reportes-disponibilidad",
    ),
]
