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

```
POST /rag/index   {"documents": [{"doc_id": "d1", "text": "..."}]}  -> {"indexed_chunks": N}
POST /rag/query   {"question": "...", "top_k": 4}                   -> {"answer": "...", "sources": [...]}
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
