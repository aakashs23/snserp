# Sri Naga Sai ERP – Project Context

## Project Overview

Sri Naga Sai ERP is an AI-powered internal ERP system built specifically for Sri Naga Sai Energy, a solar power generation company in India.

This is not a generic ERP.

The application replaces spreadsheets, folders and manual document handling with a centralized web platform that includes AI-powered document understanding.

The ERP is intended for internal company use.

---

# Primary Objectives

- Centralized document management
- Invoice generation
- Revenue tracking
- Customer management
- Loan management
- AI-powered document search
- AI-powered document summarization
- OCR
- Metadata extraction
- Secure role-based access control

---

# Tech Stack

## Frontend

- Next.js 15
- React
- TypeScript
- Tailwind CSS
- shadcn/ui
- TanStack Query
- React Hook Form
- Recharts

## Backend

- FastAPI
- SQLAlchemy
- Alembic

## Database

- PostgreSQL
- Supabase

## Authentication

- Supabase Auth
- RBAC

## Storage

- Supabase Storage

---

# AI Architecture

Current architecture:

Upload

↓

Storage

↓

OCR (PaddleOCR)

↓

PyMuPDF (PDF extraction)

↓

Metadata Extraction

↓

Semantic Chunking

↓

Embeddings

↓

ChromaDB

↓

Hybrid Retrieval

↓

Cross Encoder Reranking

↓

LLM

↓

Structured Response with Citations

Supported document types:

- PDF
- DOCX
- XLSX
- CSV
- JPG
- PNG

---

# AI Provider

Current provider:

Gemini

Fallback:

Grok

Architecture is provider-independent.

Business logic must never directly call a provider.

All AI operations must go through the AI Service layer.

---

# RAG Pipeline

Current pipeline includes:

- OCR
- Metadata extraction
- Semantic chunking
- Hybrid retrieval
- PostgreSQL metadata search
- ChromaDB vector search
- Cross encoder reranking
- Conversation memory
- Structured citations

Always preserve this architecture.

---

# Current Features

Implemented modules:

- Authentication
- RBAC
- Dashboard
- Revenue dashboard
- Customers
- Loans
- Monthly calculator
- Invoice Generator
- Invoice Register
- Document Management
- AI Assistant
- Notifications
- Activity Logs
- Settings

---

# User Roles

Admin

- Full access

Employee

- Same as Admin except:
    - Cannot manage users
    - Cannot view activity logs

Accountant

- View only assigned documents
- AI Assistant available
- Invoice register available
- No invoice generation
- No revenue dashboard
- No loan module
- No customer editing
- No uploads

Viewer

- View only assigned documents
- Read-only access
- No uploads
- No editing
- No deletes

---

# Document Permissions

RBAC determines:

"What can the user do?"

Document Permissions determine:

"Which documents can the user access?"

Both checks must always pass.

---

# Coding Standards

Backend:

- FastAPI
- SQLAlchemy
- Dependency Injection where appropriate
- Modular services
- Clean Architecture
- REST APIs
- Proper exception handling

Frontend:

- TypeScript
- Reusable components
- TanStack Query
- React Hook Form
- Tailwind
- shadcn/ui

Never introduce unnecessary dependencies.

---

# Design Principles

Financial calculations must never use AI.

Always calculate using deterministic Python code.

Use AI only for:

- Search
- OCR
- Categorization
- Metadata extraction
- Summaries
- Document understanding

---

# Performance Principles

Prefer:

- Server-side pagination
- Indexed queries
- Cached data
- Parallel requests

Avoid:

- N+1 queries
- Duplicate requests
- Large synchronous operations

---

# Security Principles

Never bypass RBAC.

Never bypass Document Permissions.

Never expose unauthorized documents.

Never expose unauthorized AI retrieval.

Validate all uploads.

Never trust frontend permissions.

---

# UI Principles

Inspired by:

Pulze.io

Style:

- Modern
- Professional
- Corporate
- Minimal

Use:

- Cards
- Tables
- Drawers
- Sidebars

Maintain visual consistency.

---

# Current Project Status

Version:

1.0 Release Candidate

Core functionality is complete.

Only bug fixes, performance improvements and production hardening should be implemented unless explicitly requested.

Avoid major architectural changes.

---

# Important Rules

Before making changes:

1. Read the relevant documentation in `/docs`.
2. Understand the existing implementation.
3. Do not redesign working systems.
4. Implement one phase at a time.
5. Test before completing.
6. Preserve existing functionality.
7. Never modify unrelated modules.
8. Explain architectural decisions before major changes.
9. If a change causes regressions, revert only that change.
10. Stop after completing the requested phase.