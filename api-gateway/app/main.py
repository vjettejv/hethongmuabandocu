import logging.config
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.logging_config import build_logging
from app.middleware import RequestContextMiddleware
from app.proxy import METHODS, proxy_http, proxy_socket
from app.settings import Settings


class FoundationResponse(BaseModel):
    service: str
    status: str


def create_app(settings=None, *, configure_logging=True, transport=None):
    settings = settings or Settings()
    if configure_logging:
        logging.config.dictConfig(build_logging(settings.service_name))

    @asynccontextmanager
    async def lifespan(application):
        timeout = httpx.Timeout(settings.read_timeout, connect=settings.connect_timeout)
        async with httpx.AsyncClient(
            timeout=timeout, follow_redirects=False, trust_env=False, transport=transport
        ) as client:
            application.state.upstream_client = client
            yield

    application = FastAPI(title="API Gateway", version="phase-2", redoc_url=None, lifespan=lifespan)
    application.state.settings = settings
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=METHODS,
        allow_headers=["Content-Type", "Authorization", "X-Request-ID"],
        expose_headers=["X-Request-ID"],
    )
    application.add_middleware(RequestContextMiddleware)

    @application.get("/health", response_model=FoundationResponse, tags=["foundation"])
    def health():
        return {"service": settings.service_name, "status": "healthy"}

    @application.get("/ready", response_model=FoundationResponse, tags=["foundation"])
    def ready():
        return {"service": settings.service_name, "status": "ready"}

    application.add_api_route("/{path:path}", proxy_http, methods=METHODS, include_in_schema=False)
    application.add_api_websocket_route("/socket.io/", proxy_socket)
    application.add_api_websocket_route("/socket.io/{path:path}", proxy_socket)
    return application


app = create_app()
