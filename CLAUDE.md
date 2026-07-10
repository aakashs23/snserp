# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Working rules

- Read [docs/09 Project Context.md](docs/09%20Project%20Context.md) before coding. It is the most current statement of intent and overrides the older numbered docs where they conflict.
- Status: **1.0 Release Candidate.** Core functionality is complete. Bug fixes, performance, and production hardening only — no major architectural changes unless explicitly requested.
- Preserve the database schema, the AI architecture, RBAC, and existing features unless explicitly instructed otherwise.
- Implement only the requested phase. No broad refactors, no unrelated files.
- Explain significant design decisions before implementing them.
- Financial calculations are always deterministic Python (`Decimal`), never AI. AI is only for search, OCR, categorization, metadata extraction, summaries, and document understanding.
- Two authorization checks must both pass: RBAC ("what can this user do?") and `DocumentPermission` ("which documents can they see?").

### Where the docs conflict with the code

Docs 03 and 05 predate doc 09; the code follows doc 09. Per 09 and the implementation: **accountant** cannot upload, generate invoices, edit customers, or see revenue/loans — only assigned documents, the invoice register, and AI. **Employee** is admin-minus-user-management-and-activity-logs. Doc 03's role table and doc 05's §6 both say otherwise. Trust doc 09 and the `RequireRole` calls.

## Commands

Backend (run from `backend/`, venv at `backend/venv`):

```bash
source venv/bin/activate
uvicorn main:app --reload          # http://localhost:8000/docs
pytest tests/                      # the only real test suite
pytest tests/test_chroma_utils.py::test_name   # single test
alembic revision --autogenerate -m "msg"
alembic upgrade head
```

Frontend (run from `frontend/`):

```bash
npm run dev
npm run build   # runs check:dashboard-pages first, then next build
npm run lint
```

`backend/test_api.py`, `test_export.py`, `test_stats.py` are ad-hoc scripts, not pytest tests. `test_stats.py` is stale (imports `SessionLocal`, which no longer exists).

## Architecture

Three tiers: Next.js 16 frontend → FastAPI backend → Supabase Postgres. ChromaDB (local, on-disk) holds document embeddings. Supabase Storage holds the uploaded files.

**Auth is not local JWT verification.** `validate_supabase_jwt` ([supabase_jwt.py](backend/app/auth/supabase_jwt.py)) round-trips the bearer token to the Supabase Auth API, then `get_current_user` looks the user up in the local `users` table by that `sub`. A user existing in Supabase Auth but not in `users` gets a 401 — registration must write both. Two RBAC helpers exist and do the same thing: `RequireRole(["admin"])` (class, `middleware/rbac.py`) and `require_roles([...])` (factory, `middleware/auth.py`). Use whichever the neighbouring endpoints use.

**AI providers are swappable via env, never imported directly.** Business code calls `ai_generate()` / `ai_embed()` from [ai_service.py](backend/app/services/ai_service.py), which resolves `AI_PRIMARY_PROVIDER` → `AI_FALLBACK_PROVIDER` (ollama | gemini | grok), retries transient errors 3× with backoff, then fails over. Never import `google.genai`, `openai`, or `langchain_ollama` outside `ai_service.py`.

**Document ingestion** ([ai_pipeline.py](backend/app/services/ai_pipeline.py), fired as a FastAPI `BackgroundTasks` job from `POST /api/v1/documents/upload`): extract text (PyMuPDF for PDFs, zipfile+ElementTree for .docx, PaddleOCR for images and for PDFs yielding <50 chars) → LLM metadata extraction into `DocumentMetadata` → `semantic_chunk_pages` → embed → ChromaDB. Chroma indexing is best-effort: a failure (typically an embedding-dimension mismatch after switching providers) logs a warning, leaves `chromadb_id` null, and still commits OCR text and metadata.

**Chat/RAG** ([chat.py](backend/app/api/chat.py) + [rag_service.py](backend/app/services/rag_service.py)): rewrite query as standalone using history → permission-filter doc IDs → expand into 3 query variants → Chroma top-20 per variant → Postgres keyword boost over metadata → OCR-text fallback → cross-encoder rerank to top-5 → pull ±1 neighbour chunks → dedupe/merge → generate. The LLM appends `[CONFIDENCE: 0.85]`, stripped by `extract_confidence`. Permission filtering happens *before* retrieval: `viewer`/`accountant` only see approved docs explicitly shared via `DocumentPermission`.

`BaseRepository` / `BaseService` (generic async CRUD over any model) exist but most API routers query SQLAlchemy directly. Don't retrofit.

## Gotchas

- **The root `.env` is the only one that loads.** `settings.py` computes `PROJECT_ROOT` as three parents up and points `env_file` there. `backend/.env` is stale and ignored.
- Both `chat.py` and `ai_pipeline.py` open their own `chromadb.PersistentClient` at import time on the `snserp_documents` collection.
- Switching embedding models invalidates the Chroma collection. `ensure_chroma_collection` recreates it on a dimension mismatch at startup, but existing vectors are lost.
- `requirements.txt` omits `google-genai`, `openai`, and `sentence-transformers` even though `ai_service.py` and `rag_service.py` import them. They're in the venv; add them if you touch that file.
- The root `ai/` package is unimplemented stubs (`raise NotImplementedError`). Nothing imports it. The real AI code lives in `backend/app/services/`.
- `frontend/AGENTS.md`: this Next.js version has breaking changes vs. training data — read `node_modules/next/dist/docs/` before writing frontend code.
- New models must be imported in `app/models/__init__.py` or Alembic autogenerate won't see them.
