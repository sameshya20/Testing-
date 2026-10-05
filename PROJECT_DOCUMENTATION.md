# PROJECT DOCUMENTATION: ENTERPRISE QA APPLICATION-LINK-AWARE TEST CASE GENERATION SYSTEM

---

## 1. PROJECT OVERVIEW

### Project Name
**Enterprise QA Application-Link-Aware Test Case Generation System**

---

### Purpose of the Project
The Enterprise QA Test Case Generation System is an intelligent, automated quality assurance platform designed to synthesize comprehensive, execution-ready software test suites. The platform bridges the gap between software requirements (Azure DevOps User Stories & Acceptance Criteria), enterprise backend business rules, and actual live application user interfaces (Application Links).

By analyzing accessible application page URLs alongside functional requirements, the system dynamically extracts UI form fields, input controls, action buttons, page titles, and observed validation error messages. It then synthesizes traceable **Positive**, **Negative**, and **Edge** test cases tailored specifically to the application under test and downloadable as professionally styled Excel workbooks (`.xlsx`).

---

### Business Problem Being Solved
Software testing in enterprise environments traditionally suffers from several critical bottlenecks:
1. **Generic & Abstract Test Cases**: Manual test cases often contain vague instructions such as *"Verify that the page works correctly"*, leading to ambiguity during execution.
2. **Disconnect from Real UI Controls**: Requirements written in ALM tools (e.g. Azure DevOps) do not specify exact field IDs, labels, or button titles present in the live web application.
3. **Incomplete Coverage of Edge & Negative Scenarios**: Testers frequently focus on happy-path scenarios, neglecting security roles, boundary value limits, rapid submission double-clicks, and malformed data payloads.
4. **Time-Consuming Manual Authoring**: Authoring 50+ detailed test cases per sprint consumes hours or days of high-cost QA engineering time.

---

### Use Case & Target Users
* **QA Leads & Test Engineers**: Rapidly generate comprehensive test suites for sprint items, reducing test design effort by up to 90%.
* **Software Developers**: Preview required positive, negative, and edge validation criteria before starting development (TDD / BDD alignment).
* **Business Analysts & Product Owners**: Validate that acceptance criteria in Azure DevOps match actual application pages and workflows.
* **Scrum Masters & Agile Teams**: Export standardized, traceable Excel test artifacts attached directly to Azure DevOps work items.

---

### Main Features & System Capabilities

1. **Secure Token-Based Authentication**: JWT bearer authentication with session login, logout, and token revocation.
2. **Azure DevOps Integration**: Direct fetching and searching of User Stories and Acceptance Criteria via Azure DevOps REST API, with fallback mock dataset for offline development.
3. **Database-Driven Application Rules**: Pre-configured database registry storing application domains, business rules, user roles, key modules, and default URLs.
4. **Live DOM & SPA Bundle Context Extractor**:
   - Fetches live target application web pages using `httpx` async client.
   - Parses standard HTML DOM structures (`Soup4`) for input fields, labels, placeholders, buttons, forms, and error alerts.
   - Inspects JavaScript bundle files (`.js`) for Single-Page Applications (SPAs built with React, Vite, Vue, Angular) to extract JSX properties (`placeholder`, `name`, `id`, `testId`, `value`, error strings).
