from rest_framework.routers import DefaultRouter

from .views import PrestamoViewSet, SolicitudPrestamoViewSet

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

urlpatterns = router.urls
