# app — production-grade Python service skeleton

Hexagonal, strictly typed, fail-fast. Generated from prod-skillpack.

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
make install     # uv sync --extra dev
make lint        # ruff
make typecheck   # mypy strict
make test        # pytest + coverage gate
make run         # uvicorn on :8000
make load        # k6 load test (needs the app running)
```

Defaults run fully offline (`APP_GREETER_PROVIDER=fake`). Configure via `APP_*` env vars
(see `.env.example`). To add an external dependency, add a port + lazy adapter + fake and
branch in `container.py` — nothing else changes.

## RAG

Retrieval-augmented generation follows the same hexagonal pattern: three ports
(`EmbedderPort`, `VectorStorePort`, `GeneratorPort`), in-memory/deterministic fakes by
default, real adapters behind a lazy SDK import.

```
POST /rag/index   {"documents": [{"doc_id": "d1", "text": "..."}]}  -> {"indexed_chunks": N}
POST /rag/query   {"question": "...", "top_k": 4}                   -> {"answer": "...", "sources": [...]}
```

Offline by default (`APP_EMBEDDER_PROVIDER=fake`, `APP_GENERATOR_PROVIDER=fake`). For real
backends, install the extra (`uv sync --extra rag`) and switch providers:

- `APP_EMBEDDER_PROVIDER=voyage` + `APP_VOYAGE_API_KEY` — embeddings via Voyage AI.
- `APP_GENERATOR_PROVIDER=claude` + `APP_ANTHROPIC_API_KEY` — generation via Claude
  (`claude-opus-4-8` by default), using the official `anthropic` SDK.

The vector store ships as an in-memory cosine index; swap in pgvector/Qdrant by adding an
adapter and branching in `build_vector_store`.