5. **Multi-Link End-to-End Workflow Analysis**: Analyzes multiple links in sequence (e.g. `Product Page` → `Cart Page` → `Checkout Page`) to generate multi-step end-to-end user journey test cases.
6. **Authenticity & Failure Resilience (Req 16 & 20)**: Uses strictly observed UI elements for verified links. If a link is unreachable, the system does not fabricate false UI elements, marking the context as unverified and proceeding with requirement-driven cases.
7. **Requirement + Link Context Priority Matrix**: Priority ordering: Requirement (source of truth) + Application Business Rules + Live Page DOM Context.
8. **Multi-Categorized Test Suite Synthesis**: Automatically categorizes generated cases into **Positive**, **Negative**, and **Edge** test cases.
9. **Full Traceability**: Every test case includes User Story ID, Acceptance Criteria ref, Application Page, Application Link, Category, Priority, Scenario, Description, Preconditions, Test Data, Test Steps, and Expected Result.
10. **Interactive Management Dashboard**: Modern responsive UI for selecting applications, filtering acceptance criteria, previewing link metadata, editing test cases in real-time, and filtering by category/priority.
11. **Styled Multi-Sheet Excel Exporter**: Generates openpyxl `.xlsx` workbooks featuring formatted headers, freeze panes, auto-fit columns, word wrapping, and priority color highlighting.

---

### Step-by-Step End-to-End User Flow

#### Simple Language Summary
> When a user opens the web application, they log in securely. They select their target software project and pick the User Stories they want to test. Optionably, they provide the web link (URL) of the live application page. When they click "Generate", the system visits the website, reads the buttons and form fields, and automatically generates positive, negative, and boundary test cases. The user can review or edit these test cases on the screen, and finally click "Export to Excel" to download a formatted spreadsheet ready for testing.

#### Technical Execution Flow
1. **User Authentication**:
   - User navigates to `http://localhost:5173/`.
   - Submits credentials via `/api/v1/auth/login`.
   - FastAPI verifies password hash (Bcrypt) and returns a signed JWT bearer token.
   - React application stores the token in `localStorage` and initializes Axios authorization headers.
2. **Requirement & Application Selection**:
   - Application fetches registered application specifications from `/api/v1/applications`.
   - Application queries Azure DevOps work items from `/api/v1/devops/search` or `/api/v1/devops/acceptance-criteria`.
   - User selects target application (e.g. *SauceDemo Swag Store*) and specific User Stories (e.g. *US-101 Login Authentication*).
3. **Application Link Analysis**:
   - User provides one or multiple application links (e.g., `https://www.saucedemo.com`).
   - Frontend posts generation request payload to `/api/v1/generation/create`.
   - `web_extractor` executes async HTTP request with custom browser headers to the provided URL.
   - If DOM parsing finds standard input elements, it extracts `id`, `name`, `label`, `placeholder`, and `type`. If DOM is an SPA container, it fetches linked script bundles and parses React/Vite JSX properties (`testId`, `placeholder`, `name`, `id`, `value`).
4. **Test Suite Synthesis**:
   - `test_generator_engine` evaluates the requirement ACs against application user roles and business rules.
   - If link extraction succeeded (`status: "success"`), it binds exact observed field names and button labels to scenario titles, test steps, test data, and expected results.
   - Generates Positive cases (valid workflow, multi-role access, multi-page E2E journey), Negative cases (omitted compulsory field, security role rejection, malformed payload), and Edge cases (upper boundary limits, unicode/special chars, rapid double-click submit).
   - `deduplication_service` removes duplicate scenarios and assigns sequential IDs (`TC-POS-001`, `TC-NEG-001`, `TC-EDG-001`).
5. **Interactive Preview & Edit**:
   - Frontend renders metrics cards (Total count, Positive, Negative, Edge, Stories covered, ACs evaluated, Pages analyzed).
   - Interactive table allows tab switching (`All`, `Positive`, `Negative`, `Edge`), searching, and modal editing.
6. **Excel Workbook Download**:
   - User clicks **"Export to Excel"**.
   - Frontend posts test cases payload to `/api/v1/export/excel`.
   - `excel_exporter` constructs a 3-sheet `openpyxl` workbook (`Positive`, `Negative`, `Edge`) with dark headers, auto-filters, custom column dimensions, and conditional priority fills (`#FEE2E2` for High, `#FEF3C7` for Medium, `#E0F2FE` for Low).
   - FastApi returns `io.BytesIO` binary stream with `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` headers, triggering instant browser download.

