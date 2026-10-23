from .base import TramitacionPrestamo
from .factory import obtener_estrategia
from .interbibliotecaria import TramitacionInterbibliotecaria
from .local import TramitacionLocal

__all__ = [
    "TramitacionPrestamo",
    "TramitacionLocal",
    "TramitacionInterbibliotecaria",
    "obtener_estrategia",
]
