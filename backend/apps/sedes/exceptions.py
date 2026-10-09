class ErrorSede(Exception):
    """Error base del dominio de sedes."""


class NombreSedeDuplicadoError(ErrorSede):
    """Existe otra sede con el mismo nombre."""


class SedeYaDadaDeBajaError(ErrorSede):
    """La sede ya se encuentra dada de baja."""


class SedeYaActivaError(ErrorSede):
    """La sede ya se encuentra activa."""


class SedeInactivaError(ErrorSede):
    """La operación requiere una sede activa."""
