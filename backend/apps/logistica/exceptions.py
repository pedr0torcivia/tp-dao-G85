class LogisticaError(Exception):
    """Base de los errores del dominio de logística."""


class TransicionInvalidaError(LogisticaError):
    """El estado actual del remito no permite la operación solicitada."""


class RemitoVacioError(LogisticaError):
    """El remito no contiene ejemplares y la operación los exige."""


class NumeroRemitoDuplicadoError(LogisticaError):
    """Ya existe un remito con ese número."""


class SedesInvalidasError(LogisticaError):
    """Las sedes del remito no cumplen las reglas del traslado."""


class EjemplarInvalidoError(LogisticaError):
    """El ejemplar no puede integrar el remito solicitado."""
