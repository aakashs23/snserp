# **Sri Naga Sai ERP – Backend Architecture & Database Schema (Version 1\)**

## **Purpose**

This document defines the backend architecture, database schema, authentication model, authorization rules, API structure, storage organization, security model, and event-driven workflows for Sri Naga Sai ERP.

This schema is designed to be scalable, normalized, and maintainable while minimizing future breaking changes.

---

# **1\. Backend Architecture**

Browser  
        │  
        ▼  
Next.js Frontend  
        │  
 REST API (HTTPS)  
        │  
        ▼  
FastAPI Backend  
        │  
 ├── Authentication Layer  
 ├── RBAC Middleware  
 ├── Business Services  
 ├── AI Service  
 ├── File Service  
 ├── Invoice Service  
 ├── Revenue Service  
 ├── Activity Logger  
        │  
        ▼  
PostgreSQL (Supabase)  
        │  
        ├── Supabase Storage  
        ├── ChromaDB  
        ├── PaddleOCR  
        ├── PyMuPDF  
        ├── Ollama  
        └── Qwen 3

---

# **2\. Database Tables**

---

## **users**

Stores application users.

| Column | Type | Constraints |
| ----- | ----- | ----- |
| id | UUID | PK (matches Supabase Auth UID) |
| full\_name | VARCHAR(120) | NOT NULL |
| email | VARCHAR(255) | UNIQUE |
| phone | VARCHAR(20) | NULL |
| role\_id | UUID | FK → roles.id |
| avatar\_url | TEXT | NULL |
| is\_active | BOOLEAN | DEFAULT TRUE |
| last\_login | TIMESTAMPTZ | NULL |
| created\_at | TIMESTAMPTZ | DEFAULT NOW() |
| updated\_at | TIMESTAMPTZ | DEFAULT NOW() |

---

## **roles**

| Column | Type |
| ----- | ----- |
| id | UUID |
| name | VARCHAR(50) |
| description | TEXT |

Default roles

* Admin  
* Accountant  
* Employee  
* Viewer

---

## **permissions**

| Column | Type |
| ----- | ----- |
| id | UUID |
| permission\_key | VARCHAR(100) |
| description | TEXT |

Example

document.create  
document.delete  
invoice.create  
invoice.edit  
invoice.delete  
user.manage  
activity.view

---

## **role\_permissions**

Many-to-many relationship.

| Column | Type |
| ----- | ----- |
| role\_id | UUID FK |
| permission\_id | UUID FK |

Composite Primary Key

(role\_id, permission\_id)

---

## **customers**

Stores companies receiving invoices.

| Column | Type |
| ----- | ----- |
| id | UUID |
| customer\_name | VARCHAR(150) |
| gst\_number | VARCHAR(20) |
| address | TEXT |
| email | VARCHAR(255) |
| phone | VARCHAR(20) |
| bank\_name | VARCHAR(120) |
| bank\_account | TEXT (Encrypted) |
| ifsc\_code | VARCHAR(20) |
| created\_at | TIMESTAMPTZ |

---

## **invoices**

| Column | Type |
| ----- | ----- |
| id | UUID |
| invoice\_number | VARCHAR(50) UNIQUE |
| customer\_id | UUID FK |
| invoice\_date | DATE |
| month\_of\_supply | DATE |
| payment\_mode | VARCHAR(30) |
| units | NUMERIC(15,3) |
| rate | NUMERIC(15,4) |
| gross\_amount | NUMERIC(15,2) |
|  |  |
|  |  |
| open\_access\_charges | NUMERIC(15,2) |
| net\_amount | NUMERIC(15,2) |
| notes | TEXT |
| pdf\_storage\_path | TEXT |
| status | VARCHAR(20) |
| payment\_date | DATE |
| created\_by | UUID FK users |
| created\_at | TIMESTAMPTZ |
| updated\_at | TIMESTAMPTZ |

---

## **documents**

Master document table.

