from rest_framework.routers import DefaultRouter

from .views import SedeViewSet

router = DefaultRouter()
router.register("", SedeViewSet, basename="sede")

urlpatterns = router.urls
