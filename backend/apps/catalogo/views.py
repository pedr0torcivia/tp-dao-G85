from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Libro
from .selectors import listar_libros
from .serializers import LibroSerializer
from .services import crear_libro


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

        return Response(respuesta.data, status=status.HTTP_201_CREATED)


class LibroDetailView(APIView):
    def get(self, request, libro_id):
        libro = get_object_or_404(Libro, id=libro_id)
        serializer = LibroSerializer(libro)

        return Response(serializer.data)
