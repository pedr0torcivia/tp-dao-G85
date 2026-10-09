from django.urls import path

from .views import api_root, health

urlpatterns = [
    path("", api_root, name="api-root"),
    path("health/", health, name="health"),
]
