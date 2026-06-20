from __future__ import annotations

from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.container import Container, build_container
from app.domain.models import Document, DomainError, Greeting, RagAnswer


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
    app.state.container = build_container()
    yield


def get_container(request: Request) -> Container:
    container: Container = request.app.state.container
    return container


def create_app() -> FastAPI:
    app = FastAPI(title="app", lifespan=lifespan)

    @app.middleware("http")
    async def _security_headers(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        response = await call_next(request)
        for header, value in _SECURITY_HEADERS.items():
            response.headers.setdefault(header, value)
        return response

    @app.exception_handler(DomainError)
    async def _domain_error(request: Request, exc: DomainError) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": str(exc)})

    @app.get("/healthz")
    async def healthz() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/readyz")
    async def readyz(request: Request) -> dict[str, str]:
        container = get_container(request)
        if not container.settings.allowed_locales:
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
    async def rag_index(request: Request, body: IndexRequest) -> IndexResponse:
        container = get_container(request)
        indexed = container.rag.index(body.documents)
        return IndexResponse(indexed_chunks=indexed)

    @app.post("/rag/query", response_model=RagAnswer)
    async def rag_query(request: Request, body: QueryRequest) -> RagAnswer:
        container = get_container(request)
        return container.rag.answer(body.question, body.top_k)

    return app


app = create_app()