---

## 2. BUSINESS USE CASE

### Complete Business Scenario

#### Background & Problem Statement
In enterprise software development, Quality Assurance teams spend considerable manual effort translating user stories into structured test cases. 

* **Manual Process**: A QA engineer opens Azure DevOps, reads a requirement such as *"User should be able to log in"*, opens a blank Excel spreadsheet or test management tool, and manually types test steps.
* **Flaws in Manual Process**:
  - **Superficiality**: Manual cases often say *"Enter valid credentials and submit"*. They fail to specify exact field labels (e.g., whether the field is `user-name`, `email`, or `account_number`).
  - **Lack of Negative/Edge Rigor**: Under sprint time pressure, QA engineers rarely write comprehensive edge cases (e.g., maximum character boundaries, rapid submit double-click handling, or special character payload sanitization).
  - **No UI Verification**: Manual test cases quickly become outdated when UI developers change button text or form field structure.
  - **Inconsistency**: Different QA engineers write test cases in different formats, leading to uneven test coverage across squads.

#### Proposed Solution
The Application-Link-Aware Test Case Generation System introduces **automated 3-way context integration**:
$$\text{Test Cases} = \text{Requirement (Azure DevOps)} + \text{Application Business Rules (DB)} + \text{Live Application Page Context (DOM/JS)}$$

#### Realistic Example Scenario

**Requirement**: User Story `US-101`: *"User should be able to log in."*

* **Scenario A: Application Link 1 = SauceDemo Login (`https://www.saucedemo.com`)**
  - *Extracted Context*: Fields = `user-name`, `password`; Button = `Login` (`login-button`); Error = `Epic sadface: Username is required`.
  - *Generated Positive Case*:
    - Scenario: `[US-101] Verify Login Workflow on Swag Labs Login`
    - Steps: `1. Navigate to Swag Labs Login (https://www.saucedemo.com). 2. Authenticate as 'Standard User'. 3. Input valid test data into verified 'user-name' field. 4. Input valid test data into verified 'password' field. 5. Click 'Login' button.`
  - *Generated Negative Case*:
    - Scenario: `[US-101] Verify Validation Error on Omitted Verified 'user-name' Field`
    - Expected Result: `Submission blocked; UI displays highlighted error (Epic sadface: Username is required).`

* **Scenario B: Application Link 2 = Enterprise CRM Sign-In (`https://crm.enterprise.com/login`)**
  - *Extracted Context*: Fields = `email_address`, `security_pin`; Button = `Sign In`; Error = `Email address is required`.
  - *Generated Positive Case*:
    - Scenario: `[US-101] Verify Sign In Workflow on CRM Enterprise Sign In`
    - Steps: `1. Navigate to CRM Enterprise Sign In. 2. Authenticate as 'Standard User'. 3. Input valid test data into verified 'email_address' field. 4. Input valid test data into verified 'security_pin' field. 5. Click 'Sign In' button.`

Notice that for the **exact same requirement**, changing the Application Link produces **measurably different, highly specific, authentic test cases** matching the respective real-world UI controls.

---

## 3. COMPLETE TECHNOLOGY STACK

### Frontend Technology Stack

