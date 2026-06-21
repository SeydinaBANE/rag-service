# RAG Service — agent instructions

Python 3.11+ FastAPI service. Hexagonal, strictly typed (mypy strict + ruff ANN),
fail-fast. Runs fully offline by default (all providers `fake`). Tooling via `uv` + Makefile —
always go through `uv run` / make targets, never `python`/`pytest` directly.

> Full architecture and conventions live in `CLAUDE.md`; this file is the quick reference.

## Setup & commands

```bash
make init        # uv sync --extra dev + pre-commit install
cp .env.example .env   # optional — defaults run offline
make docker-up   # build + run the service on :8000
```

Order before push: `make build` (= lint + typecheck + test). CI runs the same plus the
`security` job (`bandit` + `pip-audit`).

| Command | What |
|---|---|
| `make lint` | `ruff check` + `ruff format --check src tests` |
| `make format` | `ruff format` + `ruff check --fix src tests` |
| `make typecheck` | `mypy` (strict + pydantic plugin) |
| `make test` | `pytest` (asyncio_mode=auto, coverage gate 75%) |
| `make build` | lint + typecheck + test |
| `make run` | `uvicorn app.api.app:app --reload --port 8000` |
| `make load` | k6 load test (app must be running) |
| `make precommit` | run all pre-commit hooks |

Run a single test: `uv run pytest tests/unit/test_api.py::test_greet_nominal`.
Integration tests are marked `@pytest.mark.integration` (`-m integration` / `-m "not integration"`).
Install the RAG SDKs with `uv sync --extra rag`.

## Architecture

- Package `app` under `src/` (imports are `from app.xxx import ...`)
- **Entrypoint:** `app.api.app:app` (FastAPI)
- **Config:** pydantic-settings, `APP_` prefix, fail-fast `@model_validator` — see `src/app/config.py`
- **Hexagonal layers:** `domain` → `ports` (Protocol) → `adapters` (lazy SDK import + fakes) →
  `services` → `api`. No SDK/framework imports above the adapters layer.
- Add an external dependency = port + lazy adapter + fake, then branch in `container.py`.

## Style

- Ruff line-length 100, target py311, no `Any`/`dict`/`list` without concrete types
- Annotate all parameters AND return values (ruff `ANN`); tests exempt from `ANN`/`S101`
- JSON structured logging via `app.logging.get_logger(__name__)`, never `print`
- No comments in code — code must be self-documenting
- No `# type: ignore` without a documented reason
- `pre-commit` hooks run on every commit: ruff lint/format, hygiene hooks, mypy
