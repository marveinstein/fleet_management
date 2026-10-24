from django.utils.deprecation import MiddlewareMixin
from django.http import HttpResponse


class CustomCorsMiddleware(MiddlewareMixin):
    """
    Lightweight, self-contained CORS middleware allowing cross-origin
    API requests from React frontend during development and testing.
    """

    def process_request(self, request):
        if request.method == "OPTIONS":
            response = HttpResponse()
            self._add_cors_headers(response)
            return response

    def process_response(self, request, response):
        self._add_cors_headers(response)
        return response

    def _add_cors_headers(self, response):
        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Methods"] = (
            "GET, POST, PUT, PATCH, DELETE, OPTIONS"
        )
        response["Access-Control-Allow-Headers"] = (
            "Content-Type, Authorization, X-Requested-With, X-CSRFToken"
        )
