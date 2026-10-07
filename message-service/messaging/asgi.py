"""Node-compatible Engine.IO upgrade control-packet ordering."""

from urllib.parse import parse_qs


class LegacyUpgradePackets:
    def __init__(self, application):
        self.application = application

    async def __call__(self, scope, receive, send):
        query = parse_qs(scope.get("query_string", b"").decode("ascii", errors="replace"))
        upgrade = (
            scope["type"] == "websocket"
            and scope.get("path", "").startswith("/socket.io/")
            and query.get("EIO") == ["4"]
            and query.get("transport") == ["websocket"]
            and bool(query.get("sid"))
        )
        if not upgrade:
            return await self.application(scope, receive, send)

        async def compatible_send(message):
            # python-engineio queues NOOP to end an outstanding poll. If no poll
            # drains it, the WebSocket writer sends it before namespace CONNECT.
            # Node omits that optional control frame. Keep polling NOOP, probes,
            # heartbeat, CONNECT, app data and binary attachments unchanged.
            if message["type"] == "websocket.send" and message.get("text") == "6":
                return
            await send(message)

        await self.application(scope, receive, compatible_send)
