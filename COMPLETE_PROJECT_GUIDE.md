# Complete Technical & Architectural Guide: Enterprise QA Application-Link-Aware Test Case Generation System

---

## 1. PROJECT OVERVIEW

### What is this project?
The **Enterprise QA Application-Link-Aware Test Case Generation System** is an enterprise-grade automated Quality Assurance platform. It bridges the gap between software requirements (Azure DevOps User Stories & Acceptance Criteria), enterprise business rules, and real live web application user interfaces (Application Links).

### What real-world problem does it solve?
1. **Abstract & Generic Test Cases**: Manual test cases often specify generic steps like *"Verify page works"*, lacking actual field names, placeholders, or button labels.
2. **Disconnect between Requirements and Live UI**: User Stories in ALM systems (e.g., Azure DevOps) state *what* to build, but do not contain actual DOM selectors (`id`, `name`, `data-testid`, button titles) present on the live site.
3. **Incomplete Edge & Negative Coverage**: QA teams under tight deadlines focus primarily on happy-path scenarios, skipping boundary values, security role restrictions, omitted mandatory fields, and rapid submit attempts.
4. **Time-Consuming Manual Writing**: Writing 50+ detailed, step-by-step test cases for every sprint item takes days of manual QA effort.

### Why was this project developed?
To automate test suite generation by scraping live web pages (HTML DOM or SPA JavaScript bundles) and synthesizing traceable **Positive**, **Negative**, and **Edge** test cases mapped directly to Azure DevOps User Stories, exportable as formatted Excel workbooks (`.xlsx`).

### Who are the users?
* **QA Leads & Engineers**: Generate comprehensive test suites in seconds.
* **Software Developers**: Preview positive, negative, and edge criteria for Test-Driven Development (TDD/BDD).
* **Product Owners & Business Analysts**: Verify acceptance criteria coverage against live pages.
* **Agile Teams**: Attach standardized Excel test suites directly to sprint work items.

### What are the main objectives?
* Extract live UI context (input controls, buttons, placeholders, SPA JS bundles) dynamically via URL.
* Combine live UI context with Azure DevOps User Stories and business rules.
* Synthesize multi-categorized test cases with step-by-step instructions, precondition parameters, test data, and expected outcomes.
* Format and export multi-sheet, color-coded Excel workbooks using `openpyxl`.

### What are the major features?
1. **JWT Bearer Session Authentication**: Secure login/logout with in-memory session token store.
2. **Azure DevOps REST Integration + Offline Fallback**: Live REST search of DevOps work items and acceptance criteria, with a rich fallback database.
3. **Database-Driven Application Rules**: Pre-configured app domain specifications, user roles, key modules, and business constraints.
4. **Live DOM & SPA Bundle Extractor**: Inspects live HTML DOM (`httpx` + `BeautifulSoup4`) and single-page application JavaScript bundles (React/Vite JSX properties).
5. **Multi-Link E2E Workflow Analysis**: Analyzes sequential URLs (e.g. *Product Page → Cart → Checkout*) for end-to-end user journey test cases.
6. **Rule Engine & Deduplication**: Combines combinatorial engines with quality validation and deduplication.
7. **Interactive Dashboard**: Tabbed interface with coverage metrics, real-time filtering, search, and modal test case editor.
8. **Styled Excel Exporter**: Multi-sheet export (`Positive`, `Negative`, `Edge`) with custom column widths, auto-filters, and priority fills.

### Complete End-to-End Purpose
To allow a QA engineer to select an application, pull or search user stories, supply live application web links, instantly generate exhaustive test suites grounded in live UI elements, review/edit the cases on an interactive dashboard, and export a ready-to-execute Excel workbook.

---

## 2. REAL-WORLD USE CASE

### Real-World Scenario
Imagine a QA Engineer working on an e-commerce platform (*"SauceDemo Swag Store"*). The sprint includes **User Story US-101**: *"Login Authentication"* with Acceptance Criteria **AC-101.1**: *"User enters username and password to log in"*.

### Flow: User → Input → Processing → System → Output

```
┌──────────────┐     ┌─────────────────────────────────────────┐     ┌─────────────────────────────┐
│  QA Engineer │ ──> │ Inputs: App = "SauceDemo Swag Store",   │ ──> │ System analyzes requirements│
│  (User)      │     │ Story = "US-101", URL = "saucedemo.com" │     │ and extracts live DOM       │
└──────────────┘     └─────────────────────────────────────────┘     └─────────────────────────────┘
                                                                                    │
                                                                                    ▼
┌──────────────────────────────────────────────┐     ┌─────────────────────────────────────────────┐
│ Output: Interactive Dashboard + Downloadable │ <── │ Generates Positive, Negative, & Edge        │
│ openpyxl Excel Workbook (.xlsx)              │     │ test cases with real field selectors        │
└──────────────────────────────────────────────┘     └─────────────────────────────────────────────┘
```

