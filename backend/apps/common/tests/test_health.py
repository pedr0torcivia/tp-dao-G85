from django.test import SimpleTestCase
from django.urls import reverse


class HealthEndpointTest(SimpleTestCase):
    def test_health_returns_ok(self):
        response = self.client.get(reverse("health"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_schema_incluye_catalogo_circulacion_remitos_y_reportes(self):
        response = self.client.get("/api/schema/?format=json")
        self.assertEqual(response.status_code, 200)
        paths = response.json()["paths"]
        for path in [
            "/api/auth/sesion/",
            "/api/auth/ingresar/",
            "/api/auth/salir/",
            "/api/libros/",
            "/api/ejemplares/",
            "/api/reservas/",
            "/api/solicitudes/",
            "/api/remitos/",
            "/api/prestamos-vencidos/",
            "/api/reportes/movimientos/",
            "/api/reportes/demanda-interbibliotecaria/",
            "/api/reportes/disponibilidad/",
            "/api/reportes/operaciones/",
        ]:
            self.assertIn(path, paths)