| Technology | Category | What It Is | Why Used in This Project | Where Used |
| :--- | :--- | :--- | :--- | :--- |
| **TypeScript** | Programming Language | Typed superset of JavaScript providing static type checking and IntelliSense. | Prevents runtime errors, enforces strict interfaces for API request/response models and test case schema structures. | Entire frontend codebase (`frontend/src/**/*.ts`, `frontend/src/**/*.tsx`). |
| **React 18** | UI Framework | Declarative, component-based JavaScript library for building user interfaces. | Enables reactive component state management, fast virtual DOM rendering, and modular UI structure. | `frontend/src/App.tsx`, `frontend/src/components/*`. |
| **Vite** | Build Tool & Dev Server | Next-generation frontend tooling offering fast cold server start and Instant Hot Module Replacement (HMR). | Provides lightning-fast compilation, optimized production bundling, and quick developer feedback loop. | `frontend/vite.config.ts`, `frontend/package.json`. |
| **Tailwind CSS** | Styling Framework | Utility-first CSS framework for building custom modern user interfaces directly in markup. | Allows rapid creation of dark-mode UI, glassmorphism cards, responsive grid layouts, and cohesive color tokens. | `frontend/src/index.css`, `frontend/src/App.css`, component files. |
| **Lucide React** | UI Iconography | Clean, lightweight icon library for React applications. | Provides clear visual indicators for link status, test case categories, download buttons, and modal actions. | `frontend/src/components/Header.tsx`, `ApplicationForm.tsx`, `TestCaseTable.tsx`. |
| **Axios / Native Fetch** | API Communication | Promise-based HTTP client for sending requests to backend API endpoints. | Standardized async HTTP communication with automatic JSON parsing and bearer token authorization header injection. | `frontend/src/services/api.ts`. |
| **React Hooks (`useState`, `useEffect`)** | State Management | Native React primitives for managing local component state and side effects. | Manages active tab state, form input states, modal visibility, application selection, link checklist, and API response caching. | `frontend/src/App.tsx`, `ApplicationForm.tsx`, `TestCaseTable.tsx`. |

---

### Backend Technology Stack

| Technology | Category | What It Is | Why Used | Which Files Use It | Contribution to Application |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Python 3.11+** | Programming Language | Modern high-level interpreted programming language. | Offers rich ecosystem for web APIs, async I/O, HTML parsing, data processing, and document generation. | Entire backend codebase (`backend/app/**/*.py`). | Core server runtime and business logic engine. |
| **FastAPI** | Web Framework | Modern, high-performance web framework for building APIs with Python based on standard type hints. | Provides automatic OpenAPI docs, high speed, native async support, dependency injection, and Pydantic request validation. | `backend/app/main.py`, `backend/app/api/**/*.py`. | Defines API router structure and request handling endpoints. |
| **Uvicorn** | ASGI Server | Lightning-fast ASGI web server implementation for Python. | Serves the FastAPI application asynchronously on local network host and port. | `backend/run.py`. | Production and development HTTP server process. |
| **Pydantic v2** | Data Validation | Data validation and settings management library using Python type annotations. | Enforces strict payload validation for login, generation requests, link items, test case models, and Excel export requests. | `backend/app/schemas/*.py`. | Ensures data integrity between frontend and backend. |
| **SQLAlchemy 2.0** | ORM Engine | SQL toolkit and Object Relational Mapper for database interaction. | Provides object-oriented database models for Users and Applications, abstraction over SQL queries, and session management. | `backend/app/db/*.py`, `backend/app/models/*.py`. | Database access layer for application rules and user accounts. |
| **SQLite** | Database Engine | Self-contained, serverless, zero-configuration SQL database engine. | Lightweight relational database for persisting enterprise applications, business rules, user credentials, and session state. | `backend/test_generator.db`. | File-based storage for application specifications and user data. |
| **HTTPX** | Async HTTP Client | Fully featured async HTTP client for Python 3. | Fetches live external web application URLs asynchronously with custom browser headers, timeout controls, and redirect handling. | `backend/app/services/web_extractor.py`, `devops_service.py`. | Responsible for fetching live web page content and calling Azure DevOps REST APIs. |
| **BeautifulSoup4** | HTML Parser | Python library for pulling data out of HTML and XML files. | Navigates DOM trees to extract input elements, forms, action buttons, labels, placeholders, titles, and error banners. | `backend/app/services/web_extractor.py`. | Converts raw HTML responses into structured UI control metadata. |
| **PyJWT & Passlib / Bcrypt** | Security & Auth | Cryptographic utilities for password hashing and JSON Web Token (JWT) signing. | Hashes user passwords securely with Bcrypt and generates signed JWT access tokens for protected API routes. | `backend/app/core/security.py`, `backend/app/api/deps.py`. | Handles user authentication and route protection. |
| **OpenPyXL** | Excel Library | Python library to read/write Excel 2010 xlsx/xlsm files. | Constructs multi-sheet styled Excel workbooks containing formatted test case rows, headers, column auto-sizing, and priority color fills. | `backend/app/services/excel_exporter.py`. | Formats and generates downloadable `.xlsx` test suite workbooks. |
| **Pytest & Pytest-Asyncio** | Testing Framework | Testing framework for Python that makes it easy to write small, readable tests. | Executes automated unit tests for web extraction, test generation rules, link sensitivity, and API endpoints. | `backend/tests/*.py`. | Validates system correctness and regression safety. |

