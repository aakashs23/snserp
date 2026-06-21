# AI Instructions

You are developing **Sri Naga Sai ERP**.

Before making any code changes:

1. Read every document inside the `/docs` folder.
2. Treat those documents as the single source of truth.
3. Never invent architecture that contradicts the documentation.
4. Never modify the database schema unless explicitly instructed.
5. Never skip implementation phases.
6. Implement only the requested phase from the Implementation Plan.
7. Test every feature before considering it complete.
8. Follow Clean Architecture and SOLID principles.
9. Use strong TypeScript and Python typing.
10. Keep business logic deterministic. AI must only be used for document understanding, search, OCR, categorization, metadata extraction, summarization, and RAG.

Project Stack

- Frontend: Next.js 15, React, TypeScript, Tailwind CSS, shadcn/ui
- Backend: FastAPI, SQLAlchemy, Alembic
- Database: PostgreSQL (Supabase)
- Authentication: Supabase Auth
- Storage: Supabase Storage
- AI: Ollama, Qwen 3, PaddleOCR, ChromaDB, LangChain, PyMuPDF

Rules

- Never generate placeholder code.
- Never leave TODO comments for required functionality.
- Follow the Backend Schema exactly.
- Follow the UI/UX Design Brief exactly.
- Follow the App Flow exactly.
- Every API endpoint must match the documented specification.
- Every completed feature must compile and be tested.
- Stop after completing the requested phase and summarize the work completed.