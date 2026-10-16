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

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/sedes/", include("apps.sedes.urls")),
    path("api/", include("apps.circulacion.urls")),
    path("api/", include("apps.common.urls")),
    # ...
]