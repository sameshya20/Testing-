# Enterprise Test Case Generator - Technology Stack & System Workflow

This document provides a comprehensive overview of the architecture, technology stack, backend services, frontend components, data flow, and operational workflows of the **Enterprise Test Case Generator** application.

---

## 1. Technology Stack Overview

### **Backend Architecture**
* **Language & Runtime**: Python 3.11+
* **Web Framework**: **FastAPI** — High-performance, asynchronous RESTful API framework with automatic OpenAPI documentation.
* **ASGI Web Server**: **Uvicorn** — Lightning-fast ASGI server implementation for handling asynchronous HTTP requests.
* **Database & ORM**:
  * **SQLite** (`test_generator.db`) — Lightweight file-based relational database.
  * **SQLAlchemy** — Object-Relational Mapping (ORM) framework for domain model management and database queries.
* **Authentication & Security**:
  * **Bearer Token Session Store** — Custom in-memory session token store with timestamp-based expiration.
  * **SHA-256 HMAC Password Hashing** — Secure cryptographic hash algorithm for user passwords.
* **Data Processing & File Generation**:
  * **openpyxl** — Excel workbook generation library creating styled, multi-sheet `.xlsx` workbooks with custom fills, auto-filters, borders, and typography.
  * **Pydantic (v2)** — Strict data validation and schema definitions for request payload parsing and response serialization.
  * **HTTPX & BeautifulSoup4** — Asynchronous web context scraping and HTML metadata extraction engine.
* **Automated Testing**: **pytest** & **FastAPI TestClient** — Unit and integration test suite covering applications, authentication, generation, and excel exports.

---

### **Frontend Architecture**
* **Framework & Language**: **React 18** + **TypeScript** (Strict mode) — Component-based architecture with type-safe interfaces.
* **Build Tool & Bundler**: **Vite** — Next-generation fast frontend tooling and dev server.
* **Styling & Aesthetics**:
  * **Tailwind CSS** — Utility-first CSS framework with a dark enterprise slate theme (`slate-950`, `slate-900`, `blue-600`, `emerald-500`).
  * **Lucide React** — Icon library providing clean visual indicators for navigation, priorities, test categories, and actions.
* **API & Network Client**:
  * Native asynchronous `fetch` client layer (`services/api.ts`) with automatic Bearer token injection and global 401 session expiration interceptor.

---

## 2. Directory & Component Architecture

```
3rd uc/
├── TECH_STACK_AND_WORKFLOW.md
├── backend/
│   ├── run.py                          # Server launcher (Uvicorn host: 127.0.0.1, port: 8000)
│   ├── requirements.txt                # Python package dependencies
│   ├── test_generator.db               # SQLite database file
│   ├── app/
│   │   ├── main.py                     # FastAPI application entrypoint & CORS middleware
│   │   ├── core/
│   │   │   └── security.py             # Password hashing, token generation & verification
│   │   ├── db/
│   │   │   ├── session.py              # SQLAlchemy DB engine & SessionLocal
│   │   │   └── init_db.py              # Seed data initializer (User accounts & Applications)
│   │   ├── models/                     # SQLAlchemy Database Models
│   │   │   ├── user.py                 # User model (id, email, hashed_password, full_name)
│   │   │   └── application.py          # Application model (id, name, code, domain, rules)
│   │   ├── schemas/                    # Pydantic Schemas
│   │   │   ├── user.py                 # Login payload & UserRead schemas
│   │   │   ├── application.py          # Application schema
│   │   │   ├── devops.py               # DevOps work items & criteria schemas
│   │   │   └── test_case.py            # TestCase, Request, and CoverageSummary schemas
│   │   ├── api/
│   │   │   ├── deps.py                 # Dependency injector (get_current_user HTTPBearer)
│   │   │   └── v1/
│   │   │       ├── api.py              # API v1 Router aggregator
│   │   │       └── endpoints/
│   │   │           ├── auth.py         # Login, Me, Logout endpoints
│   │   │           ├── applications.py # Application catalog endpoints
│   │   │           ├── devops.py       # Azure DevOps work items & criteria search endpoints
│   │   │           ├── generation.py   # Multi-requirement test case creation endpoint
│   │   │           └── export.py       # Multi-sheet Excel workbook export endpoint
│   │   └── services/
│   │       ├── devops_service.py       # Azure DevOps integration service
│   │       ├── web_extractor.py        # Web scraping & context analyzer
│   │       ├── test_generator.py       # Core test case synthesis engine
│   │       └── excel_exporter.py       # Styled openpyxl workbook generator
│   └── tests/                          # Automated pytest suite
│       ├── test_auth.py
│       ├── test_applications.py
│       ├── test_generator.py
│       └── test_export.py
└── frontend/
    ├── package.json                    # Dependencies & build scripts
    ├── vite.config.ts                  # Vite configuration & proxy settings
    ├── index.html                      # HTML root template
    └── src/
        ├── main.tsx                    # React application entrypoint
        ├── App.tsx                     # Main application orchestrator & session state
        ├── types/                      # TypeScript interface declarations
        ├── services/
        │   └── api.ts                  # REST API communication client
        └── components/
            ├── LoginPage.tsx           # Enterprise login interface
            ├── Header.tsx              # Navigation header with user profile dropdown
            ├── ApplicationForm.tsx     # Application & multi-requirement selection form
            ├── MetricCards.tsx         # Dashboard coverage summary & metric cards
            ├── TestCaseTable.tsx       # Tabbed test case table, filter, & export toolbar
            └── EditTestCaseModal.tsx   # Scenario step & outcome editor modal
```

