# RAG Service — Vision & Architecture

## Le probleme

Exposer une capacite de question-reponse ancree (retrieval-augmented generation) derriere une API
HTTP, de qualite production : typage strict, demarrage fail-fast, observabilite, et zero dependance
externe obligatoire pour developper et tester.

## La proposition

Un service FastAPI hexagonal qui indexe des documents puis repond a des questions en s'appuyant sur
le contexte recupere — chaque dependance externe (embeddings, vector store, reranker, LLM) est
abstraite derriere un port et remplacable par un fake deterministe.

## Architecture

Flux d'une requete RAG :

```
POST /rag/index  -> chunking -> embed -> vector store
POST /rag/query  -> embed question -> retrieve (pool de candidats) -> rerank -> generate -> reponse ancree
```

Sens strict des dependances (hexagonal) : `domain` → `ports` → `adapters` → `services` → `api`.
Aucun import de SDK/framework au-dessus de la couche adapters ; les SDK sont importes paresseusement
dans les methodes des adapters pour rester importable et testable hors-ligne.

## Modules (`src/app/`)

- `config.py` — configuration pydantic-settings (prefixe `APP_`), validateur fail-fast
- `logging.py` — logging structure JSON + `get_logger`
- `domain/` — types purs + erreurs metier (`DomainError`)
- `ports/` — interfaces Protocol (`GreeterPort`, `EmbedderPort`, `VectorStorePort`, `RerankerPort`, `GeneratorPort`)
- `adapters/` — implementations reelles (Claude, Voyage, Cohere, HTTP) + fakes + `retry.py`
- `services/` — orchestration (`GreetingService`, `RagService`, `chunking`)
- `api/app.py` — application FastAPI (`/greet`, `/rag/index`, `/rag/query`, `/healthz`, `/readyz`)
- `container.py` — racine de composition (`build_*` / `build_container`)

## Principes de conception

- Typage strict (mypy strict, `disallow_any_generics`), aucun service externe requis pour les tests unitaires
- Fail-fast : refus de demarrer sur une config non sure (provider reel sans cle, etc.)
- Appels sortants bornes par timeout + retry (`adapters/retry.py`)
- Probes distinctes : `/healthz` liveness O(1), `/readyz` sonde la dependance avec etat (vector store)
- Vector store par defaut en memoire ; remplacable par pgvector/Qdrant via un adapter
