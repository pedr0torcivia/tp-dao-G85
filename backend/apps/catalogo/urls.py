from django.urls import path

from .views import LibroDetailView, LibroListCreateView

urlpatterns = [
    path("libros/", LibroListCreateView.as_view(), name="libro-list"),
    path(
        "libros/<int:libro_id>/",
        LibroDetailView.as_view(),
        name="libro-detail",
    ),
]