#### Step-by-Step What Happens:
1. **Login**: User logs in with `admin@qa.com` / `admin123`.
2. **Requirement Selection**: User selects application *"SauceDemo Swag Store"* and picks *"US-101 Login Authentication"*.
3. **Application Link Input**: User provides `https://www.saucedemo.com`.
4. **Processing**:
   - Backend fetches requirement criteria (`AC-101.1`, `AC-101.2`).
   - `web_extractor.py` visits `https://www.saucedemo.com`, discovering inputs (`user-name`, `password`) and button (`login-button`).
   - `test_generator.py` combines acceptance criteria + business rules + live UI elements.
   - Synthesizes positive cases (valid login), negative cases (missing password, invalid credentials), and edge cases (rapid double-click, max length inputs).
5. **Output**: Dashboard displays 12 generated test cases with metric cards. The user clicks **Export to Excel** to download `SauceDemo_Swag_Store_TestCases.xlsx`.

---

## 3. COMPLETE WORKFLOW

### End-to-End Execution Sequence

```
User Action
  ↓
Frontend (React + Vite)
  ↓
API Request (Axios / Fetch with JWT Bearer Token)
  ↓
FastAPI Router (app/api/v1/endpoints/*.py)
  ↓
Dependencies & Auth Injector (app/api/deps.py)
  ↓
Business Logic Services (app/services/*.py)
  ↓
Database (SQLite / SQLAlchemy) & External Scraper / DevOps API
  ↓
Combinatorial Synthesis, Quality Validation & Deduplication
  ↓
JSON / Excel Stream Response
  ↓
Frontend State Update / Browser Download
  ↓
User Interface Update
```

### Detailed Step Breakdown

