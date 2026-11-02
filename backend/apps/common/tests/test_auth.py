from io import StringIO

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.management import call_command
from django.test import TestCase
from rest_framework.test import APIClient


class AccesoTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.personal = get_user_model().objects.create_user(
            username="personal",
            password="Clave-pruebas-85",
            is_staff=True,
            first_name="Ana",
            last_name="Bibliotecaria",
        )
        cls.lector = get_user_model().objects.create_user(
            username="lector", password="Clave-pruebas-85"
        )

    def setUp(self):
        cache.clear()
        self.client = APIClient(enforce_csrf_checks=True)

    def tearDown(self):
        cache.clear()

    def token(self):
        return self.client.get("/api/auth/sesion/").json()["csrfToken"]

    def ingresar(self, username="personal", password="Clave-pruebas-85", **headers):
        return self.client.post(
            "/api/auth/ingresar/",
            {"username": username, "password": password},
            format="json",
            HTTP_X_CSRFTOKEN=self.token(),
            **headers,
        )

    def test_sesion_anonima_emite_csrf_y_no_se_cachea(self):
        res = self.client.get("/api/auth/sesion/")
        self.assertIsNone(res.json()["usuario"])
        self.assertTrue(res.json()["csrfToken"])
        self.assertIn("no-store", res["Cache-Control"])

    def test_api_de_negocio_rechaza_lecturas_anonimas(self):
        for ruta in [
            "sedes",
            "socios",
            "libros",
            "ejemplares",
            "solicitudes",
            "prestamos",
            "reservas",
            "remitos",
            "eventos-remito",
            "disponibilidad",
            "prestamos-vencidos",
            "reportes/movimientos",
            "reportes/disponibilidad",
            "reportes/demanda-interbibliotecaria",
            "reportes/operaciones",
        ]:
            with self.subTest(ruta=ruta):
                res = self.client.get(f"/api/{ruta}/")
                self.assertEqual(res.status_code, 403)
                self.assertEqual(res.json()["error"]["code"], "not_authenticated")

    def test_api_rechaza_escritura_anonima(self):
        self.assertEqual(self.client.post("/api/libros/", {}).status_code, 403)

    def test_ingreso_requiere_csrf_incluso_sin_sesion(self):
        res = self.client.post(
            "/api/auth/ingresar/", {"username": "personal", "password": "Clave-pruebas-85"}
        )
        self.assertEqual(res.status_code, 403)

    def test_ingreso_valido_restaura_identidad_y_cookie_http_only(self):
        anterior = self.token()
        res = self.ingresar()
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["usuario"]["nombre"], "Ana Bibliotecaria")
        self.assertNotEqual(anterior, res.json()["csrfToken"])
        self.assertTrue(res.cookies["sessionid"]["httponly"])
        self.assertEqual(self.client.get("/api/libros/").status_code, 200)
        sesion = self.client.get("/api/auth/sesion/").json()
        self.assertEqual(sesion["usuario"]["id"], self.personal.pk)

    def test_clave_incorrecta_y_usuario_desconocido_no_abren_sesion(self):
        for username in ["personal", "desconocido"]:
            res = self.ingresar(username=username, password="incorrecta")
            self.assertEqual(res.status_code, 400)
            self.assertEqual(res.json()["error"]["detail"], "Usuario o contraseña incorrectos.")
            self.assertIsNone(self.client.get("/api/auth/sesion/").json()["usuario"])

    def test_cuenta_sin_permiso_de_personal_no_ingresa(self):
        self.assertEqual(self.ingresar(username="lector").status_code, 400)
        self.client.force_login(self.lector)
        self.assertEqual(self.client.get("/api/libros/").status_code, 403)

    def test_cuenta_inactiva_no_ingresa(self):
        self.personal.is_active = False
        self.personal.save(update_fields=["is_active"])
        self.assertEqual(self.ingresar().status_code, 400)

    def test_revocar_permiso_bloquea_sesion_existente(self):
        self.ingresar()
        self.personal.is_staff = False
        self.personal.save(update_fields=["is_staff"])
        self.assertEqual(self.client.get("/api/libros/").status_code, 403)
        self.assertIsNone(self.client.get("/api/auth/sesion/").json()["usuario"])

    def test_cierre_invalida_cookie_anterior_y_exige_csrf(self):
        self.ingresar()
        cookie = self.client.cookies["sessionid"].value
        self.assertEqual(self.client.post("/api/auth/salir/").status_code, 403)
        res = self.client.post("/api/auth/salir/", HTTP_X_CSRFTOKEN=self.token())
        self.assertEqual(res.status_code, 200)
        self.assertIsNone(res.json()["usuario"])
        self.client.cookies["sessionid"] = cookie
        self.assertEqual(self.client.get("/api/libros/").status_code, 403)

    def test_escrituras_autenticadas_exigen_csrf(self):
        self.ingresar()
        datos = {"titulo": "Libro", "autor": "Autor", "editorial": "Editorial", "edicion": "1"}
        self.assertEqual(self.client.post("/api/libros/", datos, format="json").status_code, 403)
        res = self.client.post("/api/libros/", datos, format="json", HTTP_X_CSRFTOKEN=self.token())
        self.assertEqual(res.status_code, 201)

    def test_origen_ajeno_no_puede_iniciar_sesion(self):
        self.assertEqual(self.ingresar(HTTP_ORIGIN="https://ajeno.example").status_code, 403)

    def test_limite_de_intentos(self):
        for _ in range(10):
            self.assertEqual(self.ingresar(password="incorrecta").status_code, 400)
        self.assertEqual(self.ingresar(password="incorrecta").status_code, 429)

    def test_demo_crea_cuenta_sin_restablecer_clave_o_permisos(self):
        call_command("cargar_demo", stdout=StringIO())
        user = get_user_model().objects.get(username="biblioteca")
        self.assertTrue(user.check_password("demo"))
        self.assertTrue(user.is_staff)
        self.assertFalse(user.is_superuser)
        user.set_password("Otra-clave-85")
        user.is_active = False
        user.save()
        call_command("cargar_demo", stdout=StringIO())
        user.refresh_from_db()
        self.assertTrue(user.check_password("Otra-clave-85"))
        self.assertFalse(user.is_active)