---

### External Services & Integration Architecture

```
+-----------------------------------------------------------------------+
|                            EXTERNAL SERVICES                          |
+-----------------------------------------------------------------------+
                                  |
         +------------------------+------------------------+
         |                                                 |
         v                                                 v
+-----------------------------------+    +-----------------------------------+
|     AZURE DEVOPS REST API         |    |    EXTERNAL APPLICATION LINKS     |
| (https://dev.azure.com/{org}/...) |    |   (Live Web App / SPA Pages)      |
+-----------------------------------+    +-----------------------------------+
| - Work Item Retrieval API         |    | - Async HTTP GET Requests         |
| - Acceptance Criteria Query       |    | - HTML DOM Structure Parsing      |
| - WIT REST API (v7.0)             |    | - React/Vite JS Bundle Inspection |
| - Fallback Enterprise Mock Set    |    | - Error Container Extraction      |
+-----------------------------------+    +-----------------------------------+
         |                                                 |
         +------------------------+------------------------+
                                  |
                                  v
+-----------------------------------------------------------------------+
|               ENTERPRISE BACKEND SERVICE LAYER (FASTAPI)              |
+-----------------------------------------------------------------------+
```

1. **Azure DevOps REST API**:
   - **Endpoint**: `https://dev.azure.com/{organization}/{project}/_apis/wit/workitems/{id}?api-version=7.0`
   - **Authentication**: HTTP Basic Authentication using Personal Access Tokens (PAT).
   - **Functionality**: Fetches User Story titles, descriptions, and `Microsoft.VSTS.Common.AcceptanceCriteria` fields.
   - **Resilience**: If PAT is unconfigured or network is offline, seamlessly fails over to an internal mock dataset containing enterprise user stories (Banking, Healthcare Claims, E-Commerce Cart, HR Leave, Insurance Risk).

2. **External Application Links (Live Page Inspection)**:
   - **Protocol**: HTTP/HTTPS via `httpx.AsyncClient`.
   - **Headers**: User-Agent spoofing (`Mozilla/5.0 Chrome/120.0`) to avoid bot-blocking.
   - **Functionality**: Accesses target URLs, extracts DOM inputs/buttons/labels, and parses linked JavaScript bundles for SPAs (React/Vite).

---

## 4. SYSTEM ARCHITECTURE

### Architecture Layer Diagram

