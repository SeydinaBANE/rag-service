from __future__ import annotations

import time
import uuid
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.config import get_settings
from app.container import Container, build_container
from app.dependencies import get_principal
from app.domain.models import Document, DomainError, Greeting, RagAnswer
from app.governance import AccessDeniedError, Permission, Principal
from app.logging import configure_logging, get_logger
from app.middleware import setup_rate_limiting

_logger = get_logger("app.api.request")


class IndexRequest(BaseModel):
    documents: list[Document] = Field(min_length=1)


class IndexResponse(BaseModel):
    indexed_chunks: int


class QueryRequest(BaseModel):
    question: str = Field(min_length=1)
    top_k: int | None = Field(default=None, gt=0)


_SECURITY_HEADERS: dict[str, str] = {
    "Strict-Transport-Security": "max-age=63072000; includeSubDomains",
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
}


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    container = build_container()
    configure_logging(container.settings.log_level, container.settings.log_json)
    app.state.container = container
    yield


def get_container(request: Request) -> Container:
    container: Container = request.app.state.container
    return container


def create_app() -> FastAPI:
    app = FastAPI(title="app", lifespan=lifespan)
    settings = get_settings()
    setup_rate_limiting(
        app,
        max_requests=settings.rate_limit_max_requests,
        window_sec=settings.rate_limit_window_sec,
    )

    @app.middleware("http")
    async def _security_headers(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        response = await call_next(request)
        for header, value in _SECURITY_HEADERS.items():
            response.headers.setdefault(header, value)
        return response

    @app.middleware("http")
    async def _request_logger(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex
        start = time.perf_counter()
        log_context: dict[str, object] = {
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
        }
        try:
            response = await call_next(request)
        except Exception:
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            _logger.exception("request_failed", extra={**log_context, "duration_ms": duration_ms})
            raise
        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        response.headers["X-Request-ID"] = request_id
        _logger.info(
            "request",
            extra={**log_context, "status_code": response.status_code, "duration_ms": duration_ms},
        )
        return response

    @app.exception_handler(DomainError)
    async def _domain_error(request: Request, exc: DomainError) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": str(exc)})

    @app.exception_handler(AccessDeniedError)
    async def _access_denied(request: Request, exc: AccessDeniedError) -> JSONResponse:
        return JSONResponse(status_code=403, content={"detail": str(exc)})

    @app.get("/healthz")
    async def healthz() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/readyz")
    async def readyz(request: Request) -> dict[str, str]:
        container = get_container(request)
        if not container.rag.ready():
            raise HTTPException(status_code=503, detail="not ready")
        return {"status": "ready"}

    @app.get("/greet", response_model=Greeting)
    async def greet(request: Request, recipient: str, locale: str = "en") -> Greeting:
        container = get_container(request)
        if len(recipient) > container.settings.max_recipient_length:
            raise HTTPException(status_code=422, detail="recipient too long")
        if locale not in container.settings.allowed_locales:
            locale = container.settings.allowed_locales[0]
        return container.greeting.build_greeting(recipient, locale)

    @app.post("/rag/index", response_model=IndexResponse)
    async def rag_index(
        request: Request,
        body: IndexRequest,
        principal: Annotated[Principal, Depends(get_principal)],
        idempotency_key: Annotated[str | None, Header()] = None,
    ) -> IndexResponse:
        container = get_container(request)
        container.rbac.authorize(principal, Permission.WRITE)
        container.audit.record(principal, action="index", resource="rag", allowed=True)
        if idempotency_key is not None and not container.index_idempotency.is_new(idempotency_key):
            return IndexResponse(indexed_chunks=0)
        indexed = container.rag.index(body.documents)
        return IndexResponse(indexed_chunks=indexed)

    @app.post("/rag/query", response_model=RagAnswer)
    async def rag_query(
        request: Request,
        body: QueryRequest,
        principal: Annotated[Principal, Depends(get_principal)],
    ) -> RagAnswer:
        container = get_container(request)
        container.rbac.authorize(principal, Permission.READ)
        return container.rag.answer(body.question, body.top_k)

    return app


app = create_app()
