from rest_framework.views import exception_handler
from rest_framework.exceptions import APIException

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    
    status_code = getattr(exc, 'status_code', 500)
    detail = str(exc) or "Internal server error"
    extra = getattr(exc, 'extra', {})
    
    if response is not None:
        status_code = response.status_code
        if isinstance(response.data, dict):
            detail = response.data.get('detail', detail)
            extra = response.data.get('extra', extra)
        elif isinstance(response.data, str):
            detail = response.data
    
    response.data = {
        "detail": {
            "status": status_code,
            "detail": detail,
            "extra": extra
        }
    }
    response.status_code = status_code
    return response

class CustomAPIException(APIException):
    def __init__(self, status_code, detail, extra=None):
        self.status_code = status_code
        self.detail = detail
        self.extra = extra or {}