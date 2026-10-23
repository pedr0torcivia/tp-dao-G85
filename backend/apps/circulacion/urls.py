from django.urls import path
from rest_framework.routers import DefaultRouter

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
    *router.urls,
]
