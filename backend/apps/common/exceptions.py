from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import ValidationError
from rest_framework.views import exception_handler


def api_exception_handler(exc, context):
    if isinstance(exc, DjangoValidationError):
        exc = ValidationError(exc.message_dict if hasattr(exc, "message_dict") else exc.messages)
    response = exception_handler(exc, context)
    if response is None:
        return None

    detail = response.data
    response.data = {
        "error": {
            "status": response.status_code,
            "detail": detail,
            "code": exc.get_codes() if hasattr(exc, "get_codes") else None,
        }
    }
    return response
