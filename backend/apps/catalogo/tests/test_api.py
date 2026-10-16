from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.catalogo.models import Libro


class LibroApiTest(APITestCase):
    def crear_libro(self, **cambios):
        datos = {
            "isbn": "9780000000001",
            "titulo": "El principito",
            "autor": "Antoine de Saint-Exupéry",
            "editorial": "Salamandra",
            "edicion": "1",
        }
        datos.update(cambios)

        return Libro.objects.create(**datos)

    def test_listar_libros(self):
        self.crear_libro()

        response = self.client.get(
            reverse("libro-list")
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["titulo"], "El principito")

    def test_buscar_libros(self):
        self.crear_libro()

        self.crear_libro(
            isbn="9780000000002",
            titulo="Don Quijote",
            autor="Miguel de Cervantes",
        )

        response = self.client.get(
            reverse("libro-list"),
            {"search": "quijote"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["titulo"], "Don Quijote")

    def test_crear_libro(self):
        datos = {
            "isbn": "9780000000003",
            "titulo": "Rayuela",
            "autor": "Julio Cortázar",
            "editorial": "Sudamericana",
            "edicion": "1",
        }

        response = self.client.post(
            reverse("libro-list"),
            datos,
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["titulo"], "Rayuela")
        self.assertEqual(Libro.objects.count(), 1)

    def test_rechazar_libro_sin_titulo(self):
        datos = {
            "isbn": "9780000000004",
            "autor": "Autor desconocido",
            "editorial": "Editorial",
            "edicion": "1",
        }

        response = self.client.post(
            reverse("libro-list"),
            datos,
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Libro.objects.count(), 0)

    def test_rechazar_isbn_duplicado(self):
        self.crear_libro()

        datos = {
            "isbn": "9780000000001",
            "titulo": "Otro libro",
            "autor": "Otro autor",
            "editorial": "Otra editorial",
            "edicion": "1",
        }

        response = self.client.post(
            reverse("libro-list"),
            datos,
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Libro.objects.count(), 1)

    def test_consultar_libro(self):
        libro = self.crear_libro()

        response = self.client.get(
            reverse("libro-detail", args=[libro.id])
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], libro.id)
        self.assertEqual(response.data["titulo"], "El principito")

    def test_consultar_libro_inexistente(self):
        response = self.client.get(
            reverse("libro-detail", args=[9999])
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)