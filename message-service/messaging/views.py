from drf_spectacular.utils import extend_schema
from rest_framework.response import Response

from . import selectors, services
from .authentication import authenticate
from .http import LegacyView


class ContactsView(LegacyView):
    @extend_schema(responses=dict, tags=["messages"])
    def get(self, request):
        identity = authenticate(request)
        return Response({"data": selectors.contacts(identity.get("id"), request.request_id)})


class HistoryView(LegacyView):
    @extend_schema(responses=dict, tags=["messages"])
    def get(self, request, contact_id):
        return Response({"data": selectors.history(authenticate(request).get("id"), contact_id)})


class SendView(LegacyView):
    @extend_schema(request=dict, responses=dict, tags=["messages"])
    def post(self, request):
        return Response(
            {
                "data": services.send(
                    authenticate(request).get("id"), request.data, request.request_id
                )
            }
        )


class NotificationView(LegacyView):
    @extend_schema(responses=dict, tags=["notifications"])
    def get(self, request):
        return Response({"data": selectors.notifications(authenticate(request).get("id"))})

    @extend_schema(request=dict, responses=dict, tags=["notifications"])
    def post(self, request):
        return Response(
            {"success": True, "data": services.notify(request.data, request.request_id)}
        )


class ReadAllView(LegacyView):
    @extend_schema(request=None, responses=dict, tags=["notifications"])
    def put(self, request):
        return Response(services.read_all(authenticate(request).get("id")))