---

## 3. End-to-End Operational Workflow

The following flowchart and step-by-step description detail the execution flow from user sign-in to test case creation and Excel download.

### **Workflow Diagram**

```
 ┌────────────────┐        ┌──────────────────┐        ┌───────────────────────┐
 │  User Sign-In  │ ─────> │ Application &    │ ─────> │ Azure DevOps /        │
 │  (LoginPage)   │        │ Requirement Form │        │ Application Link Spec │
 └────────────────┘        └──────────────────┘        └───────────────────────┘
         │                          │                              │
         v                          v                              v
 ┌────────────────┐        ┌──────────────────┐        ┌───────────────────────┐
 │ /api/v1/auth/  │        │ DB Rules &       │        │ Web Context Extractor │
 │ login (Bearer) │        │ Business Logic   │        │ (web_extractor.py)    │
 └────────────────┘        └──────────────────┘        └───────────────────────┘
                                    │                              │
                                    └──────────────┬───────────────┘
                                                   v
                                       ┌───────────────────────┐
                                       │ Core Test Generator   │
                                       │ Synthesis Engine      │
                                       │ (test_generator.py)   │
                                       └───────────────────────┘
                                                   │
                                                   v
                                       ┌───────────────────────┐
                                       │ Positive, Negative,   │
                                       │ & Edge Test Suites    │
                                       └───────────────────────┘
                                        /                     \
                                       v                       v
                           ┌───────────────────────┐   ┌───────────────────────┐
                           │ Dashboard Display     │   │ Multi-Sheet Excel     │
                           │ & In-Memory Editing   │   │ Export (.xlsx)        │
                           └───────────────────────┘   └───────────────────────┘
```

---

### **Detailed Step-by-Step Execution Flow**

