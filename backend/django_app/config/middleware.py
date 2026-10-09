
import logging
import time


logger = logging.getLogger("api.monitoring")


class RequestMonitoringMiddleware:
    """
    Logs API request duration, HTTP status and unexpected errors.
    Does not log request bodies, query parameters or credentials.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.perf_counter()

        try:
            response = self.get_response(request)
        except Exception:
            duration_ms = (
                time.perf_counter() - start_time
            ) * 1000

            logger.exception(
                "Request exception: method=%s path=%s duration_ms=%.2f",
                request.method,
                request.path,
                duration_ms,
            )
            raise

        duration_ms = (
            time.perf_counter() - start_time
        ) * 1000

        status_code = response.status_code

        message = (
            "API request: method=%s path=%s "
            "status=%s duration_ms=%.2f"
        )

        log_args = (
            request.method,
            request.path,
            status_code,
            duration_ms,
        )

        if status_code >= 500:
            logger.error(message, *log_args)
        elif status_code >= 400:
            logger.warning(message, *log_args)
        else:
            logger.info(message, *log_args)

        return response
