.PHONY: init install build lint format typecheck test cov run precommit load docker-up docker-down

BASE_URL ?= http://localhost:8000

init: install

install:
	uv sync --extra dev
	uv run pre-commit install

build: lint typecheck test

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

docker-up:
	docker compose up --build

docker-down:
	docker compose down
