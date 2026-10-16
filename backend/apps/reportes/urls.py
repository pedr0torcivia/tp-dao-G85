from django.urls import path

from .views import PrestamosVencidosView

urlpatterns = [
    path(
        "prestamos-vencidos/",
        PrestamosVencidosView.as_view(),
        name="reporte-prestamos-vencidos",
    ),
]