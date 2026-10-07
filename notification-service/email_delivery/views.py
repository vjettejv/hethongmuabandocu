from drf_spectacular.utils import extend_schema
from rest_framework.response import Response

from . import services
from .http import LegacyView


class EmailView(LegacyView):
    @extend_schema(request=dict, responses=dict, tags=["email"])
    def post(self, request):
        return Response(services.send(request.data, request.request_id))
