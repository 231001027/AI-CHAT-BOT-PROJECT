# NIEPMD Audiology Department

Patient guidance portal and staff tools for the NIEPMD Audiology Department.

The clinically essential path — **registration → questionnaire → recommendations → PDF report** — is deterministic. The AI Treatment Assistant only explains recommended tests using hospital documents (RAG), and degrades to admin-authored static text when retrieval or the LLM is unavailable. It never chooses tests or diagnoses.

## Stack

| Layer | Tech |
|-------|------|
| Frontend | React 18, TypeScript, Vite, Tailwind, ShadCN-style UI, Zustand, Zod |
| Backend | FastAPI, SQLAlchemy 2 (async), Alembic, Pydantic |
| Data | PostgreSQL 16, Redis 7 |
| RAG | Qdrant + fastembed (local embeddings) + Anthropic Claude (optional) |

## Repository layout

```
├── frontend/          # Vite React app (patient + admin UI)
├── backend/           # FastAPI app (clinical core, agent suite, RAG)
├── docs/              # Architecture notes
├── docker-compose.yml # postgres, redis, qdrant, api, web
└── README.md
```

## Quick start (Docker Compose)

```bash
cp .env.example .env          # optional: ANTHROPIC_API_KEY, JWT_SECRET
docker compose up --build
```

| Service | URL |
|---------|-----|
| Frontend | http://localhost:5173 |
| API + OpenAPI | http://localhost:8000 /docs |
| Postgres (host) | `localhost:55432` → container `5432` |
| Redis | `localhost:6379` |
| Qdrant | http://localhost:6333 |

Compose maps Postgres to **55432** on the host so a local PostgreSQL on 5432 cannot shadow the container.

On first API start Compose runs `alembic upgrade head` and `python scripts/seed.py`.

**Bootstrap admin:** `admin@niepmd.gov.in` / `ChangeMe!2026` — change this password before any shared deploy.

## Local development (split)

### Infrastructure

```bash
docker compose up -d postgres redis qdrant
```

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env

# Point at the compose Postgres port on this machine:
export DATABASE_URL=postgresql+asyncpg://nipmed:nipmed@localhost:55432/nipmed
export REDIS_URL=redis://localhost:6379/0
export QDRANT_URL=http://localhost:6333
export JWT_SECRET=dev-only-change-me

alembic upgrade head
python scripts/seed.py
uvicorn app.main:app --reload --host 127.0.0.1 --port 8010
```

### Frontend

```bash
cd frontend
cp .env.example .env   # VITE_API_BASE_URL=http://127.0.0.1:8010
npm install
npm run dev
```

Root scripts forward to the frontend:

```bash
npm run dev      # → frontend
npm run build
```

## Patient flow

1. `/register/relationship` — Myself / My Child / Someone Else  
2. `/register` — demographics (+ guardian consent for child)  
3. `/chat/category` → condition  
4. `/chat/questionnaire` — branching questions  
5. `/chat/summary` — review (answers can be corrected)  
6. `/results/recommendations` — rule-engine tests + optional AI explanations  
7. `/results/report` — structured report + PDF download  

## Admin

`/admin/login` → dashboard, question bank, rules, RAG documents, AI logs, doctors, reports.

## Verification

```bash
# Unit tests (no DB required for pure logic)
cd backend && source .venv/bin/activate && pytest -q

# Frontend
cd frontend && npm run typecheck && npm run build

# Live API smoke (API must be running)
cd backend && python scripts/smoke_test.py http://127.0.0.1:8010
python scripts/rag_test.py http://127.0.0.1:8010
```

Latest local verification:

| Check | Result |
|-------|--------|
| `pytest` | 416 passed |
| Frontend typecheck + build | passed |
| `smoke_test.py` | 100/100 |
| `rag_test.py` | 28/28 |

## Safety boundaries

- Recommendations come only from the deterministic clinical rule engine.
- RAG explanations must be grounded in indexed hospital documents (or static admin text).
- Safety disclaimer is shown on AI output and embedded in the PDF report.
- Child registration requires explicit guardian consent.
- AI conversation logs are staff-only (JWT).

## Docs

- [Architecture](docs/architecture.md) — schema, API map, RAG design, folder structure  
- [Backend README](backend/README.md) — migrations, seed, env vars  

## License / institute

Built for the National Institute for Empowerment of Persons with Multiple Disabilities (NIEPMD) — Audiology Department.
