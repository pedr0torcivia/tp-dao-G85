from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.reportes.demanda_views import DemandaInterbibliotecariaView

from .views import PrestamoViewSet, ReservaViewSet, SolicitudPrestamoViewSet

router = DefaultRouter()
router.register(
    "solicitudes",
    SolicitudPrestamoViewSet,
    basename="solicitud",
)
router.register(
    "prestamos",
    PrestamoViewSet,
    basename="prestamo",
)
router.register(
    "reservas",
    ReservaViewSet,
    basename="reserva",
)

urlpatterns = [
    path(
        "reportes/demanda-interbibliotecaria/",
        DemandaInterbibliotecariaView.as_view(),
        name="demanda-interbibliotecaria",
    ),
    *router.urls,
]
