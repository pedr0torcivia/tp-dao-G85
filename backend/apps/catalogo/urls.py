from django.urls import path

from .views import (
    EjemplarListCreateView,
    LibroDetailView,
    LibroListCreateView,
)

urlpatterns = [
    path("libros/", LibroListCreateView.as_view(), name="libro-list"),
    path(
        "libros/<int:libro_id>/",
        LibroDetailView.as_view(),
        name="libro-detail",
    ),
    path(
        "ejemplares/",
        EjemplarListCreateView.as_view(),
        name="ejemplar-list",
    ),
]
