from apps.catalogo.models import Ejemplar, Libro
from apps.sedes.models import Sede
from apps.socios.models import Socio


def crear_sede(*, nombre="Central"):
    return Sede.objects.create(
        nombre=nombre,
        direccion=f"Dirección {nombre}",
        contacto=f"{nombre.lower()}@example.com",
        horarios="Lunes a viernes",
    )


def crear_socio(*, numero="SOC-001", documento="12345678"):
    return Socio.objects.create(
        numero_socio=numero,
        documento=documento,
        nombre="Persona de prueba",
        contacto="persona@example.com",
    )


def crear_libro(*, isbn="9780000000001", titulo="Patrones de diseño"):
    return Libro.objects.create(
        isbn=isbn,
        titulo=titulo,
        autor="Gamma",
        editorial="Editorial",
        edicion="1",
    )


def crear_ejemplar(*, libro, sede, codigo="EJ-001"):
    return Ejemplar.objects.create(
        codigo_inventario=codigo,
        libro=libro,
        sede_propietaria=sede,
        sede_actual=sede,
    )
