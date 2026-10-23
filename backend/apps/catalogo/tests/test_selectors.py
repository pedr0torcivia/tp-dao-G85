from django.test import TestCase

from apps.catalogo.models import Libro
from apps.catalogo.selectors import listar_libros, obtener_libro


class LibroSelectorsTest(TestCase):
    def setUp(self):
        self.central = Libro.objects.create(
            isbn="9780000000001",
            titulo="El principito",
            autor="Antoine de Saint-Exupéry",
            editorial="Salamandra",
            edicion="1",
        )
        self.norte = Libro.objects.create(
            isbn="9780000000002",
            titulo="Don Quijote",
            autor="Miguel de Cervantes",
            editorial="Austral",
            edicion="2",
        )

    def test_lista_libros_ordenados_por_titulo(self):
        libros = list(listar_libros())

        self.assertEqual(libros, [self.norte, self.central])

    def test_busca_por_titulo_autor_o_isbn(self):
        self.assertEqual(list(listar_libros(search="principito")), [self.central])
        self.assertEqual(list(listar_libros(search="cervantes")), [self.norte])
        self.assertEqual(list(listar_libros(search="0000000002")), [self.norte])

    def test_busqueda_ignora_espacios(self):
        self.assertEqual(list(listar_libros(search="  quijote  ")), [self.norte])

    def test_busqueda_vacia_lista_todos(self):
        self.assertEqual(list(listar_libros(search="   ")), [self.norte, self.central])

    def test_obtener_libro(self):
        self.assertEqual(obtener_libro(libro_id=self.central.id), self.central)