```mermaid
flowchart TD
    User(["👤 Enterprise User / QA Engineer"]) -->|Interacts via Web Browser| Frontend["🖥️ React 18 + Vite + Tailwind CSS\n(Port 5173)"]

    subgraph FrontendLayer ["Frontend Application Layer"]
        Frontend --> FormComp["ApplicationForm Component"]
        Frontend --> TableComp["TestCaseTable Component"]
        Frontend --> ApiService["API Service (Axios / Fetch)"]
    end

    ApiService -->|HTTPS / REST API + JWT Bearer| FastAPI["⚙️ FastAPI Backend Engine\n(Port 8000)"]

    subgraph BackendLayer ["Backend API & Middleware Layer"]
        FastAPI --> AuthDep["Security / JWT Middleware"]
        FastAPI --> Router["API Router (/api/v1)"]
    end

    Router --> AppEndpoint["/applications"]
    Router --> DevOpsEndpoint["/devops"]
    Router --> GenEndpoint["/generation/create"]
    Router --> ExportEndpoint["/export/excel"]

    subgraph ServiceLayer ["Core Service & Processing Layer"]
        GenEndpoint --> WebExtractor["WebContextExtractor\n(httpx + BeautifulSoup + JS Parser)"]
        GenEndpoint --> TestEngine["TestGeneratorEngine"]
        DevOpsEndpoint --> DevOpsService["AzureDevOpsService"]
        ExportEndpoint --> ExcelService["ExcelExporterService (OpenPyXL)"]
        AppEndpoint --> DB["SQLAlchemy ORM + SQLite DB\n(test_generator.db)"]
    end

    subgraph ExternalLayer ["External Data & Web Sources"]
        DevOpsService -->|REST API (PAT Auth)| ADO["Azure DevOps Services"]
        WebExtractor -->|Async HTTP GET| LiveWeb["Live Application URLs / SPAs"]
    end

    TestEngine --> DedupEngine["Deduplication & Quality Service"]
    DedupEngine --> GenResponse["Structured TestCase Response"]
    GenResponse --> Frontend

    ExcelService -->|Binary Excel Stream (.xlsx)| User Download
```

---

### Comprehensive Layer Breakdown

1. **User Presentation Layer (Browser)**:
   - Renders modern dark-mode responsive interface.
   - Captures user selections (Application, User Stories, Acceptance Criteria, Application Links).
   - Displays real-time context badges (Observed Fields, Verified Actions, Observed Error Messages).

2. **Frontend Component Architecture Layer**:
   - `LoginPage.tsx`: Authenticates user credentials and stores JWT token.
   - `ApplicationForm.tsx`: Multi-requirement selector, live link checklist, and requirement-link mapper.
   - `MetricCards.tsx`: Displays summary statistics (Total Cases, Positive, Negative, Edge, Story coverage, Pages analyzed).
   - `TestCaseTable.tsx`: Tabbed view (`All`, `Positive`, `Negative`, `Edge`), search bar, priority filters, and row-level modal editor.

3. **Backend API Gateway Layer (FastAPI)**:
   - `auth.py`: Token generation (`/login`), user details (`/me`), and logout token revocation (`/logout`).
   - `applications.py`: Retrieves database-registered enterprise applications and derives available module page links.
   - `devops.py`: Queries Azure DevOps work items, acceptance criteria lists, and search endpoint.
   - `generation.py`: Coordinates DOM extraction and test suite synthesis.
   - `export.py`: Converts generated test cases into styled openpyxl Excel workbooks.

4. **Business Logic & Processing Layer**:
   - `web_extractor.py`: Extracts DOM elements and JS script properties from application links.
   - `test_generator.py`: Executes priority rules to synthesize Positive, Negative, and Edge test cases.
   - `deduplication_service.py`: Computes scenario uniqueness to prevent duplicate test cases.
   - `excel_exporter.py`: Applies openpyxl styling (colors, gridlines, auto-filters, column dimensions).

5. **Persistence & Data Source Layer**:
   - `test_generator.db`: SQLite database storing user accounts and pre-configured enterprise applications with custom business rules.
   - `Azure DevOps REST API`: External ALM system providing user story specifications.
   - `External Application Page URLs`: External target web applications providing real-world UI element controls.

---

## 5. SUMMARY

The **Enterprise QA Application-Link-Aware Test Case Generation System** transforms software quality assurance by automatically generating specific, traceable, and authentic test cases directly from requirements and live application web pages. It eliminates generic test cases, ensures complete negative and edge case coverage, and delivers ready-to-execute Excel test workbooks in seconds.
