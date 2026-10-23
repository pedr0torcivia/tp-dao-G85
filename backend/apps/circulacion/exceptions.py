class ErrorCirculacion(Exception):
    """Error base del dominio de circulación."""


class SocioInhabilitadoError(ErrorCirculacion):
    """El socio no puede iniciar o recibir un préstamo."""


class EstadoSolicitudInvalidoError(ErrorCirculacion):
    """La solicitud no se encuentra en el estado requerido."""


class EjemplarNoDisponibleError(ErrorCirculacion):
    """El ejemplar no se encuentra disponible."""


class EjemplarNoAptoError(ErrorCirculacion):
    """El ejemplar no está físicamente apto para préstamo."""


class EjemplarNoCorrespondeError(ErrorCirculacion):
    """El ejemplar no corresponde al libro solicitado."""


class EjemplarEnOtraSedeError(ErrorCirculacion):
    """El ejemplar no se encuentra en la sede esperada."""


class PrestamoYaCreadoError(ErrorCirculacion):
    """La solicitud ya generó un préstamo."""


class PrestamoYaDevueltoError(ErrorCirculacion):
    """El préstamo ya fue devuelto."""


class FechaPrestamoInvalidaError(ErrorCirculacion):
    """Las fechas del préstamo no son coherentes."""


class TramitacionNoDisponibleError(ErrorCirculacion):
    """El tipo de tramitación todavía no está disponible."""