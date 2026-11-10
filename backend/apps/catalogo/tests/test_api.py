from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.catalogo.models import CondicionFisica, Ejemplar, EstadoEjemplar, Libro
from apps.common.testing import autenticar_personal
from apps.sedes.models import EstadoSede, Sede


class LibroApiTest(APITestCase):
    def setUp(self):
        autenticar_personal(self.client)

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
        autenticar_personal(self.client)
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
            "condicion_fisica": CondicionFisica.APTO,
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

    def test_dar_de_baja_por_http_pone_el_estado_en_baja(self):
        creado = self.crear_ejemplar()
        ejemplar_id = creado.data["id"]

        response = self.client.post(reverse("ejemplar-dar-de-baja", args=[ejemplar_id]))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["estado"], EstadoEjemplar.BAJA)

        # Un ejemplar de baja ya no puede darse de baja otra vez
        response = self.client.post(reverse("ejemplar-dar-de-baja", args=[ejemplar_id]))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_aprobar_disponibilidad_por_http_vuelve_a_disponible(self):
        creado = self.crear_ejemplar()
        ejemplar_id = creado.data["id"]
        Ejemplar.objects.filter(pk=ejemplar_id).update(estado=EstadoEjemplar.EN_REVISION)

        response = self.client.post(reverse("ejemplar-aprobar-disponibilidad", args=[ejemplar_id]))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["estado"], EstadoEjemplar.DISPONIBLE)

    def test_modificar_condicion_fisica(self):
        creado = self.crear_ejemplar()
        ejemplar_id = creado.data["id"]

        response = self.client.patch(
            reverse("ejemplar-detail", args=[ejemplar_id]),
            {"condicion_fisica": CondicionFisica.NO_APTO},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["condicion_fisica"], CondicionFisica.NO_APTO)

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


class IsbnYFotoApiTest(APITestCase):
    def setUp(self):
        from apps.common.testing import autenticar_personal

        autenticar_personal(self.client)

    def test_isbn_debe_tener_13_numeros(self):
        base = {"titulo": "Libro", "autor": "A", "editorial": "E", "edicion": "1"}
        for isbn in ["abc", "123", "97800000000011", "978000000000X"]:
            respuesta = self.client.post(
                reverse("libro-list"), {**base, "isbn": isbn}, format="json"
            )
            self.assertEqual(respuesta.status_code, 400, isbn)
        respuesta = self.client.post(
            reverse("libro-list"), {**base, "isbn": "978-0-00-000000-9"}, format="json"
        )
        self.assertEqual(respuesta.status_code, 201)
        self.assertEqual(respuesta.data["isbn"], "9780000000009")

    def test_portada_del_libro(self):
        from django.core.files.uploadedfile import SimpleUploadedFile

        from apps.catalogo.models import Libro

        libro = Libro.objects.create(titulo="Nuevo", autor="A", editorial="E", edicion="1")
        url = reverse("libro-portada", args=[libro.id])
        self.assertEqual(self.client.get(url).status_code, 404)

        jpg = b"\xff\xd8\xff\xe0" + b"1" * 40
        respuesta = self.client.post(url, {"portada": SimpleUploadedFile("tapa.jpg", jpg)})
        self.assertEqual(respuesta.status_code, 200)
        self.assertTrue(
            respuesta.data["portada_url"].startswith(f"/api/libros/{libro.id}/portada/")
        )
        self.assertEqual(self.client.get(url).content, jpg)

        malo = SimpleUploadedFile("tapa.gif", b"GIF89a....")
        self.assertEqual(self.client.post(url, {"portada": malo}).status_code, 400)


class EliminarLibroApiTest(APITestCase):
    def setUp(self):
        from apps.common.testing import autenticar_personal
        from apps.sedes.models import Sede

        autenticar_personal(self.client)
        self.sede = Sede.objects.create(nombre="Central", direccion="D", contacto="C", horarios="H")

    def test_elimina_un_libro_sin_historial(self):
        from apps.catalogo.models import Ejemplar, Libro

        libro = Libro.objects.create(titulo="Borrable", autor="A", editorial="E", edicion="1")
        Ejemplar.objects.create(
            codigo_inventario="B-1", libro=libro, sede_propietaria=self.sede, estado="BAJA"
        )
        respuesta = self.client.delete(reverse("libro-detail", args=[libro.id]))
        self.assertEqual(respuesta.status_code, 204)
        self.assertFalse(Libro.objects.filter(pk=libro.pk).exists())
        self.assertFalse(Ejemplar.objects.filter(codigo_inventario="B-1").exists())

    def test_no_elimina_con_copias_activas_ni_con_historial(self):
        from apps.catalogo.models import Ejemplar, Libro
        from apps.circulacion.models import Reserva
        from apps.socios.models import Socio

        con_copias = Libro.objects.create(
            titulo="Con copias", autor="A", editorial="E", edicion="1"
        )
        Ejemplar.objects.create(
            codigo_inventario="C-1", libro=con_copias, sede_propietaria=self.sede
        )
        respuesta = self.client.delete(reverse("libro-detail", args=[con_copias.id]))
        self.assertEqual(respuesta.status_code, 400)
        self.assertIn("copia activa", str(respuesta.data))

        reservado = Libro.objects.create(titulo="Reservado", autor="A", editorial="E", edicion="2")
        socio = Socio.objects.create(numero_socio="S", documento="D", nombre="N", contacto="C")
        Reserva.objects.create(socio=socio, libro=reservado, sede_retiro=self.sede)
        respuesta = self.client.delete(reverse("libro-detail", args=[reservado.id]))
        self.assertEqual(respuesta.status_code, 400)
        self.assertTrue(Libro.objects.filter(pk=reservado.pk).exists())
        self.assertIn("historial", str(respuesta.data))
