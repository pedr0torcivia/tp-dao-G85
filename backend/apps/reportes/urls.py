from django.urls import path

from . import views

urlpatterns = [
    path("reportes/movimientos/", views.reportes_movimientos, name="reportes-movimientos"),
]
