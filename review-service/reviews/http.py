import logging

from rest_framework.exceptions import MethodNotAllowed
from rest_framework.parsers import JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .exceptions import LegacyError


class LegacyView(APIView):
    parser_classes = [JSONParser, MultiPartParser]

    def handle_exception(self, error):
        if isinstance(error, MethodNotAllowed):
            return Response({"error": "Not found"}, status=404)
        if isinstance(error, LegacyError):
            return Response({"error": str(error)}, status=error.status)
        logging.getLogger("legacy.errors").error(
            "request failure",
            extra={
                "request_id": getattr(self.request, "request_id", "-"),
                "failure": type(error).__name__,
            },
        )
        return Response({"error": "Internal Server Error"}, status=500)
