"""Transparent REST and WebSocket transport; upstream owns business behavior."""

import asyncio
from contextlib import suppress

import httpx
from fastapi import Request, WebSocket, WebSocketDisconnect
from starlette.responses import JSONResponse, StreamingResponse
from websockets.asyncio.client import connect
from websockets.exceptions import WebSocketException

METHODS = ["GET", "HEAD", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
PREFIXES = {
    "/auth": "auth",
    "/users": "user",
    "/posts": "post",
    "/categories": "category",
    "/messages": "message",
    "/notifications": "notification",
    "/reviews": "review",
    "/search": "search",
    "/favorites": "favorite",
}
SPECIAL = {
    "/admin/posts": "post",
    "/admin/categories": "category",
    "/uploads": "post",
    "/socket.io": "message",
}
HOP_HEADERS = {
    b"connection",
    b"keep-alive",
    b"proxy-authenticate",
    b"proxy-authorization",
    b"te",
    b"trailer",
    b"transfer-encoding",
    b"upgrade",
}


def resolve(path):
    for prefix, service in SPECIAL.items():
        if path == prefix or path.startswith(prefix + "/"):
            return service, ""
    for prefix, service in PREFIXES.items():
        if path == prefix or path.startswith(prefix + "/"):
            return service, prefix
    return None


def filtered_headers(headers, *, response=False):
    blocked = set(HOP_HEADERS)
    for key, value in headers:
        if key.lower() == b"connection":
            blocked.update(token.strip().lower() for token in value.split(b","))
    if not response:
        blocked.add(b"host")
    return [
        (key, value)
        for key, value in headers
        if key.lower() not in blocked
        and not (response and key.lower().startswith(b"access-control-"))
    ]


def target_url(base, scope, prefix):
    path = scope.get("raw_path", scope["path"].encode("utf-8"))
    if prefix:
        path = path[len(prefix.encode("ascii")) :]
    path = path or b"/"
    query = scope.get("query_string", b"")
    return httpx.URL(base.rstrip("/")).copy_with(raw_path=path + (b"?" + query if query else b""))


def request_headers(request):
    headers = filtered_headers(request.scope["headers"])
    previous = request.headers.get("x-forwarded-for", "")
    client = request.client.host if request.client else ""
    forwarded = f"{previous}, {client}" if previous and client else previous or client
    headers = [
        (k, v)
        for k, v in headers
        if k.lower() not in {b"x-request-id", b"x-forwarded-for", b"x-forwarded-proto"}
    ]
    headers += [
        (b"x-request-id", request.state.request_id.encode("ascii")),
        (b"x-forwarded-for", forwarded.encode("latin-1")),
        (b"x-forwarded-proto", request.scope["scheme"].encode("ascii")),
    ]
    return headers


async def proxy_http(request: Request):
    route = resolve(request.scope["path"])
    if route is None:
        return JSONResponse({"error": "Not Found"}, status_code=404)
    service, prefix = route
    if service == "auth" and request.scope["path"].removeprefix(prefix).rstrip("/") in {
        "/health",
        "/ready",
        "/schema",
        "/docs",
    }:
        # Auth infrastructure is internal; legacy public IDs with these names didn't resolve.
        return JSONResponse({"error": "User not found"}, status_code=404)
    request.state.upstream = service
    base = getattr(request.app.state.settings, f"{service}_service_url")
    if not base:
        return JSONResponse({"error": "Service Unavailable"}, status_code=502)
    client = request.app.state.upstream_client
    try:
        outgoing = client.build_request(
            request.method,
            target_url(base, request.scope, prefix),
            headers=request_headers(request),
            content=request.stream(),
        )
        upstream = await client.send(outgoing, stream=True)
    except httpx.TimeoutException:
        return JSONResponse({"error": "Gateway Timeout"}, status_code=504)
    except httpx.HTTPError:
        return JSONResponse({"error": "Service Unavailable"}, status_code=502)

    async def body():
        try:
            async for chunk in upstream.aiter_raw():
                yield chunk
        finally:
            await upstream.aclose()

    response = StreamingResponse(body(), status_code=upstream.status_code)
    response.raw_headers = filtered_headers(upstream.headers.raw, response=True)
    return response


async def proxy_socket(websocket: WebSocket):
    settings = websocket.app.state.settings
    origin = websocket.headers.get("origin")
    if origin and origin not in settings.cors_origins:
        await websocket.close(code=1008)
        return
    base = settings.message_service_url
    if not base:
        await websocket.close(code=1013)
        return
    url = target_url(base, websocket.scope, "")
    url = url.copy_with(scheme="wss" if url.scheme == "https" else "ws")
    excluded = {
        b"host",
        b"origin",
        b"sec-websocket-key",
        b"sec-websocket-version",
        b"sec-websocket-extensions",
        b"sec-websocket-protocol",
    }
    headers = [
        (k.decode("latin-1"), v.decode("latin-1"))
        for k, v in filtered_headers(websocket.scope["headers"])
        if k.lower() not in excluded
    ]
    try:
        async with connect(
            str(url),
            origin=origin,
            additional_headers=headers,
            subprotocols=websocket.scope.get("subprotocols") or None,
            open_timeout=settings.connect_timeout,
            close_timeout=5,
            max_size=None,
            compression=None,
            proxy=None,
        ) as upstream:
            await websocket.accept(subprotocol=upstream.subprotocol)

            async def to_upstream():
                while True:
                    message = await websocket.receive()
                    if message["type"] == "websocket.disconnect":
                        return
                    await upstream.send(
                        message["bytes"] if message.get("bytes") is not None else message["text"]
                    )

            async def to_client():
                async for message in upstream:
                    if isinstance(message, bytes):
                        await websocket.send_bytes(message)
                    else:
                        await websocket.send_text(message)

            tasks = {asyncio.create_task(to_upstream()), asyncio.create_task(to_client())}
            try:
                done, _ = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
                for task in done:
                    task.result()
            finally:
                for task in tasks:
                    task.cancel()
                await asyncio.gather(*tasks, return_exceptions=True)
            with suppress(RuntimeError):
                await websocket.close(code=1000)
    except (OSError, WebSocketException, WebSocketDisconnect, TimeoutError):
        with suppress(RuntimeError):
            await websocket.close(code=1013)
