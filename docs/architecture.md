# NIEPMD Audiology — Architecture

Living notes for the clinical portal. Implementation follows the Phase 1 plan: deterministic questionnaire + rules for care routing; AI only for grounded test explanation.

## 1. Design decisions (locked)

| Topic | Choice |
|-------|--------|
| LLM | Claude (Anthropic) for phrasing / RAG answers when a key is present; optional |
| Embeddings | Default **fastembed** (`BAAI/bge-small-en-v1.5`, 384-d) — local, no API key |
| Vector DB | Qdrant — used **only** by the AI Treatment Assistant |
| Questionnaire | Branching via `question_options.next_question_id` |
| Auth (v1) | Patients: registration per visit, no login. Staff/admin: JWT |
| Reports | Server-side PDF (reportlab) from persisted `report_json` |
| Deployment | Docker Compose (postgres, redis, qdrant, api, web) |

### Hard boundary

```
Patient path (must work if RAG/LLM are down)
  register → categories → questionnaire → rules → plan → PDF

AI path (optional enrichment)
  recommended test → retrieve chunks → Claude (or extract fallback) → disclaimer
```

If retrieval finds nothing, or the model fails after retrieval, the system serves admin static explanations or a generic holding message — never an ungrounded LLM answer.

## 2. Backend layout

```
backend/app/
├── main.py                 # FastAPI app, CORS, routers
├── config.py
├── api/
│   ├── deps.py             # JWT doctor / admin deps
│   └── routes/             # auth, patients, catalog, sessions,
│                           # recommendations, ai, reports, admin,
│                           # + assistant suite + legacy triage chat
├── models/                 # SQLAlchemy ORM + enums
├── schemas/                # Pydantic
├── services/
│   ├── questionnaire.py    # branching traversal (pure)
│   ├── clinical_rules.py   # deterministic rule engine (pure)
│   ├── report_service.py   # PDF
│   ├── clinical_seed_data.py
│   ├── test_catalog_data.py
│   └── ai/                 # chunking, embeddings, vector_store, rag_pipeline
├── agents/                 # specialist assistant suite (enquiry, booking, …)
├── db/
└── core/                   # security (bcrypt + JWT), redis
```

Migrations: `backend/alembic/versions/`

- `001_initial` — triage patients / concerns / test catalog  
- `002_assistant_suite` — services, slots, knowledge, agent conversations  
- `003_clinical_core` — profiles, doctors, question bank, rules, plans, reports, RAG docs  
- `004_test_catalog_detail` — preparation + duration on `test_catalog`  

## 3. Clinical data model (summary)

```
patients ──< patient_profiles (flow_type, child_subtype, consent)
doctors (role: audiologist | admin | ent)
treatment_categories ──< conditions ──< questions ──< question_options
                                              └ next_question_id (branch)
questionnaire_sessions ──< patient_answers
clinical_rules ──< recommended_tests (per rule)
treatment_plans (JSONB snapshot of tests at evaluation time)
medical_reports (pdf path + report_json)
hospital_documents → Qdrant chunks
ai_conversations (audit: prompt_context, response, source)
static_explanations (admin fallback by test_code)
```

Answer corrections on a completed session re-run `reachable_path`: orphaned branch answers are deleted and any existing plan for that session is dropped so results must be re-evaluated.

## 4. API map

### Auth (staff)

- `POST /api/auth/login`
- `POST /api/auth/refresh`
- `GET  /api/auth/me`

### Clinical patient path

- `POST /api/patients`
- `GET  /api/patients/{id}` · `GET /api/patients` (admin)
- `GET  /api/categories?flow_type=`
- `GET  /api/conditions?category_id=`
- `GET  /api/questions?condition_id=`
- `POST /api/sessions`
- `POST /api/sessions/{id}/answers`
- `GET  /api/sessions/{id}` · `…/summary`
- `POST /api/recommendations/evaluate`
- `GET  /api/recommendations/{session_id}`
- `POST /api/ai/explain-test`
- `GET  /api/ai/conversations/{session_id}` (staff)
- `GET  /api/ai/status`
- `POST /api/reports/generate`
- `GET  /api/reports/{id}` · `…/download`

### Admin (JWT admin role)

CRUD under `/api/admin/` for categories, conditions, questions, options, rules, doctors, documents (upload → index), static explanations, plus dashboard, AI logs, reports.

OpenAPI: `GET /docs` on the running API.

## 5. Frontend routes

```
/                              Landing
/register/relationship
/register
/chat/category
/chat/questionnaire
/chat/summary
/results/recommendations
/results/report

/admin/login
/admin/dashboard | questions | rules | documents | ai-logs | doctors | reports
```

Shared: `SafetyDisclaimerBanner`, `ProgressStepper`, `QuestionCard`, `TestExplanationCard`.

State: Zustand (`frontend/src/store/session.ts`). API client: `frontend/src/lib/api.ts`.

## 6. RAG pipeline

```
Admin upload (PDF/DOCX/TXT/MD)
  → extract + chunk (~500–800 chars, overlap)
  → embed (fastembed / openai / voyage)
  → Qdrant (payload: document_id, title, category, test_tags, text)

Runtime:
  query = test_name + tags + optional patient question
  → top-k with test_tags preference; unfiltered retry only if chunk mentions the test
  → Claude grounded on extracts, or formatted extracts if model down
  → else static_explanations, else generic holding message
  → log ai_conversations (source: rag | static_fallback | cached)
```

## 7. Seed content

`python scripts/seed.py` (idempotent sections):

- Legacy triage catalog + concern configs  
- Assistant suite (services, clinicians, slots, knowledge, …)  
- Clinical flow: categories, conditions, questions, rules  
- Test catalog upsert (preparation + duration)  
- Bootstrap admin account  

Refresh authored rules only (plans keep JSONB snapshots):

```bash
python scripts/seed.py --refresh-rules
```

## 8. Testing

| Suite | Command | Scope |
|-------|---------|-------|
| Unit | `pytest -q` | questionnaire, rules, seed integrity, agents, RAG helpers, catalog coverage |
| Smoke | `scripts/smoke_test.py` | full HTTP clinical + auth + admin path |
| RAG | `scripts/rag_test.py` | upload → index → grounded explain → delete |

## 9. Environment

See `backend/.env.example` and `frontend/.env.example`.

Important backend vars: `DATABASE_URL`, `REDIS_URL`, `QDRANT_URL`, `JWT_SECRET`, `EMBEDDING_PROVIDER`, `ANTHROPIC_API_KEY` (optional), `CORS_ORIGINS`.
