import asyncio
import logging

import socketio
from django.conf import settings

LOGGER = logging.getLogger("messaging.realtime")
sio = socketio.AsyncServer(
    async_mode="asgi", cors_allowed_origins="*", logger=False, engineio_logger=False
)
_loop = None
_emit_lock = None


async def startup():
    global _loop, _emit_lock
    _loop = asyncio.get_running_loop()
    _emit_lock = asyncio.Lock()


async def shutdown():
    global _loop
    await sio.shutdown()
    _loop = None


def room(user_id):
    if user_id is None:
        value = "null"
    elif isinstance(user_id, bool):
        value = "true" if user_id else "false"
    elif isinstance(user_id, dict):
        value = "[object Object]"
    elif isinstance(user_id, float) and user_id.is_integer():
        value = str(int(user_id))
    else:
        value = str(user_id)
    return "user_" + value


@sio.event
async def connect(sid, environ, auth):
    LOGGER.info("socket connected", extra={"event": "connect", "socket_id": sid})


@sio.event
async def join_user_room(sid, user_id):
    target = room(user_id)
    await sio.enter_room(sid, target)
    LOGGER.info(
        "room joined", extra={"event": "join_user_room", "socket_id": sid, "room": target[:128]}
    )


@sio.event
async def disconnect(sid, reason):
    LOGGER.info("socket disconnected", extra={"event": "disconnect", "socket_id": sid})


async def _emit(event, payload, target):
    async with _emit_lock:
        await sio.emit(event, payload, room=target)


def emit(event, payload, user_id, request_id):
    # Django REST executes in a sync thread. Schedule onto the single ASGI loop
    # owning Engine.IO queues and room state, never create a second event loop.
    if _loop is None:
        LOGGER.warning(
            "realtime loop unavailable", extra={"event": event, "failure": "unavailable"}
        )
        return
    target = room(user_id)
    future = asyncio.run_coroutine_threadsafe(_emit(event, payload, target), _loop)
    try:
        future.result(timeout=settings.REALTIME_TIMEOUT)
        LOGGER.info(
            "room event emitted",
            extra={"request_id": request_id, "event": event, "room": target[:128]},
        )
    except Exception:
        future.cancel()
        LOGGER.warning(
            "room event unavailable",
            extra={
                "request_id": request_id,
                "event": event,
                "room": target[:128],
                "failure": "unavailable",
            },
        )
