from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .exceptions import ErrorCatalogo
from .models import Ejemplar, Libro
from .selectors import (
    disponibilidad_por_sede,
    listar_ejemplares,
    listar_libros,
)
from .serializers import (
    EjemplarSerializer,
    EjemplarUpdateSerializer,
    LibroSerializer,
)
from .services import (
    actualizar_condicion_ejemplar,
    actualizar_libro,
    asignar_ejemplar,
    crear_ejemplar,
    crear_libro,
    liberar_ejemplar,
)


def catalogo_error_response(error: ErrorCatalogo):
    return Response(
        {"error": {"detail": str(error)}},
        status=status.HTTP_400_BAD_REQUEST,
    )


class LibroListCreateView(APIView):
    def get(self, request):
        texto_busqueda = request.query_params.get("search")

        libros = listar_libros(search=texto_busqueda)
        serializer = LibroSerializer(libros, many=True)

        return Response(serializer.data)

    def post(self, request):
        serializer = LibroSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        libro = crear_libro(**serializer.validated_data)
        respuesta = LibroSerializer(libro)

        return Response(
            respuesta.data,
            status=status.HTTP_201_CREATED,
        )


class LibroDetailView(APIView):
    def get(self, request, libro_id):
        libro = get_object_or_404(Libro, id=libro_id)
        serializer = LibroSerializer(libro)

        return Response(serializer.data)

    def patch(self, request, libro_id):
        libro = get_object_or_404(Libro, id=libro_id)
        serializer = LibroSerializer(
            libro,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)

        libro = actualizar_libro(
            libro=libro,
            datos=serializer.validated_data,
        )

        return Response(LibroSerializer(libro).data)


class EjemplarListCreateView(APIView):
    def get(self, request):
        libro_id = request.query_params.get("libro_id")
        sede_id = request.query_params.get("sede_id")
        estado = request.query_params.get("estado")

        ejemplares = listar_ejemplares(
            libro_id=libro_id,
            sede_id=sede_id,
            estado=estado,
        )
        serializer = EjemplarSerializer(ejemplares, many=True)

        return Response(serializer.data)

    def post(self, request):
        serializer = EjemplarSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            ejemplar = crear_ejemplar(**serializer.validated_data)
        except ErrorCatalogo as error:
            return catalogo_error_response(error)

        respuesta = EjemplarSerializer(ejemplar)

        return Response(
            respuesta.data,
            status=status.HTTP_201_CREATED,
        )


class EjemplarDetailView(APIView):
    def get(self, request, ejemplar_id):
        ejemplar = get_object_or_404(Ejemplar, id=ejemplar_id)
        return Response(EjemplarSerializer(ejemplar).data)

    def patch(self, request, ejemplar_id):
        ejemplar = get_object_or_404(Ejemplar, id=ejemplar_id)
        serializer = EjemplarUpdateSerializer(
            ejemplar,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)

        try:
            ejemplar = actualizar_condicion_ejemplar(
                ejemplar=ejemplar,
                condicion_fisica=serializer.validated_data["condicion_fisica"],
            )
        except ErrorCatalogo as error:
            return catalogo_error_response(error)

        return Response(EjemplarSerializer(ejemplar).data)


class EjemplarAsignarView(APIView):
    def post(self, request, ejemplar_id):
        ejemplar = get_object_or_404(Ejemplar, id=ejemplar_id)

        try:
            ejemplar = asignar_ejemplar(ejemplar=ejemplar)
        except ErrorCatalogo as error:
            return catalogo_error_response(error)

        return Response(EjemplarSerializer(ejemplar).data)


class EjemplarLiberarView(APIView):
    def post(self, request, ejemplar_id):
        ejemplar = get_object_or_404(Ejemplar, id=ejemplar_id)

        try:
            ejemplar = liberar_ejemplar(ejemplar=ejemplar)
        except ErrorCatalogo as error:
            return catalogo_error_response(error)

        return Response(EjemplarSerializer(ejemplar).data)


class DisponibilidadView(APIView):
    def get(self, request):
        libro_id = request.query_params.get("libro_id")
        sede_id = request.query_params.get("sede_id")

        return Response(
            disponibilidad_por_sede(
                libro_id=libro_id,
                sede_id=sede_id,
            )
        )
