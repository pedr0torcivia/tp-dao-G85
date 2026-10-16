class ErrorCatalogo(Exception):
    """Error base para reglas de negocio del catálogo."""


class LibroDuplicadoError(ErrorCatalogo):
    """Ya existe un libro con el mismo ISBN."""


class CodigoInventarioDuplicadoError(ErrorCatalogo):
    """Ya existe un ejemplar con ese código."""


class SedePropietariaInactivaError(ErrorCatalogo):
    """La sede propietaria debe estar activa."""


class EjemplarNoDisponibleError(ErrorCatalogo):
    """El ejemplar no puede ser asignado en su estado actual."""


class EjemplarNoAsignadoError(ErrorCatalogo):
    """El ejemplar no puede liberarse porque no está asignado."""


class EjemplarDadoDeBajaError(ErrorCatalogo):
    """Un ejemplar dado de baja no puede modificarse."""
