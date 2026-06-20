# **Technical Requirements Document (TRD)**

# **Sri Naga Sai ERP**

### **AI-Powered ERP & Intelligent Document Management System for Solar Companies**

**Version:** 1.0  
**Based on:** Product Requirements Document v1.0

---

# **1\. Technical Overview**

Sri Naga Sai ERP will be developed as a modern full-stack web application using a React-based frontend and a Python backend. The system is designed to be modular, secure, scalable, and AI-first, allowing future expansion into a complete ERP platform.

The architecture follows a client-server model with separate frontend, backend, database, AI processing layer, and cloud file storage.

---

# **2\. Technology Stack**

## **Frontend**

### **Framework**

* Next.js 15 (React)  
* TypeScript

### **UI Library**

* React  
* Tailwind CSS  
* shadcn/ui  
* Lucide React Icons

### **Charts**

* Recharts

### **Forms**

* React Hook Form  
* Zod Validation

### **State Management**

* TanStack Query  
* React Context API

### **File Upload**

* UploadThing (or direct Supabase Storage uploads)

---

## **Backend**

### **Runtime**

Python 3.12+

### **Framework**

FastAPI

Reasoning

* Extremely fast  
* Async support  
* Excellent API documentation  
* Strong AI ecosystem  
* Easy integration with OCR and LLMs

---

## **Database**

### **Primary Database**

PostgreSQL

### **Provider**

Supabase PostgreSQL

Reason

* Managed PostgreSQL  
* Automatic backups  
* Built-in authentication  
* Row Level Security  
* Scalable  
* Easy integration with storage

---

## **ORM**

SQLAlchemy 2.0

Database migrations

Alembic

---

## **Authentication**

Supabase Authentication

Authentication methods

* Email \+ Password  
* Password Reset

Role Based Access Control (RBAC)

Roles

* Admin  
* Employee  
* Accountant  
* Viewer

JWT tokens will be used between frontend and backend.

---

## **File Storage**

Supabase Storage

Supported file types

* PDF  
* DOCX  
* XLSX  
* CSV  
* PNG  
* JPG  
* JPEG

Storage organization

/company-documents

/Invoices

/Agreements

/Customers

/Government

/Bank

/GST

/TDS

/Receipts

/Miscellaneous

---

## **3\. AI Stack**

### **Large Language Model (LLM)**

**Primary Model**

* Qwen 3 (8B or 14B) running locally via Ollama

**Responsibilities**

* AI Chat Assistant  
* Document Summarization  
* Natural Language Question Answering  
* Invoice Validation  
* Metadata Extraction  
* AI-powered Document Categorization  
* Financial Insight Generation  
* Retrieval-Augmented Generation (RAG)

**Reason for Selection**

* Completely free and self-hosted  
* No API usage costs  
* Company documents remain private  
* Excellent reasoning performance  
* Easy integration with FastAPI using Ollama's REST API  
* Can be upgraded to larger Qwen models in the future without major code changes  
  ---

  ### **OCR**

**PaddleOCR**

**Responsibilities**

* Extract text from scanned PDFs  
* Extract text from uploaded images  
* Read invoices, receipts, GST certificates and bank statements  
* Pass extracted text to the embedding pipeline  
  ---

  ### **Embedding Model**

**Preferred Model**

* nomic-embed-text (served locally through Ollama)

**Alternative**

* Qwen3-Embedding

**Responsibilities**

* Generate embeddings for uploaded documents  
* Power semantic document search  
* Support Retrieval-Augmented Generation (RAG)

**Reason for Selection**

* Free  
* Local inference  
* High-quality embeddings  
* Fast retrieval  
* No cloud API required  
  ---

  ### **Vector Database**

**ChromaDB**

**Responsibilities**

* Store document embeddings  
* Perform similarity search  
* Retrieve relevant document chunks  
* Provide context to the LLM before response generation  
  ---

  ### **AI Orchestration Framework**

**LangChain**

**Responsibilities**

* Document loading  
* Document chunking  
* Embedding generation  
* Vector search  
* Retrieval pipeline  
* Prompt construction  
* Chat orchestration  
  ---

### **PDF Processing**

**PyMuPDF (fitz)**

**Responsibilities**

* Read PDF documents  
* Extract embedded text  
* Split large documents  
* Extract document metadata

---

## **4\. API Architecture**

The frontend communicates exclusively with the FastAPI backend.

The FastAPI backend coordinates all business logic and AI services.

Browser

↓

Next.js Frontend

↓

FastAPI Backend

↓

──────────────────────────────────────

Business Logic Layer

──────────────────────────────────────

↓

PostgreSQL (Supabase)

↓

Supabase Storage

↓

PaddleOCR

↓

PyMuPDF

↓

Embedding Model (nomic-embed-text)

↓

ChromaDB

↓

Qwen 3 (Ollama)

↓

AI Response

---

## **5\. Hosting & Deployment**

### **Frontend**

* Vercel

### **Backend**

* Railway

Alternative

* Render

### **Database**

* Supabase PostgreSQL

### **File Storage**

* Supabase Storage

### **AI Runtime**

* Ollama running on a dedicated local machine or self-hosted Linux server

**Version 1 contains no dependency on paid cloud AI APIs.**

---

## **6\. Third-Party Libraries & Services**

### **Required Services**

#### **Supabase**

Purpose

* PostgreSQL Database  
* Authentication  
* File Storage

---

#### **Ollama**

Purpose

* Local LLM inference  
* Local embedding inference  
* AI chat processing

---

#### **Qwen 3**

Purpose

