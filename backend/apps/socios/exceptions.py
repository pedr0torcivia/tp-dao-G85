class ErrorSocio(Exception):
    """Error base del dominio de socios."""


class SocioDuplicadoError(ErrorSocio):
    """Ya existe un socio con el mismo número o documento."""


class SocioYaHabilitadoError(ErrorSocio):
    """El socio ya está habilitado."""


class SocioYaInhabilitadoError(ErrorSocio):
    """El socio ya está inhabilitado."""


class SocioInhabilitadoError(ErrorSocio):
    """La operación requiere un socio habilitado."""