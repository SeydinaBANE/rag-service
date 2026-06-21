.PHONY: install lint format typecheck test cov run precommit load

BASE_URL ?= http://localhost:8000

install:
	uv sync --extra dev
	uv run pre-commit install

lint:
	uv run ruff check src tests
	uv run ruff format --check src tests

format:
	uv run ruff format src tests
	uv run ruff check --fix src tests

typecheck:
	uv run mypy

test:
	uv run pytest

cov:
	uv run pytest --cov-report=html

run:
	uv run uvicorn app.api.app:app --reload --port 8000

precommit:
	uv run pre-commit run --all-files

load:
	BASE_URL=$(BASE_URL) k6 run load/k6/load_test.js
