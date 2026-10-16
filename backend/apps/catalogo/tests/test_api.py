from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.catalogo.models import Ejemplar, EstadoEjemplar, Libro
from apps.sedes.models import EstadoSede, Sede


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

        response = self.client.get(reverse("libro-list"))

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

        response = self.client.get(reverse("libro-detail", args=[libro.id]))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], libro.id)
        self.assertEqual(response.data["titulo"], "El principito")

    def test_consultar_libro_inexistente(self):
        response = self.client.get(reverse("libro-detail", args=[9999]))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_modificar_datos_bibliograficos(self):
        libro = self.crear_libro()

        response = self.client.patch(
            reverse("libro-detail", args=[libro.id]),
            {"titulo": "El principito actualizado"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["titulo"], "El principito actualizado")


class EjemplarApiTest(APITestCase):
    def setUp(self):
        self.sede_central = Sede.objects.create(
            nombre="Biblioteca Central",
            direccion="Av. Siempre Viva 123",
            contacto="central@biblioteca.test",
            horarios="Lunes a viernes",
            estado=EstadoSede.ACTIVA,
        )

        self.sede_norte = Sede.objects.create(
            nombre="Biblioteca Norte",
            direccion="Calle Norte 456",
            contacto="norte@biblioteca.test",
            horarios="Lunes a viernes",
            estado=EstadoSede.ACTIVA,
        )

        self.libro = Libro.objects.create(
            isbn="9780000000101",
            titulo="El principito",
            autor="Antoine de Saint-Exupéry",
            editorial="Salamandra",
            edicion="1",
        )

        self.otro_libro = Libro.objects.create(
            isbn="9780000000102",
            titulo="Don Quijote",
            autor="Miguel de Cervantes",
            editorial="Austral",
            edicion="2",
        )

    def crear_ejemplar(self, **cambios):
        datos = {
            "codigo_inventario": "EJ-0001",
            "libro_id": self.libro.id,
            "sede_propietaria_id": self.sede_central.id,
            "condicion_fisica": "Bueno",
        }
        datos.update(cambios)

        return self.client.post(
            reverse("ejemplar-list"),
            datos,
            format="json",
        )

    def test_listar_ejemplares(self):
        self.crear_ejemplar()

        response = self.client.get(reverse("ejemplar-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["codigo_inventario"], "EJ-0001")

    def test_crear_ejemplar(self):
        response = self.crear_ejemplar()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["estado"], EstadoEjemplar.DISPONIBLE)
        self.assertEqual(
            response.data["sede_actual_id"],
            self.sede_central.id,
        )
        self.assertEqual(Ejemplar.objects.count(), 1)

    def test_filtrar_por_libro(self):
        self.crear_ejemplar()

        self.crear_ejemplar(
            codigo_inventario="EJ-0002",
            libro_id=self.otro_libro.id,
        )

        response = self.client.get(
            reverse("ejemplar-list"),
            {"libro_id": self.otro_libro.id},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["codigo_inventario"], "EJ-0002")

    def test_filtrar_por_sede(self):
        self.crear_ejemplar(
            sede_propietaria_id=self.sede_norte.id,
        )

        response = self.client.get(
            reverse("ejemplar-list"),
            {"sede_id": self.sede_norte.id},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["sede_propietaria_id"], self.sede_norte.id)

    def test_filtrar_por_estado(self):
        self.crear_ejemplar()

        response = self.client.get(
            reverse("ejemplar-list"),
            {"estado": EstadoEjemplar.DISPONIBLE},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["estado"], EstadoEjemplar.DISPONIBLE)

    def test_rechazar_codigo_duplicado(self):
        self.crear_ejemplar()

        response = self.crear_ejemplar()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Ejemplar.objects.count(), 1)

    def test_consultar_ejemplar(self):
        creado = self.crear_ejemplar()
        ejemplar_id = creado.data["id"]

        response = self.client.get(reverse("ejemplar-detail", args=[ejemplar_id]))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["codigo_inventario"], "EJ-0001")

    def test_modificar_condicion_fisica(self):
        creado = self.crear_ejemplar()
        ejemplar_id = creado.data["id"]

        response = self.client.patch(
            reverse("ejemplar-detail", args=[ejemplar_id]),
            {"condicion_fisica": "Muy bueno"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["condicion_fisica"], "Muy bueno")

    def test_asignar_y_liberar_ejemplar(self):
        creado = self.crear_ejemplar()
        ejemplar_id = creado.data["id"]

        asignar = self.client.post(reverse("ejemplar-asignar", args=[ejemplar_id]))
        liberar = self.client.post(reverse("ejemplar-liberar", args=[ejemplar_id]))

        self.assertEqual(asignar.status_code, status.HTTP_200_OK)
        self.assertEqual(asignar.data["estado"], EstadoEjemplar.ASIGNADO)
        self.assertEqual(liberar.status_code, status.HTTP_200_OK)
        self.assertEqual(liberar.data["estado"], EstadoEjemplar.DISPONIBLE)

    def test_disponibilidad_por_sede(self):
        creado = self.crear_ejemplar()
        ejemplar_id = creado.data["id"]
        self.client.post(reverse("ejemplar-asignar", args=[ejemplar_id]))

        response = self.client.get(reverse("disponibilidad-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]["total"], 1)
        self.assertEqual(response.data[0]["disponibles"], 0)
        self.assertEqual(response.data[0]["no_disponibles"], 1)
