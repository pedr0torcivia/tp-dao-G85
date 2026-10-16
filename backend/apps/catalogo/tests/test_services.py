from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.catalogo.models import Libro
from apps.catalogo.services import crear_libro


class LibroServicesTest(TestCase):
    def crear_libro(self, isbn=None):
        return crear_libro(
            titulo="  El principito  ",
            autor="  Antoine de Saint-Exupéry  ",
            editorial="  Salamandra  ",
            edicion="  1  ",
            isbn=isbn,
        )

    def test_crear_libro_guarda_y_limpia_espacios(self):
        libro = self.crear_libro(isbn="  9780156012195  ")

        libro.refresh_from_db()

        self.assertEqual(Libro.objects.count(), 1)
        self.assertEqual(libro.titulo, "El principito")
        self.assertEqual(libro.autor, "Antoine de Saint-Exupéry")
        self.assertEqual(libro.editorial, "Salamandra")
        self.assertEqual(libro.edicion, "1")
        self.assertEqual(libro.isbn, "9780156012195")

    def test_rechaza_isbn_duplicado(self):
        self.crear_libro(isbn="9780156012195")

        with self.assertRaises(ValidationError) as contexto:
            self.crear_libro(isbn="9780156012195")

        self.assertIn("isbn", contexto.exception.message_dict)
        self.assertEqual(Libro.objects.count(), 1)

    def test_permite_varios_libros_sin_isbn(self):
        primero = self.crear_libro()
        segundo = self.crear_libro()

        self.assertIsNone(primero.isbn)
        self.assertIsNone(segundo.isbn)
        self.assertEqual(Libro.objects.count(), 2)

    def test_isbn_vacio_se_guarda_como_null(self):
        libro = self.crear_libro(isbn="   ")

        libro.refresh_from_db()

        self.assertIsNone(libro.isbn)