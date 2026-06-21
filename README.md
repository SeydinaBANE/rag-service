# RAG Service — production-grade Python service skeleton

[![CI](https://github.com/SeydinaBANE/rag-service/actions/workflows/ci.yml/badge.svg)](https://github.com/SeydinaBANE/rag-service/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
![Typed: mypy strict](https://img.shields.io/badge/mypy-strict-blue)
![Coverage gate: 80%](https://img.shields.io/badge/coverage-%E2%89%A580%25-brightgreen)

Hexagonal, strictly typed, fail-fast FastAPI service with a retrieval-augmented generation
pipeline. Runs fully offline by default; real Voyage/Claude/Cohere backends plug in behind
typed ports. Generated from prod-skillpack.

```
src/app/
  domain/      pure types + business errors (depends on nothing)
  ports/       Protocol interfaces (no SDK imports)
  adapters/    port implementations (lazy SDK import, retry/timeout) + fakes
  services/    orchestration (depends only on ports)
  api/         FastAPI app, security headers, /healthz + /readyz
  middleware.py   per-IP sliding-window rate limiting on /rag/* routes
  dependencies.py injectable FastAPI deps (get_principal: X-API-Key auth)
  governance.py   RBAC, PII masking, idempotency guard, audit log
  config.py    pydantic-settings, fail-fast @model_validator
  container.py composition root (build_* factories)
```

## Commands

```bash
make init        # uv sync --extra dev + pre-commit install
make build       # lint + typecheck + test
make lint        # ruff check + ruff format --check
make typecheck   # mypy strict
make test        # pytest + coverage gate (80%)
make run         # uvicorn on :8000
make docker-up   # build + run via docker compose
make load        # k6 load test (needs the app running)
```

Defaults run fully offline (`APP_GREETER_PROVIDER=fake`). Configure via `APP_*` env vars
(see `.env.example`). To add an external dependency, add a port + lazy adapter + fake and
branch in `container.py` — nothing else changes.

## RAG

Retrieval-augmented generation follows the same hexagonal pattern: four ports
(`EmbedderPort`, `VectorStorePort`, `RerankerPort`, `GeneratorPort`), in-memory/deterministic
fakes by default, real adapters behind a lazy SDK import. The query pipeline is
retrieve (candidate pool) → rerank → generate.

Both `/rag/*` routes require an `X-API-Key` header (see Security below).

```
POST /rag/index   {"documents": [{"doc_id": "d1", "text": "..."}]}  -> {"indexed_chunks": N}
POST /rag/query   {"question": "...", "top_k": 4}                   -> {"answer": "...", "sources": [...]}
```

`/rag/index` accepts an optional `Idempotency-Key` header; replaying the same key is a no-op
(`indexed_chunks: 0`), preventing duplicate chunks on retried indexing.

## Security

The `/rag/*` routes are hardened (offline-friendly defaults, override in production):

- **Authentication** — every request must send an `X-API-Key` header. Keys map to roles via
  `APP_API_KEYS` (a JSON list of `"key:role"` pairs; defaults to `dev-key-viewer:viewer` and
  `dev-key-operator:operator`). Missing header → `422`, unknown key → `401`.
- **Authorization (RBAC)** — `/rag/query` needs `read` (`viewer` or `operator`); `/rag/index`
  needs `write` (`operator`). A denied role → `403`. Each index call is recorded in an
  append-only audit log.
- **Rate limiting** — per-IP sliding window on the RAG routes
  (`APP_RATE_LIMIT_MAX_REQUESTS`/`APP_RATE_LIMIT_WINDOW_SEC`, default 60 per 60s); exceeding
  it → `429`.

```bash
curl -X POST localhost:8000/rag/query -H "X-API-Key: dev-key-viewer" \
  -H "Content-Type: application/json" -d '{"question": "..."}'
```

Offline by default (`APP_EMBEDDER_PROVIDER=fake`, `APP_GENERATOR_PROVIDER=fake`). For real
backends, install the extra (`uv sync --extra rag`) and switch providers:

- `APP_EMBEDDER_PROVIDER=voyage` + `APP_VOYAGE_API_KEY` — embeddings via Voyage AI.
- `APP_GENERATOR_PROVIDER=claude` + `APP_ANTHROPIC_API_KEY` — generation via Claude
  (`claude-opus-4-8` by default), using the official `anthropic` SDK.
- `APP_RERANKER_PROVIDER=cohere` + `APP_COHERE_API_KEY` — reranking via Cohere
  (`rerank-v3.5` by default).

The vector store ships as an in-memory cosine index; swap in pgvector/Qdrant by adding an
adapter and branching in `build_vector_store`.
