from rest_framework.routers import DefaultRouter

from .views import SocioViewSet

router = DefaultRouter()
router.register("", SocioViewSet, basename="socio")

urlpatterns = router.urls