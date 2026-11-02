from django.urls import path

from .auth import IngresarView, SalirView, SesionView
from .views import api_root, health

urlpatterns = [
    path("", api_root, name="api-root"),
    path("health/", health, name="health"),
    path("auth/sesion/", SesionView.as_view(), name="sesion"),
    path("auth/ingresar/", IngresarView.as_view(), name="ingresar"),
    path("auth/salir/", SalirView.as_view(), name="salir"),
]
