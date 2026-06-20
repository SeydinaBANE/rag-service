# CLAUDE.md

Ce fichier fournit des directives à Claude Code (claude.ai/code) lorsqu'il travaille sur le code de ce dépôt.

## Projet

Squelette de service Python de qualité production : architecture hexagonale, typage strict (mypy strict + ruff ANN), démarrage fail-fast. Généré depuis prod-skillpack. Fonctionne entièrement hors ligne par défaut (tous les providers à `fake`). Deux domaines fonctionnels cohabitent sur le même squelette : un exemple **greeter** (`/greet`) et un pipeline **RAG** (`/rag/index`, `/rag/query`).

## Commandes

L'outillage repose sur `uv` + un Makefile. Toujours passer par `uv run` (ou les cibles make), jamais `python`/`pytest` directement.

```bash
make install     # uv sync --extra dev (ajouter --extra rag pour les SDK anthropic/voyage/cohere)
make lint        # ruff check src tests
make format      # ruff format + ruff check --fix
make typecheck   # mypy strict (config dans pyproject [tool.mypy], cible le package "app")
make test        # pytest + seuil de couverture (échoue en dessous de 75 %)
make run         # uvicorn app.api.app:app --reload --port 8000
make precommit   # pre-commit run --all-files
make load        # k6 run load/k6/load_test.js (l'app doit tourner ; BASE_URL surchargeable)
```

Lancer un seul test : `uv run pytest tests/unit/test_api.py::test_greet_nominal`

Les tests d'intégration sont marqués `@pytest.mark.integration`. Pour ne lancer qu'eux : `uv run pytest -m integration`, ou pour les exclure : `-m "not integration"`.

Avant de rendre des modifications, le filet de qualité attendu est : `make lint && make typecheck && make test` tous au vert (cela reflète `.github/workflows/ci.yml`, qui exécute aussi `bandit` et `pip-audit`).

## Architecture

Sens strict des dépendances (hexagonal). Les couches internes n'importent jamais les couches externes, et **aucun import de SDK ou de framework n'est autorisé au-dessus de la couche adapters** :

```
domain/    types purs + erreurs métier (sous-classes de DomainError) ; ne dépend de rien
ports/     interfaces Protocol (GreeterPort + EmbedderPort/VectorStorePort/RerankerPort/GeneratorPort) ; aucun import de SDK/framework
adapters/  implémentations des ports + fakes ; SDK importés PARESSEUSEMENT dans les méthodes
services/  orchestration (GreetingService, RagService, chunking) ; dépend uniquement des ports, jamais des adapters
api/       app FastAPI ; /greet, /rag/index, /rag/query, en-têtes de sécurité, /healthz, /readyz, gestionnaires d'exceptions
config.py  pydantic-settings (préfixe APP_), @model_validator fail-fast
container.py  racine de composition : fabriques build_* + build_container
```

Conventions clés pour étendre ce code :

- **Ajouter une dépendance externe** = ajouter un port (Protocol dans `ports/`), un adapter paresseux + un fake dans `adapters/`, puis brancher dessus dans `container.py`. Rien d'autre ne change. Le skill `.claude/commands/add-port-adapter.md` codifie cette démarche.
- **Imports SDK paresseux** : les adapters importent leur SDK (ex. `httpx`) *à l'intérieur* de la méthode, pas en haut du module, pour que le package reste importable sans les dépendances optionnelles et que les tests tournent hors ligne. Voir `adapters/http_greeter.py`.
- **Config fail-fast** : `Settings._validate_production_safety` (un `@model_validator` pydantic) refuse de démarrer sur des combinaisons non sûres (ex. `provider=http` sans base URL). Ajouter les nouveaux invariants ici, pas dans les handlers de requêtes.
- **Flux d'erreurs** : les erreurs métier sont des sous-classes de `DomainError` levées dans `domain`/`services`, attrapées dans `api/app.py` via `@app.exception_handler(DomainError)` → 422. Ne pas attraper les erreurs domaine en cours de chaîne.
- **Câblage de la DI** : le `lifespan` FastAPI construit le `Container` une seule fois dans `app.state.container` ; les handlers le lisent via `get_container(request)`. Les appels sortants passent par `RetryPolicy` / `retry_call` (`adapters/retry.py`).

## Pipeline RAG

Le RAG suit exactement le même schéma hexagonal que le greeter : quatre ports (`EmbedderPort`, `VectorStorePort`, `RerankerPort`, `GeneratorPort`), des fakes déterministes hors ligne par défaut, des adapters réels derrière un import SDK paresseux. `RagService` (`services/rag.py`) orchestre :

- **Indexation** (`/rag/index`) : `chunk_text` (`services/chunking.py`) découpe chaque document → embed → `VectorStorePort.add`. Renvoie le nombre de chunks indexés.
- **Requête** (`/rag/query`) : embed de la question → `search` d'un pool de candidats (`retrieval_candidates`) → `rerank` jusqu'à `top_k` → `generate` d'une réponse ancrée. Pipeline : **retrieve → rerank → generate**.

Providers (tous `fake` par défaut, bascule via env ; nécessitent `uv sync --extra rag`) :

- `APP_EMBEDDER_PROVIDER=voyage` + `APP_VOYAGE_API_KEY` (modèle `voyage-3`).
- `APP_GENERATOR_PROVIDER=claude` + `APP_ANTHROPIC_API_KEY` (modèle `claude-opus-4-8`, SDK officiel `anthropic`).
- `APP_RERANKER_PROVIDER=cohere` + `APP_COHERE_API_KEY` (modèle `rerank-v3.5`).

Le vector store par défaut est un index cosinus en mémoire (`InMemoryVectorStore`) ; pour pgvector/Qdrant, ajouter un adapter et brancher dans `build_vector_store`. Les invariants RAG (dimensions, chunk_size/overlap, top_k, clés API requises selon le provider) sont validés dans `Settings._validate_rag`, appelé par `_validate_production_safety`.

## Conventions imposées par l'outillage

- ruff line-length 100, cible py311 ; le jeu de règles inclut `ANN` (tous les paramètres + retours doivent être annotés). Les tests sont exemptés de `ANN`/`S101`.
- mypy strict, `disallow_any_generics`, plugin pydantic. Utiliser des types concrets, pas de `Any`/`dict`/`list` nus.
- Les tests sont dans `tests/unit` et `tests/integration` ; les nommer `test_<fonction>_<cas>`. Chaque adapter a un fake pour garder les tests hors ligne.