| Column | Type |
| ----- | ----- |
| id | UUID |
| file\_name | VARCHAR(255) |
| original\_name | VARCHAR(255) |
| storage\_path | TEXT |
| file\_size | BIGINT |
| mime\_type | VARCHAR(120) |
| category | VARCHAR(50) |
| ai\_category | VARCHAR(80) |
| uploaded\_by | UUID FK |
| upload\_date | TIMESTAMPTZ |
| deleted\_at | TIMESTAMPTZ |
| checksum\_sha256 | VARCHAR(64) |
| version | INTEGER |
| is\_deleted | BOOLEAN |

---

## **document\_metadata**

| Column | Type |
| ----- | ----- |
| id | UUID |
| document\_id | UUID FK |
| title | TEXT |
| description | TEXT |
| keywords | TEXT\[\] |
| document\_date | DATE |
| page\_count | INTEGER |
| language | VARCHAR(20) |
| confidence\_score | NUMERIC(5,2) |

---

## **document\_ai**

Stores AI processing results.

| Column | Type |
| ----- | ----- |
| id | UUID |
| document\_id | UUID FK |
| ocr\_text | TEXT |
| summary | TEXT |
| embedding\_status | VARCHAR(30) |
| chromadb\_id | VARCHAR(120) |
| processed\_at | TIMESTAMPTZ |

---

## **activity\_logs**

| Column | Type |
| ----- | ----- |
| id | BIGSERIAL |
| user\_id | UUID |
| action | VARCHAR(100) |
| entity\_type | VARCHAR(50) |
| entity\_id | UUID |
| ip\_address | INET |
| user\_agent | TEXT |
| created\_at | TIMESTAMPTZ |

Retention

30 Days

---

## **ai\_chat\_sessions**

| Column | Type |
| ----- | ----- |
| id | UUID |
| user\_id | UUID |
| title | VARCHAR(200) |
| created\_at | TIMESTAMPTZ |

---

## **ai\_chat\_messages**

| Column | Type |
| ----- | ----- |
| id | UUID |
| session\_id | UUID |
| role | VARCHAR(20) |
| message | TEXT |
| created\_at | TIMESTAMPTZ |

---

## **notifications**

| Column | Type |
| ----- | ----- |
| id | UUID |
| user\_id | UUID |
| title | VARCHAR(200) |
| message | TEXT |
| is\_read | BOOLEAN |
| created\_at | TIMESTAMPTZ |

---

# **3\. Relationships**

roles  
   │  
   └────── users  
               │  
               ├──── invoices  
               ├──── documents  
               ├──── activity\_logs  
               ├──── notifications  
               └──── ai\_chat\_sessions

customers  
      │  
      └──── invoices

documents  
      │  
      ├──── document\_metadata  
      └──── document\_ai

roles  
      │  
      └──── role\_permissions  
                │  
                └──── permissions

---

# **4\. Database Indexes**

## **Users**

* email (Unique)  
* role\_id  
* is\_active

---

## **Customers**

* customer\_name  
* gst\_number

---

## **Documents**

* category  
* ai\_category  
* uploaded\_by  
* upload\_date DESC  
* is\_deleted  
* checksum\_sha256  
* file\_name

GIN Index

keywords

---

## **Invoices**

* invoice\_number (Unique)  
* customer\_id  
* invoice\_date  
* payment\_date  
* status  
* month\_of\_supply

---

## **Activity Logs**

* user\_id  
* created\_at DESC  
* action

---

## **AI Chat**

* session\_id  
* user\_id

---

# **5\. Authentication Model**

Authentication Provider

Supabase Auth

Authentication Methods

* Email \+ Password  
* Email Verification  
* Password Reset  
* Refresh Tokens  
* JWT Authentication

FastAPI validates Supabase JWT before every request.

No custom password storage.

---

# **6\. Authorization (RBAC)**

## **Admin**

Full system access.

Can

* Manage users  
* Upload/delete documents  
* Restore files  
* Create invoices  
* View analytics  
* View activity logs  
* Configure system

---

## **Accountant**

Can

* Manage invoices  
* Upload documents  
* View analytics  
* Use AI

Cannot

* Manage users  
* Delete users

---

## **Employee**

Can

