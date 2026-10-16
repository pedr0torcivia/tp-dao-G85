class LogisticaError(Exception):
    """Base de los errores del dominio de logística."""


class TransicionInvalidaError(LogisticaError):
    """El estado actual del remito no permite la operación solicitada."""


class RemitoVacioError(LogisticaError):
    """El remito no contiene ejemplares y la operación los exige."""