* Chatbot  
* Document summarization  
* AI categorization  
* Metadata extraction  
* Financial question answering

---

#### **nomic-embed-text**

Purpose

* Local embedding generation  
* Semantic search  
* Retrieval-Augmented Generation (RAG)

---

#### **PaddleOCR**

Purpose

* OCR  
* Text extraction from scanned PDFs and images

---

#### **ChromaDB**

Purpose

* Vector database  
* Similarity search  
* Context retrieval

---

#### **LangChain**

Purpose

* RAG orchestration  
* Prompt management  
* Document processing pipeline

---

#### **PyMuPDF**

Purpose

* PDF parsing  
* Text extraction  
* Metadata extraction

---

#### **ReportLab**

Purpose

* Invoice PDF generation

---

#### **Pandas**

Purpose

* Read Excel  
* Read CSV  
* Financial calculations  
* Data processing

---

#### **OpenPyXL**

Purpose

* Excel reading  
* Excel writing  
* Spreadsheet automation

---

# **7\. Folder Structure**

sri-naga-sai-erp/

│

├── frontend/

│   ├── app/

│   ├── components/

│   ├── hooks/

│   ├── lib/

│   ├── services/

│   ├── types/

│   ├── styles/

│   ├── utils/

│   └── middleware.ts

│

├── backend/

│   ├── app/

│   │

│   ├── api/

│   ├── models/

│   ├── schemas/

│   ├── services/

│   ├── repositories/

│   ├── ai/

│   ├── auth/

│   ├── database/

│   ├── middleware/

│   ├── utils/

│   ├── config/

│   └── main.py

│

├── docs/

│

├── database/

│

├── scripts/

│

├── tests/

│

└── README.md

---

# **8\. Naming Conventions**

## **Files**

Use lowercase with hyphens

invoice-generator.tsx

document-search.tsx

financial-dashboard.tsx

---

## **React Components**

PascalCase

InvoiceCard

DashboardLayout

DocumentUploader

---

## **Functions**

camelCase

generateInvoice()

uploadDocument()

calculateGST()

---

## **Database Tables**

snake\_case

users

documents

invoices

invoice\_register

activity\_logs

customers

---

## **API Routes**

/api/auth

/api/invoices

/api/documents

/api/dashboard

/api/chat

/api/search

/api/upload

---

## **9\. Environment Variables**

### **Frontend**

NEXT\_PUBLIC\_SUPABASE\_URL=

NEXT\_PUBLIC\_SUPABASE\_ANON\_KEY=

NEXT\_PUBLIC\_API\_URL=

### **Backend**

DATABASE\_URL=

SUPABASE\_URL=

SUPABASE\_SERVICE\_KEY=

JWT\_SECRET=

CHROMA\_DB\_PATH=

UPLOAD\_DIRECTORY=

OCR\_LANGUAGE=en

OLLAMA\_BASE\_URL=http://localhost:11434

LLM\_MODEL=qwen3:8b

EMBEDDING\_MODEL=nomic-embed-text

APP\_ENV=development

CORS\_ORIGINS=

---

# **10\. Security Requirements**

Passwords

* Never stored in plaintext  
* Hashed using bcrypt (handled by Supabase Auth)

Authentication

* JWT tokens

Authorization

* Role Based Access Control

File Storage

* Private buckets only

Database

* Row Level Security

API

* Rate limiting  
* Request validation

HTTPS only

---

# **11\. Performance Requirements**

Dashboard load

\<2 seconds

Document upload

\<5 seconds

AI search

\<8 seconds

Invoice generation

\<3 seconds

PDF preview

\<2 seconds

Support

Minimum 100 concurrent users

---

# **12\. Logging & Monitoring**

Application Logs

* Login events  
* Uploads  
* Downloads  
* AI requests  
* Invoice creation  
* Errors

Monitoring

* Railway Logs  
* Supabase Logs

Future

* Sentry  
* PostHog Analytics

---

# **13\. Backup Strategy**

Database

Daily automatic Supabase backups

Documents

Supabase Storage redundancy

Retention

30-day recovery

Deleted documents

Soft delete

Trash bin

Permanent deletion after 30 days

---

## **14\. Technical Constraints**

### **Must Use**

* Next.js  
* FastAPI  
* PostgreSQL  
* Supabase  
* Ollama  
* Qwen 3  
* nomic-embed-text  
* PaddleOCR  
* ChromaDB  
* LangChain  
* PyMuPDF  
* TypeScript  
* Tailwind CSS

  ### **Must Not Use**

* Paid LLM APIs in Version 1  
* Firebase  
* MongoDB  
* PHP  
* jQuery  
* Local file storage in production  
* Plain JavaScript (TypeScript only)

## **AI Design Principles**

* All AI inference must run locally using Ollama.  
* No company documents should be transmitted to external AI providers in Version 1\.  
* Embeddings must be generated locally.  
* AI functionality should be encapsulated within a dedicated AI service layer to allow future migration to cloud providers if required.  
* The AI provider should be abstracted through an interface so that Qwen 3 can later be replaced with another model (e.g., OpenAI, Gemini, Claude) without affecting business logic.

---

# **15\. Future Technical Considerations**

The architecture should be designed so that the following features can be added without major refactoring:

* SCADA integration  
* Inverter APIs  
* Weather APIs  
* Customer Portal  
* Vendor Portal  
* Multi-company support  
* Inventory Management  
* Mobile application (React Native)  
* Email notifications  
* Background job processing  
* AI financial forecasting  
* Automated report generation  
* Workflow automation  
* Multi-language support

The backend should remain modular, with each new feature implemented as a separate service or module to ensure maintainability and scalability.