| Step | Action / Process | Responsible File | Responsible Class / Function | Data Passed | Data Returned |
|---|---|---|---|---|---|
| 1 | Submits Login Credentials | [`LoginPage.tsx`](file:///d:/3rd%20uc/frontend/src/components/LoginPage.tsx) | `handleSubmit()` | `{ username, password }` | Stores JWT token in `localStorage` |
| 2 | Authenticates Request | [`auth.py`](file:///d:/3rd%20uc/backend/app/api/v1/endpoints/auth.py) | `login_for_access_token()` | `OAuth2PasswordRequestForm` | `{ access_token, token_type: "bearer" }` |
| 3 | Loads Applications List | [`ApplicationForm.tsx`](file:///d:/3rd%20uc/frontend/src/components/ApplicationForm.tsx) | `useEffect()` → `api.getApplications()` | Headers: `Authorization: Bearer <token>` | List of `ApplicationRead` objects |
| 4 | Queries DevOps Work Items | [`devops.py`](file:///d:/3rd%20uc/backend/app/api/v1/endpoints/devops.py) | `search_devops_work_items()` | `query_str`, `app_id` | Array of `DevOpsWorkItem` items |
| 5 | Triggers Test Generation | [`ApplicationForm.tsx`](file:///d:/3rd%20uc/frontend/src/components/ApplicationForm.tsx) | `handleSubmit()` → `api.generateTestCases()` | `GenerateTestCasesRequest` | `GenerateTestCasesResponse` |
| 6 | Extracts Web Page UI Context | [`web_extractor.py`](file:///d:/3rd%20uc/backend/app/services/web_extractor.py) | `WebExtractorService.extract_context()` | `urls: List[str]` | `WebContext` (fields, buttons, forms) |
| 7 | Synthesizes Test Cases | [`test_generator.py`](file:///d:/3rd%20uc/backend/app/services/test_generator.py) | `TestCaseGeneratorEngine.generate()` | Requirements + App Rules + Web Context | `List[TestCase]` |
| 8 | Deduplicates Test Cases | [`deduplication_service.py`](file:///d:/3rd%20uc/backend/app/services/deduplication_service.py) | `DeduplicationService.deduplicate()` | `List[TestCase]` | `List[TestCase]` (cleaned, sequential IDs) |
| 9 | Renders Dashboard Metrics | [`App.tsx`](file:///d:/3rd%20uc/frontend/src/App.tsx) | `App` state update | Response payload | Renders `MetricCards` and `TestCaseTable` |
| 10 | Exports Excel File | [`export.py`](file:///d:/3rd%20uc/backend/app/api/v1/endpoints/export.py) | `export_test_cases_to_excel()` | `ExportExcelRequest` | `StreamingResponse` (`.xlsx` binary) |

---

## 4. PROJECT ARCHITECTURE

### Architectural Diagram

```
+-----------------------------------------------------------------------------------+
|                                 FRONTEND LAYER                                    |
|  React 18 + TypeScript + Vite + Tailwind CSS + Lucide Icons                       |
|  [LoginPage] -> [ApplicationForm] -> [MetricCards] -> [TestCaseTable]             |
+-----------------------------------------------------------------------------------+
                                        |  HTTP REST (JSON / Bearer Token)
                                        v
+-----------------------------------------------------------------------------------+
|                                 BACKEND LAYER                                     |
|  FastAPI + Uvicorn + Pydantic v2                                                  |
|                                                                                   |
|  [API Routers: auth.py | applications.py | devops.py | generation.py | export.py] |
|                                       |                                           |
|  [Security / Session Store: security.py | deps.py]                                |
|                                       |                                           |
|  [Services Engine]                                                                |
|    ├── WebExtractorService (httpx + BeautifulSoup4 + SPA JS Bundle Analyzer)      |
|    ├── AzureDevOpsService (REST API Integration + Local Mock Registry)            |
|    ├── TestCaseGeneratorEngine (Rule Matrix + Combinatorial Engine)               |
|    ├── QualityValidator & DeduplicationService                                    |
|    └── ExcelExporterService (openpyxl Multi-Sheet Exporter)                       |
+-----------------------------------------------------------------------------------+
                      |                                       |
                      v                                       v
+----------------------------------+       +----------------------------------------+
|          DATABASE LAYER          |       |           EXTERNAL SERVICES            |
|  SQLite (test_generator.db)      |       |  Azure DevOps REST API                 |
|  SQLAlchemy ORM Models:          |       |  Live Web Applications (Scraped URLs)  |
|   - User                         |       +----------------------------------------+
|   - Application                  |
|   - DevOpsWorkItem               |
+----------------------------------+
```

### Components Summary
* **Frontend**: React 18 SPA built with TypeScript & Vite, styled with Tailwind CSS.
* **Backend**: Asynchronous Python FastAPI web server with Uvicorn ASGI runner.
* **Database**: SQLite database file ([`test_generator.db`](file:///d:/3rd%20uc/test_generator.db)) managed via SQLAlchemy ORM.
* **External Scraper Engine**: `httpx` async HTTP client + `BeautifulSoup4` DOM parser + Regex JS bundle parser.
* **Export Subsystem**: `openpyxl` engine converting test case schemas into formatted binary Excel streams.

---

## 5. TECH STACK

| Technology | Category | Purpose | Where Used | Why Used | Key Files |
|---|---|---|---|---|---|
| **Python 3.11** | Programming Language | Core backend execution | Backend server | High performance, rich ecosystem for web scraping and data processing | `backend/**/*.py` |
| **FastAPI** | Web Framework | REST API framework | Backend API routing | Automatic OpenAPI docs, high speed, async support | [`backend/app/main.py`](file:///d:/3rd%20uc/backend/app/main.py) |
| **Uvicorn** | ASGI Server | Web server runner | Backend server launcher | Production-ready asynchronous ASGI server for FastAPI | [`backend/run.py`](file:///d:/3rd%20uc/backend/run.py) |
| **SQLAlchemy** | Database ORM | Database mapping | Backend DB layer | Object-Relational Mapping for SQLite models | [`session.py`](file:///d:/3rd%20uc/backend/app/db/session.py) |
| **SQLite** | Relational Database | Data persistence | Backend storage | Zero-configuration file-based relational database | [`test_generator.db`](file:///d:/3rd%20uc/test_generator.db) |
| **Pydantic v2** | Data Validation | Request/Response schemas | Backend API layer | Type validation and JSON serialization | `backend/app/schemas/*.py` |
| **httpx** | HTTP Client | Asynchronous scraping | Web extractor service | Non-blocking async HTTP client with custom headers | [`web_extractor.py`](file:///d:/3rd%20uc/backend/app/services/web_extractor.py) |
| **BeautifulSoup4** | HTML Parser | DOM extraction | Web extractor service | Flexible HTML DOM parsing for form inputs and buttons | [`web_extractor.py`](file:///d:/3rd%20uc/backend/app/services/web_extractor.py) |
| **openpyxl** | Spreadsheet Library | Excel file generation | Excel exporter service | Programmatic creation of styled, multi-sheet `.xlsx` workbooks | [`excel_exporter.py`](file:///d:/3rd%20uc/backend/app/services/excel_exporter.py) |
| **pytest** | Testing Framework | Backend unit testing | Test suite | Automated testing for FastAPI endpoints and services | `backend/tests/*.py` |
| **React 18** | Frontend Library | User interface | Frontend SPA | Component-driven declarative UI rendering | `frontend/src/**/*.tsx` |
| **TypeScript** | Programming Language | Frontend type safety | Entire frontend | Static typing preventing runtime type errors | `frontend/src/**/*.ts(x)` |
| **Vite** | Build Tool / Dev Server | Frontend bundler | Frontend build | Lightning-fast HMR and bundle compilation | [`vite.config.ts`](file:///d:/3rd%20uc/frontend/vite.config.ts) |
| **Tailwind CSS** | Styling Framework | UI styling | Frontend styling | Utility-first responsive dark theme design | [`index.css`](file:///d:/3rd%20uc/frontend/src/index.css) |
| **Lucide React** | Icon Library | UI iconography | Frontend components | Modern, lightweight icons for actions and status indicators | `frontend/src/components/*.tsx` |

---

## 6. TOOLS USED

* **FastAPI / Uvicorn**: Runs the API application server locally on port 8000.
* **Vite**: Provides dev server with Hot Module Replacement (HMR) on port 5173.
* **SQLite / SQLAlchemy**: Database storage and migration engine for local persistence.
* **pytest**: Runs unit and integration test assertions across backend services.
* **npm**: Node package manager handling frontend dependencies and build scripts.
* **Git**: Version control repository tracking source changes.

---

## 7. FOLDER STRUCTURE

```
d:\3rd uc\
├── COMPLETE_PROJECT_GUIDE.md    → Complete Technical & Architectural Guide
├── PROJECT_DOCUMENTATION.md      → Project documentation & workflow reference
├── TECH_STACK_AND_WORKFLOW.md   → System architecture reference
├── backend/                     → Python FastAPI Backend
│   ├── run.py                   → Server launcher script (port 8000)
│   ├── requirements.txt         → Python package dependencies
│   ├── test_generator.db        → SQLite database file
│   ├── app/
│   │   ├── main.py              → FastAPI app initialization & CORS middleware
│   │   ├── api/                 → API Routers and Dependencies
│   │   │   ├── deps.py          → Auth dependency injection
│   │   │   └── v1/
│   │   │       ├── api.py       → API v1 router aggregator
│   │   │       └── endpoints/   → Auth, Apps, DevOps, Generation, Export endpoints
│   │   ├── core/
│   │   │   └── security.py      → Security hashing & token management
│   │   ├── db/                  → DB engine session & data initializer
│   │   ├── models/              → SQLAlchemy ORM models (User, Application, DevOps)
│   │   ├── schemas/             → Pydantic validation schemas
│   │   └── services/            → Web Extractor, Test Generator, Excel Exporter
│   └── tests/                   → Pytest automated test suite
└── frontend/                    → React + TypeScript + Vite Frontend
    ├── package.json             → Node dependencies and build scripts
    ├── vite.config.ts           → Vite configuration & backend proxy
    ├── index.html               → HTML root template
    └── src/
        ├── main.tsx             → React application root entrypoint
        ├── App.tsx              → Main app state & tab manager
        ├── components/          → UI components (Login, Header, Form, Table, Modal)
        ├── services/            → Axios/Fetch REST API client layer (`api.ts`)
        └── types/               → TypeScript interface declarations
```

---

## 8. FRONTEND

### Page & Component Breakdown

```
[App.tsx] (Main Container & Session Manager)
 ├── User NOT Authenticated: [LoginPage.tsx]
 └── User Authenticated:
      ├── [Header.tsx] (Navigation & User Profile)
      ├── [ApplicationForm.tsx] (Select App, Story, Link & Generate)
      ├── [MetricCards.tsx] (Summary Stats Cards)
      ├── [TestCaseTable.tsx] (Tabbed Cases List, Search & Filter)
      └── [EditTestCaseModal.tsx] (Popup Scenario Step Editor)
```

#### Detailed Components:
1. [`LoginPage.tsx`](file:///d:/3rd%20uc/frontend/src/components/LoginPage.tsx):
   * Renders email & password form. Calls `api.login()`. On success, saves bearer token and updates user state.
2. [`Header.tsx`](file:///d:/3rd%20uc/frontend/src/components/Header.tsx):
   * Displays application title, user avatar/name, system status, and **Logout** button.
3. [`ApplicationForm.tsx`](file:///d:/3rd%20uc/frontend/src/components/ApplicationForm.tsx):
   * Dropdown to select application.
   * Search input for Azure DevOps work items.
   * Checkbox list for User Stories / Acceptance Criteria selection.
   * Multi-URL input fields for live page link scraping.
   * **Generate Test Cases** button triggering backend processing.
4. [`MetricCards.tsx`](file:///d:/3rd%20uc/frontend/src/components/MetricCards.tsx):
   * Displays statistics: Total Cases, Positive, Negative, Edge, Stories Covered, ACs Evaluated, Pages Scraped.
5. [`TestCaseTable.tsx`](file:///d:/3rd%20uc/frontend/src/components/TestCaseTable.tsx):
   * Filter tabs (`All`, `Positive`, `Negative`, `Edge`).
   * Search input filtering title/steps/ID.
   * Action buttons: Edit row modal launcher and **Export to Excel** downloader.
6. [`EditTestCaseModal.tsx`](file:///d:/3rd%20uc/frontend/src/components/EditTestCaseModal.tsx):
   * Inline editor modal allowing QA leads to edit title, scenario, priority, steps, and expected result before exporting.

---

## 9. BACKEND

### Application Entry Point & Endpoints

**Main Entrypoint**: [`backend/app/main.py`](file:///d:/3rd%20uc/backend/app/main.py) initializes FastAPI with CORS settings permitting origins like `http://localhost:5173`.

#### REST API Endpoints Overview

| Method | Endpoint | Purpose | Handler Function | Request Payload | Response Payload |
|---|---|---|---|---|---|
| `POST` | `/api/v1/auth/login` | Session login | `login_for_access_token` | `OAuth2PasswordRequestForm` | `{ access_token, token_type }` |
| `GET` | `/api/v1/auth/me` | Current user info | `read_users_me` | Bearer Token | `UserRead` |
| `POST` | `/api/v1/auth/logout` | Revoke session | `logout` | Bearer Token | `{ message: "Logout successful" }` |
| `GET` | `/api/v1/applications` | List registered apps | `read_applications` | Bearer Token | `List[ApplicationRead]` |
| `GET` | `/api/v1/applications/{id}` | Get application by ID | `read_application` | Bearer Token | `ApplicationRead` |
| `GET` | `/api/v1/devops/search` | Search Azure DevOps | `search_devops_work_items` | `query`, `app_id` | `List[DevOpsWorkItem]` |
| `GET` | `/api/v1/devops/acceptance-criteria` | Fetch story ACs | `get_acceptance_criteria` | `work_item_ids` | `List[AcceptanceCriteria]` |
| `POST` | `/api/v1/generation/create` | Generate test cases | `create_test_cases` | `GenerateTestCasesRequest` | `GenerateTestCasesResponse` |
| `POST` | `/api/v1/export/excel` | Export Excel workbook | `export_excel` | `ExportExcelRequest` | `StreamingResponse` (`.xlsx`) |

---

## 10. DATABASE

### Database Architecture & Entity-Relationship Model

**Database Type**: SQLite ([`test_generator.db`](file:///d:/3rd%20uc/backend/test_generator.db)) using SQLAlchemy ORM.

```
+----------------------------------+       +----------------------------------+
|              users               |       |           applications           |
+----------------------------------+       +----------------------------------+
| PK  id             INTEGER       |       | PK  id             INTEGER       |
|     email          VARCHAR(255)  |       |     name           VARCHAR(255)  |
|     hashed_password VARCHAR(255)  |       |     code           VARCHAR(100)  |
|     full_name      VARCHAR(255)  |       |     domain         VARCHAR(255)  |
|     is_active      BOOLEAN       |       |     description    TEXT          |
+----------------------------------+       |     business_rules JSON / TEXT   |
                                           |     user_roles     JSON / TEXT   |
                                           +----------------------------------+
                                                            | 1
                                                            |
                                                            | N
                                           +----------------------------------+
                                           |        devops_work_items         |
                                           +----------------------------------+
                                           | PK  id             INTEGER       |
                                           | FK  application_id INTEGER       |
                                           |     external_id    VARCHAR(100)  |
                                           |     title          VARCHAR(500)  |
                                           |     description    TEXT          |
                                           |     work_item_type VARCHAR(50)   |
                                           |     acceptance_criteria JSON/TEXT|
                                           +----------------------------------+
```

1. **`users`**: Stores user authentication credentials and account metadata.
2. **`applications`**: Stores enterprise software application definitions, business rules, and user roles.
3. **`devops_work_items`**: Local database registry of Azure DevOps user stories and acceptance criteria.

---

## 11. AUTHENTICATION & AUTHORIZATION

### Session Authentication Architecture

```
User enters credentials on LoginPage
  ↓
POST /api/v1/auth/login
  ↓
security.py verifies HMAC-SHA256 password hash
  ↓
Generates UUID Session Bearer Token (token stored in security.py memory store)
  ↓
Returns Token to Frontend -> Saved in localStorage
  ↓
Subsequent API Requests include Header: `Authorization: Bearer <token>`
  ↓
deps.py intercepts token -> Verifies session -> Injects current_user context
```

* **Password Hashing**: Uses SHA-256 HMAC cryptographic hashing with custom application salt ([`security.py`](file:///d:/3rd%20uc/backend/app/core/security.py)).
* **Session Management**: Tokens map to user IDs in `_SESSION_STORE` with configurable expiration timestamps.

---

## 12. API FLOW

### Detailed Request / Response Data Flow

```
Frontend (Axios POST)
  └── Endpoint: /api/v1/generation/create
  └── Body: {
        application_id: 1,
        work_item_ids: ["US-101"],
        application_links: ["https://www.saucedemo.com"]
      }
        │
        ▼
FastAPI Router (app/api/v1/endpoints/generation.py)
        │
        ▼
WebExtractorService (app/services/web_extractor.py)
  └── Scrapes https://www.saucedemo.com
  └── Parsed DOM Context: {
        inputs: [{ id: "user-name", label: "Username" }, { id: "password", label: "Password" }],
        buttons: [{ text: "Login", id: "login-button" }]
      }
        │
        ▼
TestCaseGeneratorEngine (app/services/test_generator.py)
  └── Synthesizes Positive, Negative, Edge Test Cases
        │
        ▼
DeduplicationService (app/services/deduplication_service.py)
  └── Cleans duplicate scenarios
        │
        ▼
Returns JSON Response:
  └── { test_cases: [...], summary: { total_count: 12, positive_count: 5, ... } }
```

---

## 13. EXTERNAL SERVICES & INTEGRATIONS

1. **Azure DevOps REST API Service** ([`devops_service.py`](file:///d:/3rd%20uc/backend/app/services/devops_service.py)):
   * **Purpose**: Fetches real enterprise work items and acceptance criteria from Azure DevOps projects.
   * **Resilience & Fallback**: If Azure DevOps credentials or API endpoints are unreachable, the system automatically falls back to the database-driven local work item registry.
2. **Target Web Page Scraper** ([`web_extractor.py`](file:///d:/3rd%20uc/backend/app/services/web_extractor.py)):
   * **Purpose**: Fetches live web application pages via HTTPX async client, inspecting DOM HTML and SPA JavaScript bundle assets (`.js`).

---

## 14. AI / ML / GENAI COMPONENTS

> [!NOTE]
> **Deterministic Domain Rule Engine**: This project does **NOT** rely on external LLM APIs (such as OpenAI GPT or Anthropic Claude) or Vector Databases (such as FAISS or Pinecone). 

### How Test Synthesis Works Without Black-Box LLMs:
Instead of non-deterministic LLMs, the system employs a **Domain-Driven Rule Matrix Engine** ([`test_generator.py`](file:///d:/3rd%20uc/backend/app/services/test_generator.py)):
* **Syntactic Keyword Extraction**: Analyzes acceptance criteria for keywords like *"must"*, *"valid"*, *"invalid"*, *"maximum"*, *"boundary"*.
* **DOM Context Binding**: Directly binds observed DOM input IDs (e.g. `user-name`) and button labels (e.g. `Login`) into scenario steps.
* **Combinatorial Matrix Expansion**: Generates matrix permutations across user roles, input boundary constraints, missing fields, and double-click actions.
* **Deterministic Output**: Guarantees zero hallucinations and 100% reproducible test suites across runs.

---

## 15. DATA FLOW

### Data Transformation Pipeline

```
Raw Form Inputs (Frontend)
  ↓
Pydantic Request Payload Validation (GenerateTestCasesRequest)
  ↓
App & DevOps Query (SQLAlchemy ORM)
  ↓
DOM Context Scraping (WebExtractorService → WebContext dataclass)
  ↓
Combinatorial Generation Engine (TestCase dataclass instances)
  ↓
Quality Validation & Deduplication (DeduplicationService)
  ↓
Pydantic Serialization (GenerateTestCasesResponse)
  ↓
React State Update (App.tsx state)
  ↓
Excel Serialization (openpyxl Workbook in excel_exporter.py)
  ↓
Binary Download Stream (StreamingResponse)
```

---

## 16. IMPORTANT FUNCTIONS & CLASSES

### Backend Core Classes & Functions

1. **`WebExtractorService`** ([`web_extractor.py`](file:///d:/3rd%20uc/backend/app/services/web_extractor.py)):
   * `extract_context(urls: List[str]) -> WebContext`: Async function that downloads target URLs, parses HTML via `BeautifulSoup`, scans SPA JS bundles for JSX properties, and extracts input controls and buttons.
2. **`TestCaseGeneratorEngine`** ([`test_generator.py`](file:///d:/3rd%20uc/backend/app/services/test_generator.py)):
   * `generate(...) -> List[TestCase]`: Core synthesis engine that merges work items, app rules, and web context into categorized test cases.
3. **`ExcelExporterService`** ([`excel_exporter.py`](file:///d:/3rd%20uc/backend/app/services/excel_exporter.py)):
   * `generate_workbook(test_cases) -> BytesIO`: Constructs a multi-sheet `openpyxl` workbook (`Positive`, `Negative`, `Edge`) with dark header styling, auto-column fit, and priority colors.
4. **`DeduplicationService`** ([`deduplication_service.py`](file:///d:/3rd%20uc/backend/app/services/deduplication_service.py)):
   * `deduplicate(test_cases) -> List[TestCase]`: Removes redundant scenarios and formats sequential identifiers (`TC-POS-001`, `TC-NEG-001`, `TC-EDG-001`).

---

## 17. CONFIGURATION

### Configuration Files Overview

1. **`backend/requirements.txt`**: Declares backend dependencies (`fastapi`, `uvicorn`, `sqlalchemy`, `httpx`, `beautifulsoup4`, `openpyxl`, `pytest`).
2. **`frontend/package.json`**: Declares frontend dependencies (`react`, `react-dom`, `lucide-react`, `tailwindcss`, `typescript`, `vite`).
3. **`frontend/vite.config.ts`**: Configures Vite dev server and proxy rules forwarding `/api` requests to `http://127.0.0.1:8000`.

---

## 18. ERROR HANDLING

* **Backend Validation**: Pydantic models automatically validate incoming JSON request payloads, returning HTTP `422 Unprocessable Entity` for invalid payloads.
* **Scraping Resilience**: If a provided application link is offline or unreachable, `web_extractor.py` catches `httpx.HTTPError`, logs the error, marks the web context as unverified, and proceeds with requirement-driven synthesis without breaking the API pipeline.
* **Frontend Error Toasting**: Axios interceptors in [`api.ts`](file:///d:/3rd%20uc/frontend/src/services/api.ts) catch HTTP status codes (e.g. `401 Unauthorized`) and automatically clear session storage to redirect to login.

---

## 19. FILE UPLOAD / FILE PROCESSING

While the system does not process incoming file uploads, it processes web asset files (scraping external `.js` bundle files to parse SPA components) and generates outgoing formatted spreadsheet files (`.xlsx`).

---

## 20. EXPORT / DOWNLOAD

### Excel Exporter Subsystem (`openpyxl`)

When the user clicks **Export to Excel**:
1. Frontend posts test cases payload to `/api/v1/export/excel`.
2. [`excel_exporter.py`](file:///d:/3rd%20uc/backend/app/services/excel_exporter.py) creates an `openpyxl.Workbook`.
3. Creates 3 separate worksheets: **Positive Cases**, **Negative Cases**, **Edge Cases**.
4. Applies visual styling:
   * Header Row: Dark Slate Fill (`#1E293B`), White Bold Font (`#FFFFFF`).
   * Priority Cell Fills: High (`#FEE2E2` soft red), Medium (`#FEF3C7` soft yellow), Low (`#E0F2FE` soft blue).
   * Thin grid borders and auto-calculated column widths.
5. Returns `io.BytesIO` binary stream with headers: `content-disposition: attachment; filename=TestCases.xlsx`.

---

## 21. SECURITY

* **Password Security**: SHA-256 HMAC cryptographic password hashing ([`security.py`](file:///d:/3rd%20uc/backend/app/core/security.py)).
* **Authentication**: Bearer Token authorization header required for protected API endpoints.
* **CORS Middleware**: Explicit origin restrictions configured in [`main.py`](file:///d:/3rd%20uc/backend/app/main.py).
* **SQL Injection Prevention**: Parameterized queries enforced via SQLAlchemy ORM.

---

## 22. TESTING

### Automated Backend Test Suite

The system includes automated backend unit and integration tests located in [`backend/tests/`](file:///d:/3rd%20uc/backend/tests).

#### Test Files & Coverage:
* `test_auth.py`: Tests login, token generation, user info retrieval, and invalid credential handling.
* `test_applications.py`: Tests fetching application catalogs and application details.
* `test_devops_db.py`: Tests DevOps work item search and criteria retrieval from database.
* `test_generator.py`: Tests core test case synthesis engine across positive, negative, and edge scenarios.
* `test_link_awareness.py`: Tests live DOM scraping and SPA bundle context extraction.
* `test_export.py`: Tests openpyxl Excel file stream creation.

#### Running Tests:
```bash
cd backend
python -m pytest
```
*Result*: **20 passed** in 8.92 seconds.

---

## 23. RUNNING THE PROJECT

### Quickstart Guide

#### 1. Backend Setup & Run
```bash
cd backend
python run.py
```
*Runs FastAPI server at `http://127.0.0.1:8000` with live API docs at `http://127.0.0.1:8000/docs`.*

#### 2. Frontend Setup & Run
```bash
cd frontend
npm run dev
```
*Runs React dev server at `http://localhost:5173`.*

#### 3. Default Login Credentials
* **Email**: `admin@qa.com`
* **Password**: `admin123`

---

## 24. DEPLOYMENT

* **Backend**: Can be deployed using `uvicorn` behind an Nginx reverse proxy or containerized using Docker with Python 3.11 image.
* **Frontend**: Can be built using `npm run build` to produce static production assets in `frontend/dist/` served via Nginx or Vercel/Netlify.

---

## 25. COMPLETE END-TO-END EXAMPLE

### Detailed Execution Trace for a Login Scenario

```
User Action: Types 'https://www.saucedemo.com', selects 'US-101 Login', clicks 'Generate Test Cases'
  ↓
Frontend Component: ApplicationForm.tsx handles form submission
  ↓
API Service: frontend/src/services/api.ts calls POST /api/v1/generation/create
  ↓
Backend Route: backend/app/api/v1/endpoints/generation.py (create_test_cases)
  ↓
Service 1: WebExtractorService.extract_context(["https://www.saucedemo.com"])
  ├── Scrapes page HTML
  ├── Extracts input fields: id="user-name", id="password"
  └── Extracts action button: id="login-button", text="Login"
  ↓
Service 2: TestCaseGeneratorEngine.generate(...)
  ├── Rule 1 (Positive): Creates scenario "Valid Login with Standard Credentials" using observed selector 'user-name'
  ├── Rule 2 (Negative): Creates scenario "Omitted Password Submission"
  └── Rule 3 (Edge): Creates scenario "Rapid Double-Click Submission on login-button"
  ↓
Service 3: DeduplicationService.deduplicate(...) -> Assigns IDs TC-POS-001, TC-NEG-001, TC-EDG-001
  ↓
Response: FastAPI returns JSON payload with 12 test cases and metric statistics
  ↓
UI Update: App.tsx updates state -> MetricCards.tsx and TestCaseTable.tsx re-render instantly
```

---

## 26. INTERVIEW / MENTOR UNDERSTANDING

### Top 10 Questions & Concise Technical Answers

1. **Q: What makes this project "Application-Link-Aware"?**
   * **A**: Rather than generating abstract test steps, it inspects live web application URLs via DOM parsing and JS SPA bundle analysis, binding actual observed field IDs, placeholders, and button text directly into the generated test cases.
2. **Q: Why use a domain rule engine instead of an LLM like OpenAI?**
   * **A**: Rule engines guarantee 100% deterministic, repeatable, and hallucination-free outputs required in enterprise QA environments, without incurring API token costs or latency.
3. **Q: How does the backend handle single-page applications (SPAs)?**
   * **A**: When static HTML lacks standard form tags, `web_extractor.py` parses linked script bundles (`.js` files) to extract React/Vite JSX properties like `testId`, `placeholder`, `name`, and button text.
4. **Q: What happens if a provided application link is offline?**
   * **A**: The system handles HTTP exceptions gracefully, marks the context as unverified, and falls back to requirement-driven test generation so the user experience is never interrupted.
5. **Q: How is the database structured?**
   * **A**: SQLite database managed via SQLAlchemy with 3 core tables: `users` (auth), `applications` (business rules & domain specs), and `devops_work_items` (user stories & acceptance criteria).
6. **Q: How are Excel files generated and sent to the client?**
   * **A**: `openpyxl` generates styled `.xlsx` sheets in an in-memory `io.BytesIO` buffer, returned as a FastAPI `StreamingResponse` with Excel binary headers.
7. **Q: How does authentication work?**
   * **A**: Session authentication using UUID tokens signed on login, stored in `localStorage`, and passed via `Authorization: Bearer <token>` headers to FastAPI dependency injectors.
8. **Q: What test categories are synthesized?**
   * **A**: **Positive** (happy path & multi-role), **Negative** (missing fields & invalid data), and **Edge** (boundary limits & rapid submissions).
9. **Q: How does the system deduplicate scenarios?**
   * **A**: `DeduplicationService` computes normalized scenario hashes, removing duplicate steps and re-indexing IDs sequentially.
10. **Q: How is frontend routing and backend proxying handled?**
    * **A**: Vite config proxies `/api` requests to `http://127.0.0.1:8000`, bypassing CORS during local development.

---

## 27. WHAT I SHOULD SAY ABOUT THE PROJECT

### 1-Minute Elevator Pitch
> *"I worked on an Enterprise QA Application-Link-Aware Test Case Generation System that automates software test design. By combining Azure DevOps User Stories with live web application DOM and single-page application bundle context via URL scraping, our platform automatically synthesizes step-by-step Positive, Negative, and Edge test cases grounded in real UI element selectors. The system features a FastAPI backend, a React/TypeScript frontend, and an openpyxl export engine that produces multi-sheet, color-coded Excel workbooks ready for test execution."*

---

## 28. BEGINNER LEARNING PATH

1. **Python & Async Basics**: Learn Python `async`/`await` and FastAPI fundamentals.
2. **HTML DOM & Scraping**: Learn HTML element selectors and parsing using `BeautifulSoup4` and `httpx`.
3. **React & TypeScript**: Learn state management, components, and Axios API integration.
4. **SQLAlchemy & Database Modeling**: Understand ORM schemas and SQLite queries.
5. **Domain Rule Engines**: Understand combinatorial matrices, data validation, and Excel formatting using `openpyxl`.

---

## 29. FINAL PROJECT CHEAT SHEET

* **Project**: Enterprise QA Application-Link-Aware Test Case Generation System
* **Core Purpose**: Synthesize traceable Positive, Negative, and Edge test suites from Azure DevOps stories & live page URLs.
* **Frontend**: React 18, TypeScript, Vite, Tailwind CSS, Lucide React (`http://localhost:5173`)
* **Backend**: Python 3.11, FastAPI, Uvicorn, SQLAlchemy, Pydantic v2 (`http://127.0.0.1:8000`)
* **Database**: SQLite ([`backend/test_generator.db`](file:///d:/3rd%20uc/backend/test_generator.db))
* **Scraping Engine**: `httpx` async + `BeautifulSoup4` DOM parser + SPA JS bundle regex extractor
* **Export Engine**: `openpyxl` multi-sheet styled Excel workbook generator
* **Key Endpoints**: `/api/v1/auth/login`, `/api/v1/applications`, `/api/v1/devops/search`, `/api/v1/generation/create`, `/api/v1/export/excel`
* **Test Suite**: 20 automated backend pytest cases (`python -m pytest`)
* **Running Commands**:
  - Backend: `cd backend && python run.py`
  - Frontend: `cd frontend && npm run dev`
