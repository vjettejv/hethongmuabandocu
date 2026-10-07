import os

import socketio
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django_app = get_asgi_application()
from messaging import realtime  # noqa: E402
from messaging.asgi import LegacyUpgradePackets  # noqa: E402

application = LegacyUpgradePackets(
    socketio.ASGIApp(
        realtime.sio,
        django_app,
        socketio_path="socket.io",
        on_startup=realtime.startup,
        on_shutdown=realtime.shutdown,
    )
)
