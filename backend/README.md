# NIEPMD Audiology — Backend

FastAPI service for the NIEPMD Audiology Department portal.

**Hard design rule:** test recommendations come only from the deterministic clinical rule engine (`clinical_rules.py` + seeded `clinical_rules` rows). Claude / RAG never choose tests. The AI Treatment Assistant explains recommended tests from indexed hospital documents, with static fallbacks.

## Stack

- FastAPI + Uvicorn  
- PostgreSQL + SQLAlchemy 2.0 (async) + Alembic  
- Redis (chat / session cache for assistant suite)  
- Qdrant + fastembed (RAG)  
- Anthropic SDK (optional LLM)  
- reportlab (PDF) · pypdf / python-docx (ingestion)  
- pytest  

## Layout

```
backend/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── api/routes/          # clinical + admin + assistants + legacy triage
│   ├── agents/              # specialist assistants
│   ├── models/ · schemas/
│   ├── services/
│   │   ├── questionnaire.py · clinical_rules.py · report_service.py
│   │   └── ai/              # rag_pipeline, embeddings, vector_store, chunking
│   ├── db/ · core/
├── alembic/versions/        # 001 … 004
├── scripts/
│   ├── seed.py
│   ├── smoke_test.py
│   └── rag_test.py
├── tests/
├── Dockerfile
├── requirements.txt
└── .env.example
```

Prefer this package over legacy `backend/fastapi/` and `backend/node/`.

## Quick start

From the **repo root** (recommended):

```bash
docker compose up --build
```

API: http://localhost:8000 · docs: `/docs`

### Local API against Compose infra

Host Postgres is published on **55432** (see root `docker-compose.yml`).

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env

export DATABASE_URL=postgresql+asyncpg://nipmed:nipmed@localhost:55432/nipmed
export REDIS_URL=redis://localhost:6379/0
export QDRANT_URL=http://localhost:6333
export JWT_SECRET=dev-only-change-me

alembic upgrade head
python scripts/seed.py
uvicorn app.main:app --reload --host 127.0.0.1 --port 8010
```

Bootstrap admin (seeded): `admin@niepmd.gov.in` / `ChangeMe!2026`.

## Migrations

```bash
alembic upgrade head
alembic downgrade -1   # one step, if needed
```

| Revision | Purpose |
|----------|---------|
| 001 | Initial triage schema |
| 002 | Assistant suite |
| 003 | Clinical core (questionnaire, rules, reports, RAG docs) |
| 004 | Test catalog preparation / duration |

## Seed

```bash
python scripts/seed.py
python scripts/seed.py --refresh-rules   # replace rule definitions only
```

Treatment plans store JSONB snapshots, so refreshing rules does not rewrite past patient advice.

## Tests

```bash
pytest -q
python scripts/smoke_test.py http://127.0.0.1:8010
python scripts/rag_test.py http://127.0.0.1:8010
```

## Main clinical endpoints

| Method | Path | Notes |
|--------|------|-------|
| `POST` | `/api/patients` | Consent required for child |
| `GET` | `/api/categories` | `?flow_type=adult\|child` |
| `GET` | `/api/conditions` | `?category_id=` |
| `GET` | `/api/questions` | `?condition_id=` |
| `POST` | `/api/sessions` | Start questionnaire |
| `POST` | `/api/sessions/{id}/answers` | Next question or complete; corrections allowed |
| `POST` | `/api/recommendations/evaluate` | Rules engine |
| `POST` | `/api/ai/explain-test` | RAG / static fallback |
| `POST` | `/api/reports/generate` | PDF + JSON |
| `POST` | `/api/auth/login` | Staff JWT |
| `*` | `/api/admin/…` | Admin CRUD + document upload |

Full OpenAPI: `/docs`.

## Environment

See `.env.example`. Notable keys:

- `DATABASE_URL`, `REDIS_URL`, `QDRANT_URL`  
- `JWT_SECRET`, `CORS_ORIGINS`  
- `EMBEDDING_PROVIDER` (`fastembed` default), `EMBEDDING_MODEL`, `EMBEDDING_DIMENSIONS`  
- `ANTHROPIC_API_KEY` (optional — RAG falls back to extracts / static text)  

## CORS

```
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

## Related docs

- [Root README](../README.md)  
- [Architecture](../docs/architecture.md)  