#### **Step 1: Enterprise Authentication & Session Protection**
1. The user visits the web application (`http://localhost:5173/`).
2. If no active session token exists in `localStorage`, [LoginPage.tsx](file:///d:/3rd%20uc/frontend/src/components/LoginPage.tsx) renders.
3. User enters credentials (e.g., `admin@enterprise.com` / `password123`).
4. The frontend calls `POST /api/v1/auth/login`.
5. Backend [auth.py](file:///d:/3rd%20uc/backend/app/api/v1/endpoints/auth.py) verifies the email and password against `User` table records using SHA-256 HMAC comparison.
6. Upon success, a 64-character bearer token is issued and returned.
7. Subsequent requests automatically pass the `Authorization: Bearer <token>` header, enforced by [deps.py](file:///d:/3rd%20uc/backend/app/api/deps.py).

#### **Step 2: Enterprise Application & Multi-Requirement Selection**
1. [ApplicationForm.tsx](file:///d:/3rd%20uc/frontend/src/components/ApplicationForm.tsx) fetches the registered application list from `GET /api/v1/applications`.
2. The user selects a target enterprise application (e.g., *Enterprise Banking Portal*, *Healthcare Claims Management*, *E-Commerce Checkout*).
3. The user chooses the requirement input method:
   * **User Story Mode**: Search and select multiple User Stories (e.g., `US-101`, `US-102`) rendered as interactive chip elements.
   * **Acceptance Criteria Mode**: Search and select specific Acceptance Criteria items (e.g., `US-101 AC-1`).
4. (Optional) User enters an Application URL for live web structure context extraction.

#### **Step 3: Multi-Requirement Test Suite Synthesis**
1. User clicks **Create Test Cases**, triggering `POST /api/v1/generation/create`.
2. Backend [generation.py](file:///d:/3rd%20uc/backend/app/api/v1/endpoints/generation.py):
   - Fetches business rules, user roles, and key modules for the selected Application from the SQLite database.
   - Communicates with [devops_service.py](file:///d:/3rd%20uc/backend/app/services/devops_service.py) to resolve selected User Stories and Acceptance Criteria.
   - If an Application Link is supplied, [web_extractor.py](file:///d:/3rd%20uc/backend/app/services/web_extractor.py) asynchronously inspects page title, headers, form fields, and buttons.
3. The core engine [test_generator.py](file:///d:/3rd%20uc/backend/app/services/test_generator.py) synthesizes:
   - **Positive Scenarios**: Standard happy path flows validating expected functionality.
   - **Negative Scenarios**: Input boundary violations, invalid role permissions, expired sessions, and error handling.
   - **Edge Scenarios**: Boundary values, concurrent access, empty data payloads, and network timeout conditions.
4. Each test case maintains strict **requirement traceability** (`US-101 AC-1`), priority tags, preconditions, step-by-step execution instructions, and expected outcomes.

#### **Step 4: Interactive Quality Dashboard**
1. Test suite results populate state in [App.tsx](file:///d:/3rd%20uc/frontend/src/App.tsx).
2. [MetricCards.tsx](file:///d:/3rd%20uc/frontend/src/components/MetricCards.tsx) calculates coverage summaries: total test count, breakdown by type (Positive, Negative, Edge), high-priority test percentage, and estimated total execution time.
3. [TestCaseTable.tsx](file:///d:/3rd%20uc/frontend/src/components/TestCaseTable.tsx) provides:
   - Category tab switching (Positive / Negative / Edge).
   - Instant scenario search and priority filter dropdowns.
   - Expandable rows for viewing step-by-step execution details.
   - Inline test case editing modal ([EditTestCaseModal.tsx](file:///d:/3rd%20uc/frontend/src/components/EditTestCaseModal.tsx)) and scenario deletion.

#### **Step 5: Multi-Sheet Excel Workbook Export**
1. User clicks **Download Excel**.
2. Frontend sends current test suite state to `POST /api/v1/export/excel`.
3. Backend [excel_exporter.py](file:///d:/3rd%20uc/backend/app/services/excel_exporter.py) generates an `openpyxl` workbook containing:
   - Three separate formatted sheets: **Positive**, **Negative**, and **Edge**.
   - Dark slate headers, bold text styling, and auto-adjusted column widths.
   - Priority color fills (High = Soft Red, Medium = Soft Amber, Low = Soft Blue).
   - Dedicated **User Story** and **Acceptance Criteria** columns for requirement traceability.
   - Auto-filters on row headers and frozen top header pane.
4. Binary `.xlsx` file stream is transmitted back to the browser for direct user download.

---

## 4. Key Summary Points

| Feature / Aspect | Implementation Details |
| :--- | :--- |
| **API Protocol** | Asynchronous RESTful JSON API using FastAPI & Pydantic schemas |
| **Security Layer** | Bearer Token Session Store with SHA-256 HMAC password verification |
| **Database** | SQLite + SQLAlchemy ORM with pre-seeded enterprise domain rules & accounts |
| **Frontend UI** | React 18 + TypeScript + Tailwind CSS with dark slate theme |
| **Traceability** | Requirement tags mapped across User Stories & AC items in UI & Excel |
| **Excel Exporter** | Multi-sheet `.xlsx` workbook builder with priority highlights & auto-filters |
| **Automated Testing** | Full coverage unit test suite with `pytest` & `tsc` type checking |
