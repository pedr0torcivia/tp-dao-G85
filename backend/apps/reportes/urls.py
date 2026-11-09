from django.urls import path

from . import views
from .views import PrestamosVencidosView

urlpatterns = [
    path("reportes/operaciones/", views.reportes_operaciones, name="reportes-operaciones"),
    path(
        "prestamos-vencidos/",
        PrestamosVencidosView.as_view(),
        name="reporte-prestamos-vencidos",
    ),
    path("reportes/activos/", views.reportes_activos, name="reportes-activos"),
    path("reportes/logistica/", views.reportes_logistica, name="reportes-logistica"),
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
