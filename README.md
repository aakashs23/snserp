# Sri Naga Sai ERP

**AI-Powered ERP & Intelligent Document Management System for Solar Companies**

> *Smart Business Management Powered by AI.*

---

## Overview

Sri Naga Sai ERP is a modern, AI-powered Enterprise Resource Planning platform designed specifically for small and medium-sized solar companies. It centralizes document storage, invoice generation, financial tracking, and intelligent document retrieval into a single secure web application.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | Next.js 15, TypeScript, Tailwind CSS, shadcn/ui, Recharts |
| **Backend** | FastAPI (Python 3.12+), SQLAlchemy 2.0, Alembic |
| **Database** | PostgreSQL (Supabase) |
| **Storage** | Supabase Storage |
| **Auth** | Supabase Auth (JWT + TOTP 2FA) |
| **AI / LLM** | Qwen 3 (8B) via Ollama (100% local) |
| **Embeddings** | nomic-embed-text via Ollama |
| **Vector DB** | ChromaDB |
| **OCR** | PaddleOCR |
| **PDF Parsing** | PyMuPDF |
| **AI Orchestration** | LangChain |

## Project Structure

```
snserp/
├── frontend/          # Next.js 15 + TypeScript
├── backend/           # FastAPI + Python 3.12+
├── ai/                # AI services (OCR, embeddings, chat, RAG)
├── docs/              # Documentation
├── scripts/           # Utility scripts
└── tests/             # Test suites
```

## Getting Started

### Prerequisites

- **Node.js** 20+
- **Python** 3.12+
- **Ollama** (with `qwen3:8b` and `nomic-embed-text` models)
- **Supabase** project (PostgreSQL + Storage + Auth)

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
# Open http://localhost:3000
```

### Backend Setup

```bash
cd backend
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp ../.env.example .env  # Edit with your config
uvicorn main:app --reload
# Open http://localhost:8000/docs
```

### AI Setup

```bash
# Install and start Ollama
ollama pull qwen3:8b
ollama pull nomic-embed-text
```

## Environment Variables

Copy `.env.example` to `.env` and fill in your values. See the file for all required configuration.

## Documentation

All project documentation is in the `docs/` directory:

- [PRD](docs/01%20PRD%20SNS%20ERP.md)
- [TRD](docs/02%20TRD%20SNS%20ERP.md)
- [App Flow](docs/03%20App%20Flow%20SNS%20ERP.md)
- [UI/UX Design Brief](docs/04%20UI_UX%20Design%20Brief%20SNS%20ERP.md)
- [Backend Schema](docs/05%20Backend%20Schema%20SNS%20ERP.md)
- [Implementation Plan](docs/06%20Implementation%20Plan%20SNS%20ERP.md)

## License

Proprietary — Sri Naga Sai Energy © 2026