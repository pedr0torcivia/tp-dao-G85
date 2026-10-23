from django.urls import path

from .views import (
    DisponibilidadView,
    EjemplarAprobarDisponibilidadView,
    EjemplarAsignarView,
    EjemplarDarDeBajaView,
    EjemplarDetailView,
    EjemplarLiberarView,
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
    path(
        "ejemplares/<int:ejemplar_id>/",
        EjemplarDetailView.as_view(),
        name="ejemplar-detail",
    ),
    path(
        "ejemplares/<int:ejemplar_id>/asignar/",
        EjemplarAsignarView.as_view(),
        name="ejemplar-asignar",
    ),
    path(
        "ejemplares/<int:ejemplar_id>/liberar/",
        EjemplarLiberarView.as_view(),
        name="ejemplar-liberar",
    ),
    path(
        "ejemplares/<int:ejemplar_id>/dar-de-baja/",
        EjemplarDarDeBajaView.as_view(),
        name="ejemplar-dar-de-baja",
    ),
    path(
        "ejemplares/<int:ejemplar_id>/aprobar-disponibilidad/",
        EjemplarAprobarDisponibilidadView.as_view(),
        name="ejemplar-aprobar-disponibilidad",
    ),
    path(
        "disponibilidad/",
        DisponibilidadView.as_view(),
        name="disponibilidad-list",
    ),
]
