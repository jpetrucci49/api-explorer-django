# github/middleware.py
import time
import structlog
from django.utils.deprecation import MiddlewareMixin

class TimingMiddleware(MiddlewareMixin):
    def process_request(self, request):
        request.start_time = time.time()

    def process_response(self, request, response):
        if hasattr(request, "start_time"):
            duration = (time.time() - request.start_time) * 1000
            response["X-Response-Time"] = f"{duration:.2f}"
        return response

class RequestLoggingMiddleware(MiddlewareMixin):
    def __init__(self, get_response):
        self.get_response = get_response
        self.logger = structlog.get_logger("github")

    def process_request(self, request):
        self.logger.info(
            "request_started",
            method=request.method,
            path=request.path,
            query=request.GET.urlencode(),
        )

    def process_response(self, request, response):
        cache_status = response.get("X-Cache", "UNKNOWN")
        duration = "unknown"
        if hasattr(request, "start_time"):
            duration = (time.time() - request.start_time) * 1000
            duration = f"{duration:.2f}"
        self.logger.info(
            "request_finished",
            method=request.method,
            path=request.path,
            query=request.GET.urlencode(),
            status=response.status_code,
            cache=cache_status,
            duration=f"{duration}ms",
        )
        return response

    def process_exception(self, request, exception):
        self.logger.error(
            "request_failed",
            method=request.method,
            path=request.path,
            query=request.GET.urlencode(),
            exception=str(exception),
        )