* Upload documents  
* View documents  
* Use AI  
* View own activity

Cannot

* Delete invoices  
* Manage users

---

## **Viewer**

Read-only.

Cannot modify any data.

---

# **7\. Row Level Security (Supabase)**

Enable RLS on all application tables.

Rules

Users

* Users may read/update only their own profile.  
* Admin may read/update every user.

Documents

* Viewer: SELECT only.  
* Employee: SELECT \+ INSERT.  
* Accountant: SELECT \+ INSERT \+ UPDATE.  
* Admin: Full CRUD.

Invoices

* Viewer: Read only.  
* Employee: No access.  
* Accountant: CRUD.  
* Admin: CRUD.

Activity Logs

* Admin: View all.  
* Employee: View own logs only.

Notifications

* User may access only their own notifications.

---

# **8\. Sensitive Fields**

Encrypt at rest

* Customer bank account  
* IFSC (optional masking in UI)  
* Storage access tokens  
* Refresh tokens  
* API secrets  
* Environment variables

Never store

* Passwords  
* AI prompts  
* JWT refresh tokens in database

---

# **9\. Supabase Storage Structure**

documents/

    agreements/

    invoices/

    gst/

    loans/

    tax/

    reports/

    misc/

invoice-pdfs/

user-avatars/

temp/

trash/

Deleted files

trash/

      original\_path

      deletion\_timestamp

Permanent deletion after 30 days.

---

# **10\. Webhooks / Event Triggers**

## **Document Uploaded**

Trigger

Upload Complete

↓

Create DB Record

↓

OCR

↓

Metadata Extraction

↓

AI Categorization

↓

Generate Embeddings

↓

Store in ChromaDB

↓

Update Processing Status

---

## **Invoice Created**

Trigger

Generate PDF

↓

Store PDF

↓

Create Invoice Record

↓

Log Activity

---

## **User Login**

Trigger

Update Last Login

↓

Create Activity Log

---

## **Document Deleted**

Trigger

Move to Trash

↓

Set deleted\_at

↓

Schedule Permanent Deletion

---

# **11\. API Endpoints**

## **Authentication**

POST   /auth/login  
POST   /auth/logout  
POST   /auth/register  
POST   /auth/forgot-password  
POST   /auth/reset-password  
GET    /auth/me

---

## **Users**

GET    /users  
GET    /users/{id}  
POST   /users  
PATCH  /users/{id}  
DELETE /users/{id}

---

## **Documents**

GET    /documents  
GET    /documents/{id}  
POST   /documents/upload  
PATCH  /documents/{id}  
DELETE /documents/{id}  
POST   /documents/{id}/restore  
GET    /documents/{id}/download  
GET    /documents/trash  
DELETE /documents/{id}/permanent

---

## **Invoices**

GET    /invoices  
GET    /invoices/{id}  
POST   /invoices  
PATCH  /invoices/{id}  
DELETE /invoices/{id}  
GET    /invoices/{id}/pdf

---

## **Customers**

GET    /customers  
POST   /customers  
PATCH  /customers/{id}  
DELETE /customers/{id}

---

## **Dashboard**

GET /dashboard/overview  
GET /dashboard/revenue  
GET /dashboard/recent-activity

---

## **Revenue**

GET /revenue/monthly  
GET /revenue/yearly  
GET /revenue/customer

---

## **AI**

POST /ai/chat  
POST /ai/summarize  
POST /ai/search  
POST /ai/categorize  
POST /ai/metadata

---

## **Activity Logs**

GET /activity

---

## **Notifications**

GET /notifications  
PATCH /notifications/{id}/read

---

# **12\. Future Expansion**

The schema is intentionally designed to allow future modules without breaking existing tables.

Reserved modules include:

* SCADA Integration  
* Solar Plant Monitoring  
* Weather Data  
* Inventory Management  
* Procurement  
* Payroll  
* CRM  
* Vendor Management  
* Maintenance Scheduling  
* Multi-Company Support  
* Multi-Plant Support  
* Multi-Tenant SaaS Deployment

These modules can be added through new tables and services without requiring changes to the Version 1 schema.

