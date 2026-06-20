# **Sri Naga Sai ERP – Application Flow Document (Version 1\)**

## **Purpose**

This document defines how users navigate through Sri Naga Sai ERP, including authentication, page hierarchy, navigation patterns, key user journeys, redirects, and application states.

The objective is to ensure every screen is connected logically and provides a consistent user experience.

---

# **1\. Application Structure**

Landing  
│  
├── Login  
├── Register (Development Only)  
├── Forgot Password  
│  
└── Dashboard  
      │  
      ├── Dashboard Home  
      ├── Documents  
      │      ├── Upload  
      │      ├── Document Details  
      │      ├── Preview  
      │      └── Trash  
      │  
      ├── Invoice Generator  
      ├── Invoice Register  
      ├── Revenue Dashboard  
      ├── Monthly Calculator  
      ├── AI Assistant  
      ├── Activity Logs  
      ├── User Management (Admin)  
      └── Settings

---

# **2\. Screens / Pages**

## **Authentication**

### **Login**

Purpose

* Authenticate existing users  
* Redirect authenticated users to Dashboard

Actions

* Login  
* Forgot Password  
* Register (Development Only)

---

### **Register (Development Only)**

Purpose

Create new user accounts during development.

Actions

* Create Account  
* Return to Login

---

### **Forgot Password**

Purpose

Allow users to request a password reset email.

Actions

* Submit Email  
* Return to Login

---

## **Dashboard**

Purpose

Provide a high-level overview of business performance.

Widgets

* Monthly Revenue  
* Yearly Revenue  
* Uploaded Documents  
* Invoice Count  
* Loan Details  
* Recent Activity  
* Quick Actions

Quick Actions

* Upload Document  
* Create Invoice  
* Open AI Assistant  
* Revenue Dashboard

---

## **Document Management**

Purpose

Central repository for company documents.

Features

* Search  
* Filters  
* Upload  
* Rename  
* Download  
* Delete  
* AI Category  
* Metadata  
* OCR Status

Views

* Grid View  
* Table View

---

## **Upload Document**

Purpose

Upload company documents.

Flow

Select File

↓

Upload

↓

OCR

↓

Metadata Extraction

↓

Embedding

↓

AI Categorization

↓

Stored Successfully

---

## **Document Details**

Purpose

Display complete document information.

Sections

* Preview  
* Metadata  
* AI Summary  
* OCR Text  
* Version Information  
* Activity History

Actions

* Rename  
* Download  
* Delete  
* Restore (if in Trash)

---

## **Trash**

Purpose

Store deleted files for 30 days.

Actions

* Restore  
* Permanently Delete

---

## **Invoice Generator**

Purpose

Generate deterministic invoices.

Fields

* Customer  
* Date  
* Invoice Number  
* Mode of Payment  
* Month of Supply  
* Units  
* Rate  
* Amount  
* GST  
* TDS  
* Open Access Charges  
* Notes  
* Bank Details

Actions

* Preview Invoice  
* Save  
* Generate PDF  
* Cancel

---

## **Invoice Register**

Purpose

Manage all invoices.

Columns

* Invoice Number  
* Customer  
* Financial Year  
* Amount  
* Payment Status  
* Payment Date  
* Download

Actions

* Search  
* Filter  
* Download  
* View Details

---

## **Revenue Dashboard**

Purpose

Business analytics.

Charts

* Monthly Revenue  
* Yearly Revenue  
* Revenue by Customer  
* Paid vs Pending  
* Revenue Trend

---

## **Monthly Calculator**

Purpose

Calculate monthly billing values.

Calculations

* Gross Amount  
* GST  
* TDS  
* Open Access Charges  
* Net Amount  
* Final Payable

Results are generated using deterministic backend calculations.

---

## **AI Assistant**

Purpose

Natural language interaction with company documents.

Example Queries

* Show Goldi invoices from March  
* Summarize this agreement  
* Find latest GST document  
* Show Project XYZ files  
* Highest revenue customer

Responses include

* Citations  
* Related Documents  
* AI Summary

---

## **Activity Logs**

Purpose

Maintain an audit trail.  
Activity Logs can reset every 30 days

Tracks

* Login  
* Logout  
* Upload  
* Download  
* Delete  
* Restore  
* Invoice Creation  
* User Actions

---

## **User Management (Admin Only)**

Purpose

Manage ERP users.

Actions

* Add User  
* Disable User  
* Change Role  
* Reset Password  
* Have access to entire system

---

## **Settings**

Sections

* Profile  
* Password  
* Notifications  
* Company Information  
* AI Configuration (future)  
* System Preferences

---

# **3\. Navigation Structure**

## **Primary Navigation**

Automatically show and hide Left Sidebar like MacOS feature

* Dashboard  
* Documents  
* Invoice Generator  
* Invoice Register  
* Revenue Dashboard  
* Monthly Calculator  
* AI Assistant  
* Activity Logs

Admin Only

* User Management

Bottom of Sidebar

* Settings  
* Logout

---

