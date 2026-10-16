from rest_framework.routers import DefaultRouter

from .views import DetalleRemitoViewSet, EventoRemitoViewSet, RemitoViewSet

router = DefaultRouter()
router.register("remitos", RemitoViewSet, basename="remito")
router.register("detalles-remito", DetalleRemitoViewSet, basename="detalle-remito")
router.register("eventos-remito", EventoRemitoViewSet, basename="evento-remito")

urlpatterns = router.urls
