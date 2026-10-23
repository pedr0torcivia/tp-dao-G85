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
]