## **Top Navigation**

Contains

* Search  
* Notifications  
* User Profile  
* Theme Toggle

---

## **Secondary Navigation**

Document Details

Tabs

* Overview  
* Preview  
* Metadata  
* OCR  
* AI Summary  
* Activity

Revenue Dashboard

Tabs

* Monthly  
* Yearly  
* Customer Analysis

Settings

Tabs

* Profile  
* Security  
* Preferences

---

# **4\. Entry Points**

Unauthenticated Users

Landing

↓

Login

↓

Dashboard

Authenticated Users

Dashboard

Direct navigation via Sidebar

Shared Document Links (future)

Login

↓

Requested Document

---

# **5\. Authentication Flow**

Development

Landing

↓

Login

↓

Dashboard

OR

Landing

↓

Register

↓

Email Verification through 2FA with verification code

↓

Login

↓

Dashboard

Forgot Password

Login

↓

Forgot Password

↓

Email which needs to be valid

↓

Reset Password

↓

Login

---

# **6\. Key User Journeys**

## **Journey 1 – Upload and Process a Document**

Dashboard

↓

Upload Document

↓

OCR Processing

↓

Metadata Extraction

↓

AI Categorization

↓

Embedding

↓

Document Stored

↓

Document Details

---

## **Journey 2 – Create an Invoice**

Dashboard

↓

Invoice Generator

↓

Fill Details

↓

Calculate Totals

↓

Preview and be able to edit and make changes

↓

Generate PDF

↓

Save Invoice

↓

Invoice Register

---

## **Journey 3 – Ask the AI Assistant**

Dashboard

↓

AI Assistant

↓

User Query

↓

Semantic Search

↓

Retrieve Documents

↓

Generate AI Response

↓

Open Related Document

---

# **7\. Edge Cases**

## **Empty States**

Dashboard

* No revenue available  
* No invoices yet

Documents

* No uploaded files

Invoice Register

* No invoices found

AI Assistant

* No matching documents

Activity Logs

* No recorded activity

Each page provides a clear call-to-action where appropriate.

---

## **Loading States**

* Dashboard skeleton cards  
* Table skeleton rows  
* Chart placeholders  
* AI typing indicator  
* Upload progress bar  
* OCR processing indicator

---

## **Error States**

Authentication

* Invalid credentials  
* Invalid email after wrong 2FA  
* Session expired

Uploads

* Unsupported file type  
* File too large  
* Upload failed

Invoices

* Required fields missing  
* Duplicate invoice number

AI

* Model unavailable  
* No response generated  
* No relevant documents found

Database

* Connection failure  
* Timeout

---

# **8\. Modal, Drawer, and Overlay Interactions**

## **Confirmation Modals**

* Delete Document  
* Permanently Delete  
* Restore File  
* Logout  
* Remove User

---

## **Upload Drawer**

Allows drag-and-drop uploads without leaving the current page.

---

## **AI Chat Drawer**

Accessible from any page.

Supports asking contextual questions while continuing current work.

---

## **Document Preview Overlay**

Displays PDF or image preview without navigating away from the document list.

---

## **Invoice Preview Modal**

Preview generated invoice before saving or exporting.

---

# **9\. Redirect Logic**

| User Action | Redirect |
| ----- | ----- |
| Successful Login | Dashboard |
| Successful Registration | Login |
| Password Reset | Login |
| Upload Complete | Document Details |
| Delete Document | Documents List |
| Restore Document | Trash |
| Permanent Delete | Trash |
| Save Invoice | Invoice Register |
| Open Invoice | Invoice Details |
| AI Result Document Click | Document Details |
| Session Expired | Login |
| Unauthorized Page | Access Denied |
| Logout | Login |

---

# **10\. Role-Based Navigation**

## **Admin**

Full system access

* Dashboard  
* Documents  
* Invoice Generator  
* Invoice Register  
* Revenue Dashboard  
* Monthly Calculator  
* AI Assistant  
* Activity Logs  
* User Management  
* Settings

---

## **Accountant**

Access

* Dashboard  
* Documents  
* Invoice Generator  
* Invoice Register  
* Revenue Dashboard  
* Monthly Calculator  
* AI Assistant  
* Settings

No User Management.

---

## **Employee**

Access

* Dashboard  
* Documents  
* AI Assistant  
* Activity Logs (Own Activity)  
* Settings

No financial administration.

---

## **Viewer**

Read-only access

* Dashboard  
* Documents  
* Revenue Dashboard (Read Only)  
* AI Assistant  
* Settings

Cannot upload, edit, or delete content.

---

# **11\. Global UX Principles**

* Hide and show sidebar navigation across authenticated pages.  
* Breadcrumbs on nested pages for easy orientation.  
* All destructive actions require confirmation.  
* AI features provide citations to source documents.  
* Long-running operations display progress indicators.  
* Forms support autosave where appropriate.  
* Role-based permissions dynamically control visible navigation and available actions.  
* Responsive layout optimized for desktop, with graceful support for tablets and mobile phones.

