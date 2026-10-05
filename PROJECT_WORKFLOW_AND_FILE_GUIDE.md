# Project Workflow and File Responsibility Guide
## Complete Technical Architecture, Execution Flow & File-by-File Reference (Non-AI Implementation)

---

## 1. Project Overview

The **Enterprise Test Case Generator** is a full-stack, enterprise-grade web application designed for Quality Assurance (QA) engineers, test leads, and developers. Its primary objective is to take structured software requirements (such as Azure DevOps-style hierarchical Areas, User Stories, Acceptance Criteria, and Application URLs) and automatically synthesize structured, actionable, and comprehensive **Positive**, **Negative**, and **Edge** test cases.

### Core Value & Non-AI Philosophy
Unlike modern generative AI prototypes that depend on unpredictable cloud Large Language Models (LLMs), prompt engineering, or vector database embeddings, **this entire project operates on 100% deterministic, rule-based business logic, relational database persistence, and DOM web scraping**:
1. **Deterministic Quality & Predictability**: Given the same User Story, Acceptance Criteria, and application parameters, the application consistently generates exact, repeatable, production-ready test scenarios with complete boundary conditions.
2. **Zero Cloud/AI Costs & Latency**: There are no OpenAI/Anthropic/Gemini API calls, no token fees, no token limits, and no model hallucinations. Test generation occurs locally in milliseconds.
3. **Enterprise Security & Data Sovereignty**: Requirements, credentials, and application URLs never leave the enterprise boundary or local server.
4. **Complete Manual Control**: QA engineers can select exact hierarchical Areas, choose specific User Stories, toggle individual Acceptance Criteria via checkboxes, configure application target URLs, inspect generated test cases in a tabbed interface, edit scenarios in-place, delete unwanted rows, and export clean, styled, multi-sheet Microsoft Excel workbooks (`.xlsx`).

---

## 2. Architecture

The application is structured into a clean, decoupled 3-tier client-server architecture:

```
+---------------------------------------------------------------------------------------+
|                                    PRESENTATION LAYER                                 |
|                               (React 18 + TypeScript + Vite)                          |
|                                                                                       |
|   LoginPage.tsx  <--->  Header.tsx  <--->  ApplicationForm.tsx (AreaSelector)       |
|                                  <--->  MetricCards.tsx  <--->  TestCaseTable.tsx     |
|                                                         <--->  EditTestCaseModal.tsx  |
+-------------------------------------------+-------------------------------------------+
                                            |
                               HTTP / REST (JSON)
                        Bearer Token Session Authentication
                                            |
+-------------------------------------------v-------------------------------------------+
|                                    APPLICATION LAYER                                  |
|                             (FastAPI + Uvicorn ASGI Server)                           |
|                                                                                       |
|   app/main.py (CORS, Lifespan)                                                        |
|   app/api/v1/endpoints/                                                               |
|     ├── auth.py          (Login, Session Validation, Logout)                          |
|     ├── applications.py  (Catalog of Enterprise Applications)                         |
|     ├── devops.py        (Areas, User Stories, Acceptance Criteria)                   |
|     ├── generation.py    (Multi-Requirement Test Case Synthesis)                      |
|     └── export.py        (Multi-Sheet OpenPyXL Workbook Generation)                   |
|                                                                                       |
|   app/services/                                                                       |
|     ├── devops_service.py        (Local DB + Mock / Live ADO Fallback)                |
|     ├── web_extractor.py         (HTTPX + BeautifulSoup4 HTML Scraper)                 |
|     ├── test_generator.py        (Rule Analyzer & Test Synthesis Engine)              |
|     ├── combination_engine.py    (Orthogonal Parameter Combinations)                  |
|     ├── deduplication_service.py (SequenceMatcher Duplicate Detection)                |
|     ├── quality_validator.py     (Coverage Auditing & Verification)                   |
|     └── excel_exporter.py        (Styled openpyxl Excel Generator)                    |
+-------------------------------------------+-------------------------------------------+
                                            |
                                SQLAlchemy 2.0 ORM
                                            |
+-------------------------------------------v-------------------------------------------+
|                                      DATA LAYER                                       |
|                                (SQLite Relational DB)                                 |
|                                                                                       |
|   test_generator.db                                                                   |
|     ├── users                (Registered user accounts & hashed credentials)          |
|     ├── applications         (Business systems, domain rules, default URLs)           |
|     ├── areas                (Hierarchical project parts & modules)                   |
|     ├── user_stories         (Requirements, agile titles, descriptions, states)       |
|     └── acceptance_criteria  (Gherkin/functional criteria numbered rules)             |
+---------------------------------------------------------------------------------------+
```

### Technology Breakdown

| Layer | Technology | Version | Purpose in this Project |
| :--- | :--- | :--- | :--- |
| **Frontend Framework** | React | 19.x / 18.x | Component-based interactive User Interface |
| **Frontend Language** | TypeScript | 5.x / 6.x | Strict type safety for data models, API payloads, and UI events |
| **Build Tool & Bundler** | Vite | 8.x | Ultra-fast development server with reverse-proxy support |
| **Frontend Styling** | Tailwind CSS | 4.x | Utility-first dark enterprise styling (`slate-950`, `slate-900`) |
| **UI Iconography** | Lucide React | 1.x | Enterprise icons for tabs, folders, statuses, actions |
| **Backend Framework** | FastAPI | >= 0.104.0 | High-performance async Python web framework with auto OpenAPI |
| **ASGI Web Server** | Uvicorn | >= 0.24.0 | Lightning-fast asynchronous server running on `127.0.0.1:8000` |
| **Database Engine** | SQLite | 3.x | Lightweight, zero-config relational database file (`test_generator.db`) |
| **Database ORM** | SQLAlchemy | >= 2.0.0 | Declarative database models, query builder, and relationship manager |
| **Data Validation** | Pydantic | >= 2.4.0 | Strict request/response schema serialization and type enforcement |
| **HTTP Client** | HTTPX | >= 0.25.0 | Async HTTP client used for web scraping and DevOps API calls |
| **HTML Parser** | BeautifulSoup4 | >= 4.12.0 | DOM parser extracting form inputs, action buttons, headings, and labels |
| **Spreadsheet Engine** | openpyxl | >= 3.1.2 | Generates multi-sheet styled `.xlsx` files with colored headers and filters |
| **Automated Testing** | pytest | >= 7.4.0 | Backend unit and integration test suite |

---

## 3. Folder Structure

The project root is organized into two primary subdirectories: `backend/` and `frontend/`. Only active, functional directories and files are present:

```
d:/3rd uc/
├── test_generator.db                 # SQLite database file created/read by backend
├── backend/
│   ├── run.py                        # Backend launcher script (starts Uvicorn on 127.0.0.1:8000)
│   ├── requirements.txt              # Python package dependencies
│   ├── test_generator.db             # Local database copy in backend directory
│   ├── app/
│   │   ├── __init__.py               # Package marker
│   │   ├── main.py                   # FastAPI application initialization & CORS setup
│   │   ├── core/
│   │   │   ├── __init__.py           # Package marker
│   │   │   ├── config.py             # Application settings & environment variables
│   │   │   └── security.py           # HMAC SHA-256 password hashing & Bearer token store
│   │   ├── db/
│   │   │   ├── __init__.py           # Package marker
│   │   │   ├── session.py            # SQLAlchemy database engine and SessionLocal session factory
│   │   │   └── init_db.py            # Database schema creator and seed data populator
│   │   ├── models/                   # SQLAlchemy ORM Database Models
│   │   │   ├── __init__.py           # Model aggregator export
│   │   │   ├── user.py               # User table model (users)
│   │   │   ├── application.py        # Application table model (applications)
│   │   │   └── devops.py             # Area, UserStory, AcceptanceCriteria models
│   │   ├── schemas/                  # Pydantic Schemas (Request/Response DTOs)
│   │   │   ├── __init__.py           # Package marker
│   │   │   ├── user.py               # LoginRequest, LoginResponse, UserRead
│   │   │   ├── application.py        # ApplicationRead, ApplicationBase
│   │   │   ├── devops.py             # AreaRead, UserStoryRead, AcceptanceCriteriaRead, DevOpsWorkItem
│   │   │   └── test_case.py          # TestCase, TestCaseGenerationRequest, CoverageSummary
│   │   ├── api/
│   │   │   ├── __init__.py           # Package marker
│   │   │   ├── deps.py               # get_current_user HTTPBearer dependency
│   │   │   └── v1/
│   │   │       ├── api.py            # APIRouter combining auth, apps, devops, generation, export
│   │   │       └── endpoints/        # HTTP Route Handlers
│   │   │           ├── auth.py       # POST /login, GET /me, POST /logout
│   │   │           ├── applications.py # GET /applications, GET /applications/{id}
│   │   │           ├── devops.py     # Areas, User Stories, Acceptance Criteria endpoints
│   │   │           ├── generation.py # POST /generation/create (Test case generator)
│   │   │           └── export.py     # POST /export/excel (Excel download)
│   │   └── services/                 # Pure Business Logic & Auxiliary Services
│   │       ├── __init__.py           # Package marker
│   │       ├── devops_service.py     # Database and Azure DevOps fallback service
│   │       ├── web_extractor.py      # Non-AI HTML DOM and form input scraper
│   │       ├── combination_engine.py # Orthogonal parameter matrix generator
│   │       ├── deduplication_service.py # SequenceMatcher duplicate test case detector
│   │       ├── quality_validator.py  # Test coverage auditor
│   │       ├── test_generator.py     # Deterministic rule analyzer & test case synthesis engine
│   │       └── excel_exporter.py     # Styled openpyxl workbook builder
│   └── tests/                        # Automated Pytest suite
│       ├── test_auth.py              # Authentication test cases
│       ├── test_applications.py      # Application catalog tests
│       ├── test_devops_db.py         # Area, Story, Criteria relational query tests
│       ├── test_generator.py         # Deterministic test generation rule tests
│       ├── test_link_awareness.py    # Web extractor and link context integration tests
│       └── test_export.py            # Excel workbook generation tests
└── frontend/
    ├── package.json                  # Node.js project manifest & scripts
    ├── vite.config.ts                # Vite dev server configuration & /api proxy
    ├── index.html                    # Root HTML document
    └── src/
        ├── main.tsx                  # React DOM bootstrap entrypoint
        ├── App.tsx                   # Main state orchestrator & view controller
        ├── index.css                 # Global CSS & Tailwind CSS layer definitions
        ├── App.css                   # Component auxiliary styles
        ├── types/
        │   └── index.ts              # TypeScript interfaces (User, TestCase, Area, etc.)
        ├── services/
        │   └── api.ts                # REST API client functions using native fetch()
        └── components/               # React UI Components
            ├── LoginPage.tsx         # User authentication form
            ├── Header.tsx            # Navigation bar with user profile dropdown
            ├── AreaSelector.tsx      # Hierarchical tree selector for DevOps Areas/Parts
            ├── ApplicationForm.tsx   # 5-step interactive workflow form
            ├── MetricCards.tsx       # Summary banner & 4 metric counters
            ├── TestCaseTable.tsx     # Tabbed table (Positive/Negative/Edge) with actions
            └── EditTestCaseModal.tsx # In-place modal editor for test case scenarios
```

---

## 4. Application Startup

### Backend Startup Sequence
When executing `python backend/run.py`:
1. **Python Path Resolution**: [run.py](file:///d:/3rd%20uc/backend/run.py#L5-L6) adds the `backend/` directory to `sys.path`.
2. **ASGI Server Launch**: Uvicorn initializes the FastAPI app defined in [main.py](file:///d:/3rd%20uc/backend/app/main.py#L18-L23) on host `127.0.0.1` and port `8000`.
3. **Database Lifespan Execution**: The `@asynccontextmanager lifespan(app: FastAPI)` function in [main.py](file:///d:/3rd%20uc/backend/app/main.py#L9-L16) invokes `init_db()`:
   - `Base.metadata.create_all(bind=engine)` inspects [models](file:///d:/3rd%20uc/backend/app/models/__init__.py#L1-L6) and creates SQLite tables: `users`, `applications`, `areas`, `user_stories`, and `acceptance_criteria` if they do not exist.
   - **Seed Users**: Seeds `admin@enterprise.com` and `qa@enterprise.com` with hashed password `password123` via `hash_password()`.
   - **Seed Applications**: Populates 5 enterprise applications (`BANK-PORTAL`, `HEALTH-CLAIMS`, `ECOMM-CORE`, `HR-LEAVE`, `INS-UNDERWRITE`) with business rules, key modules, and user roles.
   - **Seed Areas**: Populates a multi-level hierarchical tree: Root `Project` -> Categories (`Finance`, `HR`, `Healthcare`, `Sales`, `Insurance`) -> Leaf Areas (`Payments`, `Banking`, `Recruitment`, `Payroll`, `Claims`, `Orders`, `Customers`, `Underwriting`).
   - **Seed User Stories**: Seeds stories `US-001` through `US-004` and `US-101` through `US-105` linked to specific Areas.
   - **Seed Acceptance Criteria**: Seeds detailed functional criteria for each story (e.g. `US-101-AC-01` through `US-101-AC-04`, `US-102-AC-01` through `US-102-AC-04`, etc.).
4. **CORS Middleware Configuration**: [main.py](file:///d:/3rd%20uc/backend/app/main.py#L32-L38) applies `CORSMiddleware` using `settings.CORS_ORIGINS` allowing frontend requests from ports `5173`, `5174`, and `3000`.
5. **Router Registration**: [main.py](file:///d:/3rd%20uc/backend/app/main.py#L40) mounts `api_router` from [api.py](file:///d:/3rd%20uc/backend/app/api/v1/api.py#L6-L10) under prefix `/api/v1`.

### Frontend Startup Sequence
When executing `npm run dev` in `frontend/`:
1. **Vite Configuration Loading**: Vite reads [vite.config.ts](file:///d:/3rd%20uc/frontend/vite.config.ts#L6-L17), activating React and Tailwind CSS v4 plugins.
2. **Reverse Proxy Setup**: Vite configures an internal HTTP proxy mapping any frontend call to `/api` directly to `http://127.0.0.1:8000`.
3. **HTML & DOM Mount**: Vite serves [index.html](file:///d:/3rd%20uc/frontend/index.html#L1-L14). The browser loads [main.tsx](file:///d:/3rd%20uc/frontend/src/main.tsx#L6-L10), which mounts `<App />` inside `#root`.
4. **Session Verification**: In [App.tsx](file:///d:/3rd%20uc/frontend/src/App.tsx#L38-L58), `useEffect` runs:
   - Registers a session expired handler to intercept 401s.
   - Reads `localStorage.getItem('auth_token')`. If a token exists, calls `fetchCurrentUser()` (`GET /api/v1/auth/me`).
   - If the token is valid, sets `currentUser`, displaying the main dashboard.
   - If no token exists or the token has expired, sets `currentUser = null`, displaying [LoginPage.tsx](file:///d:/3rd%20uc/frontend/src/components/LoginPage.tsx#L10-L132).

---

## 5. Complete User Workflow

```
[ Step 1: User Opens Application ]
                │
                ▼
[ Step 2: Session Check ] ──(No Token)──► [ Step 3: Login Screen ]
                │                                     │
          (Valid Token)                               │ User enters credentials
                │                                     ▼
                │                          [ Step 4: POST /auth/login ]
                │                                     │
                ├─────────────────────────────────────┘
                ▼
[ Step 5: Dashboard Screen Loads ]
                │
                ├──► Automatically queries GET /devops/areas (Loads hierarchical tree)
                └──► Automatically queries GET /applications (Loads enterprise applications)
                │
                ▼
[ Step 6: Step 1 - User Selects Area / Part ]
                │ (e.g. User selects "Payments" under "Finance")
                ▼
[ Step 7: Frontend fetches GET /devops/areas/{id}/user-stories ]
                │ (Populates User Stories list; auto-selects first story, e.g. US-101)
                ▼
[ Step 8: Step 2 - User Selects User Story ]
                │ (e.g. "US-101: Fund Transfer & Multi-Factor Authorization")
                ▼
[ Step 9: Frontend fetches GET /devops/user-stories/{id}/acceptance-criteria ]
                │ (Populates AC checkboxes: AC-01, AC-02, AC-03, AC-04)
                ▼
[ Step 10: Step 3 - User Selects Acceptance Criteria ]
                │ (User toggles individual criteria or clicks "Select All")
                ▼
[ Step 11: Step 4 - User Configures Application Link ]
                │ (Default provided: "https://www.amazon.in/"; user can edit or add URLs)
                ▼
[ Step 12: Step 5 - User Clicks "Generate Test Cases" ]
                │
                ▼
[ Step 13: POST /generation/create sent to Backend ]
                │
                ├──► Backend fetches Story & Criteria details from DB
                ├──► Web Extractor safely accesses URL, scrapes forms, buttons, & fields
                ├──► Test Generator Engine parses numeric thresholds, timeouts, security rules
                ├──► Deduplication Service eliminates redundancy via SequenceMatcher
                └──► Backend returns Positive, Negative, & Edge test cases + Coverage Summary
                │
                ▼
[ Step 14: Results Rendered in Frontend ]
                │
                ├──► MetricCards displays Total, Positive, Negative, & Edge counts
                └──► TestCaseTable displays scenarios in tabs with expandable rows
                │
                ▼
[ Step 15: User Reviews & Interacts with Test Cases ]
                │
                ├──► Filter by Priority (High / Medium / Low)
                ├──► Expand row to view Preconditions, Test Data, Steps, Expected Outcome
                ├──► Click Edit to modify scenario, steps, or data in modal
                └──► Click Delete to remove unnecessary scenarios
                │
                ▼
[ Step 16: User Clicks "Download Excel" ]
                │
                ├──► Frontend sends POST /export/excel with current test cases
                ├──► Backend generates styled multi-sheet workbook (.xlsx) via openpyxl
                └──► Browser automatically triggers native file download
```

---

## 6. Screen-by-Screen Workflow

### Screen 1: Login Screen

* **Component File**: [LoginPage.tsx](file:///d:/3rd%20uc/frontend/src/components/LoginPage.tsx#L10-L132)
* **Purpose**: Authenticate the QA engineer using corporate credentials and issue a secure session bearer token.
* **UI Elements**:
  * **Email Input Field**: Pre-filled with `admin@enterprise.com` for convenience; allows typing.
  * **Password Input Field**: Pre-filled with `password123`; masked password input.
  * **"Sign In" Button**: Submits the authentication form.
  * **"Forgot Password" Button**: Displays an informational prompt directing the user to their QA administrator.
* **User Actions & Execution Flow**:
  1. User clicks **"Sign In"**.
  2. `handleSubmit(e)` executes in [LoginPage.tsx](file:///d:/3rd%20uc/frontend/src/components/LoginPage.tsx#L16-L35).
  3. Frontend validates non-empty email and password.
  4. Calls `loginUser(email, password)` in [api.ts](file:///d:/3rd%20uc/frontend/src/services/api.ts#L55-L75).
  5. Network request dispatched: `POST /api/v1/auth/login` with body `{ email: "admin@enterprise.com", password: "password123" }`.
  6. Backend endpoint [auth.py](file:///d:/3rd%20uc/backend/app/api/v1/endpoints/auth.py#L12-L34) runs:
     - Normalizes email and queries `User` table in `test_generator.db`.
     - Validates password hash using `verify_password()` in [security.py](file:///d:/3rd%20uc/backend/app/core/security.py#L16-L18).
     - Generates 64-character hex token via `create_access_token()`, saving it in memory with 24-hour expiration.
     - Returns `{ access_token, token_type: "bearer", user: { id, email, full_name, is_active } }`.
  7. Frontend receives response, stores token in `localStorage['auth_token']`, and calls `onLoginSuccess(user)`.
  8. In [App.tsx](file:///d:/3rd%20uc/frontend/src/App.tsx#L60-L64), `currentUser` state is updated, immediately transitioning the view to the Main Dashboard.
* **Error Handling**: If invalid credentials are provided, backend raises `HTTP 401 Unauthorized` with `"Invalid email or password. Please try again."`. [LoginPage.tsx](file:///d:/3rd%20uc/frontend/src/components/LoginPage.tsx#L55-L60) renders a red alert banner with the error text.
* **Loading State**: The "Sign In" button displays a rotating `Loader2` spinner and `"Signing In..."` text while disabling duplicate clicks.

---

### Screen 2: Navigation Header

* **Component File**: [Header.tsx](file:///d:/3rd%20uc/frontend/src/components/Header.tsx#L10-L96)
* **Purpose**: Fixed persistent top bar displaying application branding, active user identity, and session controls.
* **UI Elements**:
  * **Brand Logo & Title**: Displays the layered logo and "Test Case Generator" title.
  * **User Profile Pill**: Displays the user's initial (`A` for Admin) in an avatar circle with a chevron icon.
  * **Profile Dropdown Menu**:
    * **User Information**: Shows full name (`Enterprise Admin`) and email (`admin@enterprise.com`).
    * **Profile Option**: Shows an alert with user details when clicked.
    * **Logout Option**: Red button with log-out icon.
* **User Actions & Execution Flow**:
  1. User clicks the profile avatar -> toggles `isOpen` state displaying the dropdown menu.
  2. Clicking anywhere outside the dropdown triggers a document-level `mousedown` listener that automatically closes it.
  3. User clicks **"Logout"**.
  4. Triggers `onLogout()` in [App.tsx](file:///d:/3rd%20uc/frontend/src/App.tsx#L66-L71), calling `logoutUser()` in [api.ts](file:///d:/3rd%20uc/frontend/src/services/api.ts#L95-L106).
  5. Sends `POST /api/v1/auth/logout` with the Bearer token.
  6. Backend removes token from `ACTIVE_TOKENS` dictionary in [security.py](file:///d:/3rd%20uc/backend/app/core/security.py#L43-L46).
  7. Frontend removes `auth_token` from `localStorage`, sets `currentUser = null`, and resets all generation state, smoothly returning the user to the Login screen.

---

### Screen 3: Test Generation Configuration Form

* **Component Files**: [ApplicationForm.tsx](file:///d:/3rd%20uc/frontend/src/components/ApplicationForm.tsx#L50-L662) and [AreaSelector.tsx](file:///d:/3rd%20uc/frontend/src/components/AreaSelector.tsx#L21-L355)
* **Purpose**: The primary 5-step operational interface where the QA engineer selects functional project areas, user stories, acceptance criteria, and application URLs.

#### Step 1: Area / Service Selection (Hierarchical Tree)
* **Component**: [AreaSelector.tsx](file:///d:/3rd%20uc/frontend/src/components/AreaSelector.tsx)
* **Purpose**: Allows navigating and selecting functional project areas organized in an Azure DevOps-style directory hierarchy.
* **Data Source**: Fetched via `fetchAreas()` (`GET /api/v1/devops/areas`) on mount.
* **Interaction**:
  * Root and parent nodes (e.g. `Project`, `Finance`, `Healthcare`, `Sales`) have chevron toggle buttons to expand and collapse sub-branches.
  * Each item has a checkbox and title. Clicking any node (e.g., `Payments` or `Banking`) toggles its selection in `selectedAreaIds`.
  * Selected areas are rendered at the top as removable badge chips (e.g. `Finance / Payments [x]`).
  * A "Clear all" button deselects all areas in a single click.

#### Step 2: User Story Selection
* **Component**: Section 2 in [ApplicationForm.tsx](file:///d:/3rd%20uc/frontend/src/components/ApplicationForm.tsx#L349-L422)
* **Purpose**: Displays all User Stories belonging to the selected Area(s).
* **Data Source**: Automatically fetched via `fetchUserStoriesByAreas(selectedAreaIds)` (`GET /api/v1/devops/areas/multi/user-stories?area_ids=...`) when `selectedAreaIds` changes.
* **Interaction**:
  * Displays work item cards formatted with Azure DevOps monospace ID badges (e.g., `US-101`, `US-102`).
  * Clicking a story selects it in `selectedStoryId` and highlights it with a blue border and checkmark circle.
  * Defaults to auto-selecting the first available story upon loading.

#### Step 3: Acceptance Criteria Selection
* **Component**: Section 3 in [ApplicationForm.tsx](file:///d:/3rd%20uc/frontend/src/components/ApplicationForm.tsx#L425-L495)
* **Purpose**: Enables granular selection of specific functional criteria to test.
* **Data Source**: Automatically fetched via `fetchAcceptanceCriteriaByStory(selectedStoryId)` (`GET /api/v1/devops/user-stories/{id}/acceptance-criteria`) when `selectedStoryId` changes.
* **Interaction**:
  * Each criterion is rendered as an independent checkbox card with criteria ID (e.g. `[US-101-AC-01]`) and full functional rule text.
  * **"Select All" / "Deselect All" Button**: Located in the header; toggles all criteria at once.
  * Criteria are pre-selected by default to save QA engineers time.
  * Clicking any card toggles its ID in `selectedCriteriaIds`.

#### Step 4: Application Link Configuration
* **Component**: Section 4 in [ApplicationForm.tsx](file:///d:/3rd%20uc/frontend/src/components/ApplicationForm.tsx#L497-L639)
* **Purpose**: Connects the requirements to live web application interfaces for DOM context and form field extraction.
* **Default Value**: Pre-loaded with `Amazon India Storefront` (`https://www.amazon.in/`).
* **Interaction**:
  * **Inline Edit Button**: Clicking the pencil icon switches a link into edit mode with Link Name and URL input fields. Clicking "Save Changes" validates and updates the URL.
  * **Remove Button**: Clicking the `[X]` icon removes the link.
  * **"Add Custom Link"**: Two input fields (Link Name and URL) allowing the user to append additional application URLs (e.g. `Checkout Page`, `https://example.com/checkout`). Validates safe protocols (`http://` or `https://`) and rejects duplicates.

#### Step 5: "Generate Test Cases" Button
* **Button Code**: [ApplicationForm.tsx](file:///d:/3rd%20uc/frontend/src/components/ApplicationForm.tsx#L642-L658)
* **Function**: `handleSubmit(e)`
* **Validation Checks**:
  1. Verifies `selectedAreaIds.length > 0`. If empty, raises error: `"Please select an Area to continue."`.
  2. Verifies `selectedStoryId` is chosen. If empty, raises error: `"Please select a user story to continue."`.
  3. Verifies `selectedCriteriaIds.length > 0`. If empty, raises error: `"No acceptance criteria selected. Please select at least one acceptance criterion to continue."`.
* **API Dispatched**: `POST /api/v1/generation/create`
* **Loading State**: The button disables and displays `<Loader2 className="animate-spin" />` with text `"Generating Test Cases..."`.

---

### Screen 4: Summary Metrics Dashboard

* **Component File**: [MetricCards.tsx](file:///d:/3rd%20uc/frontend/src/components/MetricCards.tsx#L9-L84)
* **Purpose**: Displays visual coverage metrics and scenario distributions immediately after test cases are generated.
* **UI Elements**:
  * **Top Summary Banner**: Confirms the number of User Stories analyzed, Acceptance Criteria evaluated, and Application Pages inspected.
  * **Total Cases Card (Blue)**: Shows cumulative test cases across all categories.
  * **Positive Scenarios Card (Emerald)**: Shows count of normal/happy-path validation scenarios.
  * **Negative Scenarios Card (Amber)**: Shows count of boundary rejection, validation error, and security lockout scenarios.
  * **Edge Scenarios Card (Purple)**: Shows count of extreme boundary values, exact limits, and timeout scenarios.
* **Data Reactivity**: When a user deletes a scenario or adds changes in the table, the metrics dynamically update to match the active state.

---

### Screen 5: Tabbed Test Case Table

* **Component File**: [TestCaseTable.tsx](file:///d:/3rd%20uc/frontend/src/components/TestCaseTable.tsx#L26-L311)
* **Purpose**: Comprehensive tabular presentation of generated test cases with category tabs, priority filters, drawer inspection, scenario editing, row deletion, and Excel export.
* **UI Elements & Actions**:
  * **Category Tabs**:
    * **Positive Tab**: Emerald icon, displays positive test cases (e.g. `TC-POS-001`).
    * **Negative Tab**: Amber icon, displays negative test cases (e.g. `TC-NEG-001`).
    * **Edge Tab**: Purple icon, displays edge/boundary test cases (e.g. `TC-EDG-001`).
  * **Priority Filter Dropdown**: Filters active rows by `All Priorities`, `High Priority`, `Medium Priority`, or `Low Priority`.
  * **Table Headers**: Column `#` (expander), `Test Case ID`, `Ref`, `Priority`, `Test Scenario`, `Expected Result`, and `Actions`.
  * **Expandable Row Drawer**:
    * Clicking the chevron (`v` / `^`) on any row toggles an expanded detail view.
    * Displays: **Preconditions**, **Test Data** (in monospace font), **Application Page & URL**, **Step-by-Step Test Steps** (numbered list), and **Full Expected Outcome**.
  * **Row Actions**:
    * **Edit Button (Pencil Icon)**: Opens the [EditTestCaseModal.tsx](file:///d:/3rd%20uc/frontend/src/components/EditTestCaseModal.tsx) for that test case.
    * **Delete Button (Trash Icon)**: Calls `onDeleteTestCase(category, id)`, immediately removing the row from state and decrementing the metric cards.
  * **"Download Excel" Button**:
    * Calls `onExportExcel()` -> dispatches `POST /api/v1/export/excel`.
    * Streams back the binary `.xlsx` file and initiates browser download.

---

### Screen 6: Edit Test Case Modal

* **Component File**: [EditTestCaseModal.tsx](file:///d:/3rd%20uc/frontend/src/components/EditTestCaseModal.tsx#L11-L148)
* **Purpose**: Allows QA engineers to manually tailor, refine, or augment any generated test scenario directly in the browser.
* **Input Fields**:
  * **Priority**: Select dropdown (`High`, `Medium`, `Low`).
  * **Test Scenario**: Single-line text input for scenario title.
  * **Test Description**: Multi-line text input for objective.
  * **Preconditions**: Single-line text input for environment requirements.
  * **Test Data**: Text input for specific input variables or payloads.
  * **Test Steps**: Multi-line textarea where each line represents an individual step.
  * **Expected Result**: Multi-line text input for expected system behavior.
* **Actions**:
  * **Cancel Button / [X] Icon**: Closes the modal without applying changes.
  * **"Save Changes" Button**: Splits the steps textarea by newlines, updates the parent test case object in [App.tsx](file:///d:/3rd%20uc/frontend/src/App.tsx#L96-L104), and closes the modal. The updated scenario appears instantly in the table.

---

## 7. Frontend Architecture

### State Management & Data Flow
The frontend state is centralized in [App.tsx](file:///d:/3rd%20uc/frontend/src/App.tsx) and passed down via typed props:

```
                                App.tsx (Root State Orchestrator)
                                 ├── currentUser: User | null
                                 ├── positiveCases: TestCase[]
                                 ├── negativeCases: TestCase[]
                                 ├── edgeCases: TestCase[]
                                 ├── currentReqRef: string
                                 └── isLoading / isExporting
                                          │
            ┌─────────────────────────────┼─────────────────────────────┐
            ▼                             ▼                             ▼
       Header.tsx                ApplicationForm.tsx             MetricCards.tsx
  (User display & logout)    (Area & Story selection)       (Live count cards)
                                          │                             │
                                  AreaSelector.tsx                      ▼
                              (Tree expand/collapse)           TestCaseTable.tsx
                                                            (Tabs, Filters, Drawer)
                                                                        │
                                                              EditTestCaseModal.tsx
                                                              (In-place scenario edit)
```

### Type Definitions
All data structures are strongly typed in [types/index.ts](file:///d:/3rd%20uc/frontend/src/types/index.ts):
* `User`: `{ id: number, email: string, full_name: string, is_active: boolean }`
* `Area`: `{ id: number, name: string, code: string, description?: string, application_id?: number, parent_id?: number | null }`
* `UserStory`: `{ id: string, title: string, description?: string, state?: string, assigned_to?: string, area_id: number }`
* `AcceptanceCriteriaRead`: `{ id: string, user_story_id: string, criteria_number: number, text: string }`
* `TestCase`: `{ id: string, requirement_ref: string, user_story?: string, acceptance_criteria?: string, application_page?: string, application_link?: string, category: string, priority: string, scenario: string, description: string, preconditions: string, test_data: string, test_steps: string[], expected_result: string }`
* `TestCaseGenerationRequest`: `{ application_id: number, requirement_source: string, requirement_identifiers: string[], application_links: ApplicationLinkPayload[], area_ids?: number[], ... }`
* `TestCaseGenerationResponse`: `{ positive_test_cases: TestCase[], negative_test_cases: TestCase[], edge_test_cases: TestCase[], coverage_summary: CoverageSummary, analysis_summary: string, url_context_analyzed: boolean, url_analysis_message?: string }`

---

## 8. Backend Architecture

The backend is built around FastAPI, using clean separation of concerns:

```
                            HTTP Request (JSON / Headers)
                                          │
                                          ▼
                                  api/deps.py
                           (Bearer Token Validation)
                                          │
                                          ▼
                            api/v1/endpoints/*.py
                           (FastAPI Route Handlers)
                                          │
                         ┌────────────────┴────────────────┐
                         ▼                                 ▼
                  services/*.py                     models/*.py
            (Deterministic Logic Engines)      (SQLAlchemy Data Models)
                         │                                 │
                         ▼                                 ▼
                 External HTTP/DOM                 test_generator.db
             (httpx / BeautifulSoup4)             (SQLite Database)
```

### Backend Subsystems
1. **Core Security ([security.py](file:///d:/3rd%20uc/backend/app/core/security.py))**:
   - `hash_password()`: Generates SHA-256 HMAC strings using `SECRET_KEY`.
   - `verify_password()`: Performs constant-time comparison via `hmac.compare_digest()`.
   - `create_access_token()`: Generates 64-character random hex tokens via Python `secrets.token_hex(32)`.
   - `verify_token()`: Validates token presence and checks expiration timestamps.
2. **Dependency Injection ([deps.py](file:///d:/3rd%20uc/backend/app/api/deps.py))**:
   - `get_current_user()`: Validates incoming HTTP `Authorization: Bearer <token>` headers, querying the `users` table. Protects all API endpoints against unauthenticated access.
3. **Database Session ([session.py](file:///d:/3rd%20uc/backend/app/db/session.py))**:
   - Manages SQLite connection pooling with `check_same_thread=False`.
   - Provides `get_db()` generator yielding a clean SQLAlchemy session per request and closing it safely on completion.
4. **Services Layer ([services/](file:///d:/3rd%20uc/backend/app/services))**:
   - `devops_service`: Reads stories and criteria from SQLite database.
   - `web_extractor`: Safely accesses URLs with timeout protection, parses DOM elements without AI.
   - `test_generator`: Contains `RequirementRuleAnalyzer` which applies deterministic regular expression parsers for numerical thresholds, timeouts, attempt counters, and security rules.
   - `deduplication_service`: Consolidates duplicate scenarios using Python's standard `difflib.SequenceMatcher`.
   - `excel_exporter`: Produces formatted Microsoft Excel `.xlsx` spreadsheets using `openpyxl`.

---

## 9. API Endpoints

The complete REST API specification implemented in the project:

| Method | Endpoint | Frontend File | Frontend Function | Backend File | Backend Function | Request Input | Response Output |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/auth/login` | `LoginPage.tsx` | `loginUser()` | `endpoints/auth.py` | `login()` | `{ email, password }` | `{ access_token, token_type, user }` |
| `GET` | `/api/v1/auth/me` | `App.tsx` | `fetchCurrentUser()` | `endpoints/auth.py` | `get_me()` | Header: `Bearer <token>` | `UserRead` model `{ id, email, full_name, is_active }` |
| `POST` | `/api/v1/auth/logout` | `Header.tsx` | `logoutUser()` | `endpoints/auth.py` | `logout()` | Header: `Bearer <token>` | `{ status: "success", message: "Signed out successfully." }` |
| `GET` | `/api/v1/applications` | `ApplicationForm.tsx` | `fetchApplications()` | `endpoints/applications.py` | `get_applications()` | Header: `Bearer <token>` | `List[ApplicationRead]` with `available_links` |
| `GET` | `/api/v1/applications/{id}` | N/A (Utility) | N/A | `endpoints/applications.py` | `get_application()` | Path: `app_id`, Header: `Bearer` | `ApplicationRead` model |
| `GET` | `/api/v1/devops/areas` | `ApplicationForm.tsx` | `fetchAreas()` | `endpoints/devops.py` | `get_areas()` | Header: `Bearer <token>` | `List[AreaRead]` (id, name, code, parent_id, etc.) |
| `GET` | `/api/v1/devops/areas/multi/user-stories` | `ApplicationForm.tsx` | `fetchUserStoriesByAreas()` | `endpoints/devops.py` | `get_user_stories_by_multiple_areas()` | Query: `area_ids=1&area_ids=2` | `List[UserStoryRead]` (matching area or sub-areas) |
| `GET` | `/api/v1/devops/areas/{area_id}/user-stories` | `ApplicationForm.tsx` | `fetchUserStoriesByArea()` | `endpoints/devops.py` | `get_user_stories_by_area()` | Path: `area_id` | `List[UserStoryRead]` |
| `GET` | `/api/v1/devops/user-stories/{story_id}/acceptance-criteria` | `ApplicationForm.tsx` | `fetchAcceptanceCriteriaByStory()` | `endpoints/devops.py` | `get_acceptance_criteria_by_user_story()` | Path: `story_id` (e.g. `US-101`) | `List[AcceptanceCriteriaRead]` (id, number, text) |
| `GET` | `/api/v1/devops/work-items/{id}` | N/A (Service) | N/A | `endpoints/devops.py` | `get_work_item()` | Path: `work_item_id` | `DevOpsWorkItem` model |
| `GET` | `/api/v1/devops/acceptance-criteria` | N/A (Service) | `fetchAcceptanceCriteria()` | `endpoints/devops.py` | `get_acceptance_criteria()` | Header: `Bearer <token>` | `List[AcceptanceCriteriaItem]` |
| `GET` | `/api/v1/devops/search` | N/A (Service) | `searchWorkItems()` | `endpoints/devops.py` | `search_work_items()` | Query: `q=query_text` | `List[DevOpsWorkItem]` |
| `POST` | `/api/v1/generation/create` | `ApplicationForm.tsx` | `generateTestCases()` | `endpoints/generation.py` | `generate_test_cases()` | `TestCaseGenerationRequest` payload | `TestCaseGenerationResponse` (positive, negative, edge, summary) |
| `POST` | `/api/v1/export/excel` | `TestCaseTable.tsx` | `exportExcelWorkbook()` | `endpoints/export.py` | `export_excel()` | `ExportExcelRequest` payload | Binary OpenXML stream (`.xlsx` file attachment) |

---

## 10. Frontend → Backend Flow

Here is the exact step-by-step trace of how data travels across network boundaries:

```
[ User Action: Clicks "Generate Test Cases" in ApplicationForm.tsx ]
                               │
                               ▼
  1. Frontend Form Validation (Checks non-empty Area, Story, Criteria)
                               │
                               ▼
  2. Native fetch() client in services/api.ts
     - Injects: 'Authorization': 'Bearer 4a9f...'
     - Injects: 'Content-Type': 'application/json'
     - Serializes: JSON.stringify(payload)
                               │
                               ▼
  3. Dispatches HTTP POST to http://127.0.0.1:8000/api/v1/generation/create
                               │
                               ▼
  4. FastAPI Route Handler: endpoints/generation.py -> generate_test_cases()
     - Dependency: deps.py -> get_current_user verifies Bearer token against ACTIVE_TOKENS
     - Dependency: session.py -> get_db yields active SQLAlchemy Session
                               │
                               ▼
  5. Backend Processing Pipeline:
     a. Queries Application table for ID (name, business rules, user roles)
     b. Calls devops_service.get_work_item() querying UserStory and AcceptanceCriteria tables
     c. Calls web_extractor.extract_multi_context() with httpx + BeautifulSoup4
     d. Invokes test_generator_engine.generate_multi_requirement_test_suite()
        - RequirementRuleAnalyzer analyzes thresholds, timeouts, lockouts, rules
        - DeduplicationService consolidates duplicates with SequenceMatcher
        - Assigns sequential IDs: TC-POS-001, TC-NEG-001, TC-EDG-001
                               │
                               ▼
  6. Backend Serializes Response:
     - Returns TestCaseGenerationResponse JSON payload (HTTP 200 OK)
                               │
                               ▼
  7. Frontend Client Receives Response:
     - api.ts checks response.ok, parses response.json()
                               │
                               ▼
  8. React State Update in App.tsx:
     - setGenerationResult(result)
     - setPositiveCases(result.positive_test_cases)
     - setNegativeCases(result.negative_test_cases)
     - setEdgeCases(result.edge_test_cases)
                               │
                               ▼
  9. React Re-renders UI:
     - MetricCards renders counters
     - TestCaseTable renders populated tabs with interactive scenarios
```

---

## 11. Database Workflow

The database is an SQLite relational database stored in `test_generator.db`.

* **Configuration**: Defined in [config.py](file:///d:/3rd%20uc/backend/app/core/config.py#L16) as `sqlite:///./test_generator.db`.
* **Engine & Session**: Configured in [session.py](file:///d:/3rd%20uc/backend/app/db/session.py) with `create_engine` and `sessionmaker`.

### Database Schema Table

| Table Name | Model Class | File | Purpose | Important Columns & Types | Relationships | Used By |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `users` | `User` | [models/user.py](file:///d:/3rd%20uc/backend/app/models/user.py) | User accounts & credentials | `id` (INT PK), `email` (VARCHAR UNIQUE), `full_name` (VARCHAR), `hashed_password` (VARCHAR), `is_active` (BOOL) | None | [auth.py](file:///d:/3rd%20uc/backend/app/api/v1/endpoints/auth.py), [deps.py](file:///d:/3rd%20uc/backend/app/api/deps.py) |
| `applications` | `Application` | [models/application.py](file:///d:/3rd%20uc/backend/app/models/application.py) | Enterprise software catalog | `id` (INT PK), `name` (VARCHAR UNIQUE), `code` (VARCHAR UNIQUE), `domain` (VARCHAR), `default_url` (VARCHAR), `business_rules` (TEXT), `user_roles` (TEXT), `key_modules` (TEXT) | `areas` (1-to-many backref) | [applications.py](file:///d:/3rd%20uc/backend/app/api/v1/endpoints/applications.py), [generation.py](file:///d:/3rd%20uc/backend/app/api/v1/endpoints/generation.py) |
| `areas` | `Area` | [models/devops.py](file:///d:/3rd%20uc/backend/app/models/devops.py) | DevOps Area Paths / System Parts | `id` (INT PK), `name` (VARCHAR), `code` (VARCHAR UNIQUE), `description` (TEXT), `application_id` (INT FK -> `applications.id`), `parent_id` (INT FK -> `areas.id`) | `parent` / `children` (self-referential), `user_stories` (1-to-many) | [devops.py](file:///d:/3rd%20uc/backend/app/api/v1/endpoints/devops.py), [AreaSelector.tsx](file:///d:/3rd%20uc/frontend/src/components/AreaSelector.tsx) |
| `user_stories` | `UserStory` | [models/devops.py](file:///d:/3rd%20uc/backend/app/models/devops.py) | Functional requirements | `id` (VARCHAR PK e.g. `US-101`), `title` (VARCHAR), `description` (TEXT), `state` (VARCHAR), `assigned_to` (VARCHAR), `area_id` (INT FK -> `areas.id`) | `area` (many-to-1), `acceptance_criteria` (1-to-many cascade delete) | [devops.py](file:///d:/3rd%20uc/backend/app/api/v1/endpoints/devops.py), [devops_service.py](file:///d:/3rd%20uc/backend/app/services/devops_service.py) |
| `acceptance_criteria` | `AcceptanceCriteria` | [models/devops.py](file:///d:/3rd%20uc/backend/app/models/devops.py) | Numbered acceptance rules | `id` (VARCHAR PK e.g. `US-101-AC-01`), `user_story_id` (VARCHAR FK -> `user_stories.id`), `criteria_number` (INT), `text` (TEXT) | `user_story` (many-to-1) | [devops.py](file:///d:/3rd%20uc/backend/app/api/v1/endpoints/devops.py), [test_generator.py](file:///d:/3rd%20uc/backend/app/services/test_generator.py) |

### Complete Database Operation Trace: Fetching Stories for Selected Area

1. **User Action**: User clicks the `Payments` checkbox in the Area tree.
2. **Frontend Event**: `AreaSelector.tsx` notifies `ApplicationForm.tsx` of `selectedAreaIds = [3]`.
3. **API Dispatch**: `fetchUserStoriesByAreas([3])` calls `GET /api/v1/devops/areas/multi/user-stories?area_ids=3`.
4. **Backend Route**: [endpoints/devops.py](file:///d:/3rd%20uc/backend/app/api/v1/endpoints/devops.py#L25-L62) receives request.
5. **Database Queries**:
   - `db.query(Area).filter(Area.id == 3).first()` finds Area `Payments`.
   - Recursive helper `get_child_ids()` runs: `db.query(Area.id).filter(Area.parent_id == 3).all()` to collect all child area IDs.
   - Story query runs: `db.query(UserStory).filter(UserStory.area_id.in_(all_area_ids)).all()`.
6. **Data Serialization**: SQLAlchemy `UserStory` entities are transformed into Pydantic `UserStoryRead` schemas.
7. **Response**: FastAPI returns JSON array of stories (`US-101`, `US-102`, `US-103`).
8. **UI Rendering**: `ApplicationForm.tsx` renders story cards with IDs and titles.

---

## 12. Authentication Workflow

```
[ User submits Login Form ]
             │
             ▼
[ POST /api/v1/auth/login ]
             │
             ├──► endpoints/auth.py cleans email: payload.email.strip().lower()
             ├──► Queries db.query(User).filter(User.email == email_clean).first()
             │
   (User not found OR verify_password fails) ──► HTTP 401: "Invalid email or password."
             │
       (User valid)
             │
             ├──► Check user.is_active is True
             ├──► create_access_token(user.email):
             │    - Generates 64-char hex string: token = secrets.token_hex(32)
             │    - Stores: ACTIVE_TOKENS[token] = { "email": email, "expires_at": time.time() + 86400 }
             │
             ▼
[ Response: LoginResponse JSON ]
  { "access_token": "4a9f...", "token_type": "bearer", "user": { ... } }
             │
             ▼
[ Frontend api.ts stores token ]
  localStorage.setItem('auth_token', token)
             │
             ▼
[ Subsequent API Request, e.g. GET /api/v1/devops/areas ]
             │
             ├──► Injects header: 'Authorization': 'Bearer 4a9f...'
             │
             ▼
[ Backend Dependency: deps.py -> get_current_user ]
             │
             ├──► verify_token("4a9f..."):
             │    - Looks up ACTIVE_TOKENS["4a9f..."]
             │    - If not found or expired -> HTTP 401: "Your session has expired."
             │    - Returns email: "admin@enterprise.com"
             │
             ├──► Queries db.query(User).filter(User.email == email).first()
             │
             ▼
[ Route Handler executes with validated current_user ]
```

---

## 13. External API & Web Scraping Workflow

The project contains two external integration capabilities: Azure DevOps REST API and Non-AI Web DOM Scraping.

### 1. Azure DevOps Integration ([devops_service.py](file:///d:/3rd%20uc/backend/app/services/devops_service.py))
* **Configuration**: Set in `.env` or [config.py](file:///d:/3rd%20uc/backend/app/core/config.py):
  * `ADO_ORGANIZATION`: Organization name (e.g. `EnterpriseOrg`).
  * `ADO_PROJECT`: Project name (e.g. `QualityAssurance`).
  * `ADO_PAT`: Personal Access Token for authentication.
* **Authentication**: HTTP Basic Auth with Base64-encoded PAT (`Basic :<ADO_PAT>`).
* **Operational Modes**:
  1. **Primary Mode (Database & Mock)**: When `db` is supplied or `ADO_PAT` is unconfigured, queries the local SQLite `UserStory` and `AcceptanceCriteria` tables. If the ID matches standard enterprise IDs (`US-101` to `US-105`), returns the structured requirement immediately with zero network delay.
  2. **Live ADO Mode**: If `ADO_PAT` is configured and an unknown ID is requested, queries the Azure DevOps REST API endpoint:
     `GET https://dev.azure.com/{org}/{project}/_apis/wit/workitems/{id}?api-version=7.0`.
  3. **Intelligent Fallback Generator**: If Azure DevOps is offline or unreachable, generates a structured requirement fallback adhering to the `DevOpsWorkItem` schema.

### 2. Non-AI Web Context Extractor ([web_extractor.py](file:///d:/3rd%20uc/backend/app/services/web_extractor.py))
* **Technology**: `httpx` (async HTTP client) + `BeautifulSoup4` (HTML parser) + regular expressions.
* **Purpose**: Inspects live application links (such as the default `https://www.amazon.in/` or internal portals) to detect real form field names, input IDs, buttons, headings, and error banners so test cases accurately reflect the live user interface.
* **Execution Steps**:
  1. `normalize_url()` ensures standard HTTPS scheme and strips trailing slashes.
  2. `is_safe_url()` blocks dangerous protocols (`javascript:`, `data:`, `file:`, `vbscript:`).
  3. Dispatches async HTTP GET request with realistic browser User-Agent and a strict 6.0s timeout.
  4. Parses the returned HTML using BeautifulSoup:
     - Extracts `<title>`, `<h1>`, `<h2>` for page context.
     - Scans `<input>`, `<select>`, `<textarea>` tags for `id`, `name`, `placeholder`, and associated `<label>` elements.
     - Scans `<button>`, `<a>`, and `<input type="submit">` tags for button labels (e.g. `Sign In`, `Submit`, `Transfer`).
     - Detects error nodes (`class="error"` or `class="alert"`).
  5. **SPA Bundle Fallback**: If the page is a client-side Single Page Application (e.g. React/Vite where inputs are rendered via JavaScript bundles), scans `<script src="...">` files using regex for `placeholder:`, `testId:`, and `value:` properties.
  6. Returns structured metadata `{ page_title, detected_inputs, detailed_inputs, detected_actions, observed_errors }`.
  7. **Graceful Fallback**: If the URL is offline, times out, or blocked, the extractor marks `status: "failed"` and falls back to application business rules without interrupting test generation.

---

## 14. Business Logic: Deterministic Test Generation

The core business logic is located in [test_generator.py](file:///d:/3rd%20uc/backend/app/services/test_generator.py). It operates entirely on **deterministic rule analysis** rather than artificial intelligence.

```
       Requirement Text (Acceptance Criteria / Business Rule)
                                 │
                                 ▼
                     RequirementRuleAnalyzer
                                 │
         ┌───────────────────────┼───────────────────────┐
         ▼                       ▼                       ▼
     Pattern 1               Pattern 2               Pattern 3
  Numerical / Currency       Temporal / Timeouts      Status / Security
   Limit Thresholds           Inactivity Rules         Attempt Counters
  (e.g. $10,000, 20%)      (e.g. 15 min, past date)    (e.g. 3 failed OTP)
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                                 ▼
     Generates ScenarioTemplate Objects for Category:
         ├── Positive  (Compliant value, authorized role, valid submission)
         ├── Negative  (Exceeded limit, expired time, 3 failed attempts)
         └── Edge      (Exact boundary value, delta increment, last attempt)
                                 │
                                 ▼
     Integrates Verified Web DOM Fields (from web_extractor)
                                 │
                                 ▼
     Synthesizes Multi-Page End-to-End Workflow Cases
                                 │
                                 ▼
     DeduplicationService (SequenceMatcher Similarity Filter)
                                 │
                                 ▼
     Re-indexes Sequential IDs (TC-POS-001, TC-NEG-001, TC-EDG-001)
```

### Deterministic Rule Patterns

#### Pattern 1: Numerical, Currency, and Limit Thresholds
* **Regex Trigger**: Detects patterns like `over $10,000`, `exceeding $5,000`, `longer than 5 days`, `discount override is 20%`, `risk score > 75`.
* **Mathematical Boundary Evaluation**:
  - `val_at_limit`: The exact threshold (e.g. `$10,000` or `5 days`).
  - `val_compliant`: 50% of the threshold (e.g. `$5,000`).
  - `val_just_above`: Smallest increment over threshold (`threshold + $0.01` or `threshold + 1 day`).
  - `val_exceeded`: 150% of threshold (e.g. `$15,000`).
* **Synthesized Scenarios**:
  - **Positive**: Valid submission within standard limit without triggering secondary reviews.
  - **Negative**: Submission exceeding limit without required authorization is blocked.
  - **Edge 1**: Exact boundary value ($10,000.00) processed without triggering above-threshold penalty.
  - **Edge 2**: Smallest incremental breach ($10,000.01) immediately triggers secondary authorization.

#### Pattern 2: Temporal, Expiration, and Timeout Rules
* **Regex Trigger**: Detects `times out after 15 minutes`, `link expires after 15 minutes`, `effective date in past`.
* **Synthesized Scenarios**:
  - **Positive**: Activity performed within active timeframe succeeds.
  - **Negative**: Inactivity exceeding timeframe invalidates session and redirects to login.
  - **Edge**: User action dispatched 1 second prior to timeout cutoff resets timer.

#### Pattern 3: Security & Consecutive Attempt Counters
* **Regex Trigger**: Detects `invalid OTP entered 3 consecutive times`, `password reset link`.
* **Boundary Evaluation**: Reads the count `N` (default 3).
* **Synthesized Scenarios**:
  - **Positive**: Valid credential on Attempt 1 authorizes user immediately.
  - **Negative**: `N` consecutive invalid attempts locks account for 15 minutes.
  - **Edge**: `N-1` invalid attempts followed by valid entry on final attempt succeeds and resets failure count.

#### Deduplication Engine ([deduplication_service.py](file:///d:/3rd%20uc/backend/app/services/deduplication_service.py))
Uses `difflib.SequenceMatcher` to compute similarity ratios across scenario titles, descriptions, test data, and expected results:
- Preserves distinct boundary values (e.g. `$10,000` vs `$10,000.01` are never treated as duplicates).
- Eliminates identical duplicate scenarios generated from overlapping rules.
- Re-indexes remaining test cases sequentially.

---

## 15. File-by-File Responsibilities

| File | Layer | Responsibility | Important Functions / Classes | Called By | Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| [backend/run.py](file:///d:/3rd%20uc/backend/run.py) | Backend Launcher | Starts Uvicorn ASGI server on `127.0.0.1:8000` | Entrypoint `__main__` | User terminal command | `uvicorn.run()` |
| [backend/app/main.py](file:///d:/3rd%20uc/backend/app/main.py) | Backend Core | Initializes FastAPI app, lifespan, CORS, and registers API routers | `lifespan()`, `root()` | `run.py` | `init_db()`, `CORSMiddleware`, `api_router` |
| [backend/app/core/config.py](file:///d:/3rd%20uc/backend/app/core/config.py) | Configuration | Loads environment variables & application settings | `Settings` | `main.py`, `session.py`, `devops_service.py` | `os.getenv()`, `dotenv.load_dotenv()` |
| [backend/app/core/security.py](file:///d:/3rd%20uc/backend/app/core/security.py) | Security | HMAC SHA-256 password hashing & token store | `hash_password()`, `verify_password()`, `create_access_token()`, `verify_token()`, `revoke_token()` | `auth.py`, `deps.py`, `init_db.py` | `hmac`, `hashlib`, `secrets`, `time` |
| [backend/app/db/session.py](file:///d:/3rd%20uc/backend/app/db/session.py) | Database Setup | Creates SQLite database engine and session factory | `get_db()`, `SessionLocal`, `Base` | `init_db.py`, `deps.py`, endpoints | `sqlalchemy.create_engine()`, `sessionmaker()` |
| [backend/app/db/init_db.py](file:///d:/3rd%20uc/backend/app/db/init_db.py) | DB Initialization | Creates database schema and populates seed data | `init_db()` | `main.py` lifespan | `Base.metadata.create_all()`, `SessionLocal` |
| [backend/app/models/user.py](file:///d:/3rd%20uc/backend/app/models/user.py) | DB Model | SQLAlchemy model for `users` table | `User` | `init_db.py`, `auth.py`, `deps.py` | `Base`, `Column`, `Integer`, `String` |
| [backend/app/models/application.py](file:///d:/3rd%20uc/backend/app/models/application.py) | DB Model | SQLAlchemy model for `applications` table | `Application` | `init_db.py`, `applications.py`, `generation.py` | `Base`, `Column`, `Text` |
| [backend/app/models/devops.py](file:///d:/3rd%20uc/backend/app/models/devops.py) | DB Model | Models for `areas`, `user_stories`, `acceptance_criteria` | `Area`, `UserStory`, `AcceptanceCriteria` | `init_db.py`, `devops.py`, `generation.py` | `Base`, `relationship`, `ForeignKey` |
| [backend/app/schemas/user.py](file:///d:/3rd%20uc/backend/app/schemas/user.py) | Pydantic Schema | DTOs for user login and profile | `LoginRequest`, `LoginResponse`, `UserRead` | `auth.py` | `pydantic.BaseModel` |
| [backend/app/schemas/application.py](file:///d:/3rd%20uc/backend/app/schemas/application.py) | Pydantic Schema | DTOs for enterprise applications | `ApplicationBase`, `ApplicationRead` | `applications.py` | `pydantic.BaseModel` |
| [backend/app/schemas/devops.py](file:///d:/3rd%20uc/backend/app/schemas/devops.py) | Pydantic Schema | DTOs for areas, user stories, acceptance criteria | `AreaRead`, `UserStoryRead`, `AcceptanceCriteriaRead`, `DevOpsWorkItem` | `devops.py`, `devops_service.py` | `pydantic.BaseModel`, `ConfigDict` |
| [backend/app/schemas/test_case.py](file:///d:/3rd%20uc/backend/app/schemas/test_case.py) | Pydantic Schema | DTOs for test generation, coverage, and export | `TestCase`, `TestCaseGenerationRequest`, `TestCaseGenerationResponse`, `CoverageSummary`, `ExportExcelRequest` | `generation.py`, `export.py`, services | `pydantic.BaseModel`, `Field` |
| [backend/app/api/deps.py](file:///d:/3rd%20uc/backend/app/api/deps.py) | Auth Dependency | Validates incoming Bearer tokens across protected routes | `get_current_user()` | All endpoint routers | `verify_token()`, `get_db()`, `HTTPBearer` |
| [backend/app/api/v1/api.py](file:///d:/3rd%20uc/backend/app/api/v1/api.py) | API Aggregator | Combines individual endpoint routers into `api_router` | `api_router` | `main.py` | `APIRouter.include_router()` |
| [backend/app/api/v1/endpoints/auth.py](file:///d:/3rd%20uc/backend/app/api/v1/endpoints/auth.py) | HTTP Endpoint | Authentication routes (`/login`, `/me`, `/logout`) | `login()`, `get_me()`, `logout()` | `api.py` router | `verify_password()`, `create_access_token()`, `revoke_token()` |
| [backend/app/api/v1/endpoints/applications.py](file:///d:/3rd%20uc/backend/app/api/v1/endpoints/applications.py) | HTTP Endpoint | Application catalog routes (`/applications`) | `get_applications()`, `get_application()`, `build_available_links()` | `api.py` router | `db.query(Application)` |
| [backend/app/api/v1/endpoints/devops.py](file:///d:/3rd%20uc/backend/app/api/v1/endpoints/devops.py) | HTTP Endpoint | Azure DevOps areas, stories, & criteria routes | `get_areas()`, `get_user_stories_by_area()`, `get_user_stories_by_multiple_areas()`, `get_acceptance_criteria_by_user_story()` | `api.py` router | `db.query(Area)`, `db.query(UserStory)`, `db.query(AcceptanceCriteria)` |
| [backend/app/api/v1/endpoints/generation.py](file:///d:/3rd%20uc/backend/app/api/v1/endpoints/generation.py) | HTTP Endpoint | Core test case generation route (`/generation/create`) | `generate_test_cases()` | `api.py` router | `devops_service`, `web_extractor`, `test_generator_engine` |
| [backend/app/api/v1/endpoints/export.py](file:///d:/3rd%20uc/backend/app/api/v1/endpoints/export.py) | HTTP Endpoint | Excel workbook download route (`/export/excel`) | `export_excel()` | `api.py` router | `excel_exporter.generate_workbook()` |
| [backend/app/services/devops_service.py](file:///d:/3rd%20uc/backend/app/services/devops_service.py) | Service | Database work item fetcher with live ADO fallback | `AzureDevOpsService.get_work_item()`, `get_acceptance_criteria_list()` | `devops.py`, `generation.py` | `httpx.AsyncClient`, `db.query()` |
| [backend/app/services/web_extractor.py](file:///d:/3rd%20uc/backend/app/services/web_extractor.py) | Service | Non-AI HTML DOM and form input scraper | `WebContextExtractor.extract_single_url_context()`, `extract_multi_context()`, `normalize_url()`, `is_safe_url()` | `generation.py` | `httpx.AsyncClient`, `BeautifulSoup` |
| [backend/app/services/combination_engine.py](file:///d:/3rd%20uc/backend/app/services/combination_engine.py) | Service | Orthogonal pairwise parameter combinations | `CombinationEngine.derive_combinations()` | `test_generator.py` | `itertools.product` |
| [backend/app/services/deduplication_service.py](file:///d:/3rd%20uc/backend/app/services/deduplication_service.py) | Service | Redundant test scenario deduplication | `DeduplicationService.deduplicate()`, `_similarity_ratio()` | `test_generator.py` | `difflib.SequenceMatcher` |
| [backend/app/services/quality_validator.py](file:///d:/3rd%20uc/backend/app/services/quality_validator.py) | Service | Test suite coverage auditing | `QualityValidator.validate_and_summarize()` | `test_generator.py` | `CoverageSummary` |
| [backend/app/services/test_generator.py](file:///d:/3rd%20uc/backend/app/services/test_generator.py) | Service | Deterministic rule analyzer & test synthesizer | `RequirementRuleAnalyzer.analyze_requirement()`, `TestGeneratorEngine.generate_multi_requirement_test_suite()` | `generation.py` | `deduplication_service`, `combination_engine` |
| [backend/app/services/excel_exporter.py](file:///d:/3rd%20uc/backend/app/services/excel_exporter.py) | Service | Multi-sheet styled Microsoft Excel workbook builder | `ExcelExporterService.generate_workbook()`, `_clean_str()` | `export.py` | `openpyxl.Workbook`, `PatternFill`, `Font`, `Border` |
| [frontend/package.json](file:///d:/3rd%20uc/frontend/package.json) | Frontend Config | Project manifest, dependencies, and build scripts | N/A | Node.js / Vite | `vite`, `react`, `tailwindcss`, `lucide-react` |
| [frontend/vite.config.ts](file:///d:/3rd%20uc/frontend/vite.config.ts) | Frontend Config | Vite development server and `/api` reverse proxy | Default export | Vite runtime | `@vitejs/plugin-react`, `@tailwindcss/vite` |
| [frontend/index.html](file:///d:/3rd%20uc/frontend/index.html) | HTML Template | Entrypoint HTML page mounting `#root` | N/A | Browser | `/src/main.tsx` |
| [frontend/src/main.tsx](file:///d:/3rd%20uc/frontend/src/main.tsx) | Frontend Entry | React DOM client initialization | Entrypoint | Vite | `createRoot()`, `<App />`, `index.css` |
| [frontend/src/index.css](file:///d:/3rd%20uc/frontend/src/index.css) | Stylesheet | Tailwind CSS imports & dark enterprise theme base styles | CSS rules | `main.tsx` | `@import "tailwindcss"` |
| [frontend/src/types/index.ts](file:///d:/3rd%20uc/frontend/src/types/index.ts) | Types | TypeScript interface definitions for entire frontend | `User`, `TestCase`, `Area`, `UserStory`, `CoverageSummary` | All frontend files | TypeScript compiler |
| [frontend/src/services/api.ts](file:///d:/3rd%20uc/frontend/src/services/api.ts) | API Client | REST client functions communicating with FastAPI | `loginUser()`, `fetchCurrentUser()`, `logoutUser()`, `fetchAreas()`, `fetchUserStoriesByAreas()`, `fetchAcceptanceCriteriaByStory()`, `generateTestCases()`, `exportExcelWorkbook()` | `App.tsx`, `LoginPage.tsx`, `ApplicationForm.tsx`, `TestCaseTable.tsx` | Native `fetch()`, `localStorage`, `Blob` |
| [frontend/src/App.tsx](file:///d:/3rd%20uc/frontend/src/App.tsx) | Component | Top-level state orchestrator & dashboard view manager | `App()`, `handleLoginSuccess()`, `handleLogout()`, `handleGenerate()`, `handleUpdateTestCase()`, `handleDeleteTestCase()`, `handleExportExcel()` | `main.tsx` | All frontend components & `api.ts` |
| [frontend/src/components/LoginPage.tsx](file:///d:/3rd%20uc/frontend/src/components/LoginPage.tsx) | Component | User login interface with email and password fields | `LoginPage()`, `handleSubmit()` | `App.tsx` | `loginUser()` from `api.ts` |
| [frontend/src/components/Header.tsx](file:///d:/3rd%20uc/frontend/src/components/Header.tsx) | Component | Fixed top bar with user profile dropdown & logout | `Header()` | `App.tsx` | `lucide-react` icons |
| [frontend/src/components/AreaSelector.tsx](file:///d:/3rd%20uc/frontend/src/components/AreaSelector.tsx) | Component | Azure DevOps hierarchical tree selector for Areas | `AreaSelector()`, `buildNodes()`, `getAreaPath()` | `ApplicationForm.tsx` | `lucide-react` icons |
| [frontend/src/components/ApplicationForm.tsx](file:///d:/3rd%20uc/frontend/src/components/ApplicationForm.tsx) | Component | 5-step form (Areas, Stories, Criteria, Links, Submit) | `ApplicationForm()`, `handleSubmit()`, `handleAddCustomLink()`, `handleSaveEditLink()` | `App.tsx` | `AreaSelector`, `api.ts` functions |
| [frontend/src/components/MetricCards.tsx](file:///d:/3rd%20uc/frontend/src/components/MetricCards.tsx) | Component | Coverage summary banner and 4 count cards | `MetricCards()` | `App.tsx` | `lucide-react` icons |
| [frontend/src/components/TestCaseTable.tsx](file:///d:/3rd%20uc/frontend/src/components/TestCaseTable.tsx) | Component | Tabbed table with priority filters, drawers, and export | `TestCaseTable()`, `getActiveList()`, `toggleRowExpanded()` | `App.tsx` | `EditTestCaseModal`, `lucide-react` |
| [frontend/src/components/EditTestCaseModal.tsx](file:///d:/3rd%20uc/frontend/src/components/EditTestCaseModal.tsx) | Component | In-place modal scenario and steps editor | `EditTestCaseModal()`, `handleSave()` | `TestCaseTable.tsx` | `lucide-react` icons |

---

## 16. Important Functions

### 1. `generate_multi_requirement_test_suite()`
* **File**: [backend/app/services/test_generator.py](file:///d:/3rd%20uc/backend/app/services/test_generator.py#L723-L1011)
* **Purpose**: Synthesizes Positive, Negative, and Edge test cases for multiple User Stories, Acceptance Criteria, and Application URLs.
* **Called When**: Triggered by `POST /api/v1/generation/create`.
* **Input**:
  * `app`: `Application` SQLAlchemy model.
  * `stories`: `List[DevOpsWorkItem]`.
  * `selected_ac_filter`: Optional list of criteria IDs selected by user.
  * `page_contexts`: List of extracted DOM dictionaries from `web_extractor`.
* **Processing**:
  1. Inspects `page_contexts` to extract verified input field names and action button labels.
  2. Iterates through each User Story and its acceptance criteria lines.
  3. Filters criteria matching `selected_ac_filter` using `RequirementRuleAnalyzer.matches_ac_filter()`.
  4. Calls `RequirementRuleAnalyzer.analyze_requirement()` to parse business logic patterns.
  5. Injects verified DOM fields into test steps when live page access succeeded.
  6. Evaluates application-level `business_rules` into additional scenario templates.
  7. Consolidates redundant test cases using `deduplication_service.deduplicate()`.
  8. Re-indexes unique IDs (`TC-POS-001`, `TC-NEG-001`, `TC-EDG-001`).
  9. Calculates coverage statistics and returns `TestCaseGenerationResponse`.
* **Output**: `TestCaseGenerationResponse` containing lists of Positive, Negative, and Edge test cases and summary metrics.
* **Used By**: [endpoints/generation.py](file:///d:/3rd%20uc/backend/app/api/v1/endpoints/generation.py#L113-L121).

### 2. `analyze_requirement()`
* **File**: [backend/app/services/test_generator.py](file:///d:/3rd%20uc/backend/app/services/test_generator.py#L90-L718)
* **Purpose**: Evaluates requirement text against deterministic regex patterns and extracts exact mathematical boundaries.
* **Input**: `text` (rule text), `ref_code`, `story_id`, `page_name`, `page_url`, `action_btn`, `field_1`, `field_2`, `roles`, `is_verified`.
* **Processing**:
  1. Executes regex for numerical/currency limits (`curr_m`, `unit_m`).
  2. Executes regex for temporal/timeout constraints (`time_m`, `past_date_m`).
  3. Executes regex for authentication/lockout counters (`otp`, `lockout`, `consecutive`).
  4. Formulates `ScenarioTemplate` objects with distinct preconditions, inputs, steps, and expected results.
* **Output**: `List[ScenarioTemplate]`.
* **Used By**: `TestGeneratorEngine.generate_multi_requirement_test_suite()`.

### 3. `extract_multi_context()`
* **File**: [backend/app/services/web_extractor.py](file:///d:/3rd%20uc/backend/app/services/web_extractor.py#L216-L273)
* **Purpose**: Safely scrapes and parses HTML from multiple application links without AI.
* **Input**: `links: Optional[List[ApplicationLinkPayload]]`.
* **Processing**:
  1. Deduplicates links by normalized URL and validates safe protocols.
  2. For each URL, dispatches an async HTTP GET request using `httpx.AsyncClient` with a 6.0s timeout.
  3. Parses HTML using `BeautifulSoup`, extracting inputs, buttons, and titles.
  4. If few inputs are detected, runs regex parsing against client-side JavaScript bundles to extract React/Vite input placeholders.
  5. Returns a summary status and list of page context dictionaries.
* **Output**: `Tuple[bool, str, List[Dict[str, Any]]]`.
* **Used By**: [endpoints/generation.py](file:///d:/3rd%20uc/backend/app/api/v1/endpoints/generation.py#L110).

### 4. `generate_workbook()`
* **File**: [backend/app/services/excel_exporter.py](file:///d:/3rd%20uc/backend/app/services/excel_exporter.py#L19-L198)
* **Purpose**: Builds a styled Microsoft Excel workbook with 3 tabs ("Positive", "Negative", "Edge").
* **Input**: `positive_cases`, `negative_cases`, `edge_cases`, `app_name`, `req_ref`.
* **Processing**:
  1. Creates an `openpyxl.Workbook()` and removes the default sheet.
  2. Iterates over `sheets_data`: creates sheet, writes 13 dark navy header cells (`#1E293B`) with white bold text.
  3. Writes data rows, applying wrapped text formatting and row height calculations.
  4. Styles Priority column (High: light red `#FEE2E2`, Medium: light yellow `#FEF3C7`, Low: light blue `#E0F2FE`).
  5. Enables column auto-filters (`ws.auto_filter.ref`) and freezes top row (`A2`).
  6. Configures column widths (from 12 to 45 characters).
  7. Saves workbook into an in-memory `io.BytesIO` buffer.
* **Output**: `io.BytesIO` stream.
* **Used By**: [endpoints/export.py](file:///d:/3rd%20uc/backend/app/api/v1/endpoints/export.py#L16-L22).

### 5. `loginUser()`
* **File**: [frontend/src/services/api.ts](file:///d:/3rd%20uc/frontend/src/services/api.ts#L55-L75)
* **Purpose**: Sends login credentials to the backend and saves the returned Bearer token.
* **Input**: `email: string`, `password: string`.
* **Processing**: Dispatches `POST /api/v1/auth/login`. On HTTP 200, extracts `access_token` and calls `setAuthToken(token)` to store it in `localStorage`.
* **Output**: `Promise<LoginResponse>`.
* **Used By**: [LoginPage.tsx](file:///d:/3rd%20uc/frontend/src/components/LoginPage.tsx#L28).

---

## 17. Dependency / Call Flow

### Feature 1: User Login
```
LoginPage.tsx (handleSubmit)
       │
       ▼
services/api.ts (loginUser)
       │
       ▼  POST /api/v1/auth/login
endpoints/auth.py (login)
       │
       ├──► db/session.py (get_db -> SQLAlchemy Session)
       ├──► models/user.py (db.query(User).filter(User.email == email))
       └──► core/security.py (verify_password, create_access_token)
```

### Feature 2: Hierarchical Area & Story Loading
```
ApplicationForm.tsx (useEffect)
       │
       ├──► services/api.ts (fetchAreas)
       │          │
       │          ▼  GET /api/v1/devops/areas
       │    endpoints/devops.py (get_areas)
       │          └──► models/devops.py (db.query(Area))
       │
       └──► AreaSelector.tsx (User toggles area node)
                  │
                  ▼
            ApplicationForm.tsx (selectedAreaIds updated)
                  │
                  ▼
            services/api.ts (fetchUserStoriesByAreas)
                  │
                  ▼  GET /api/v1/devops/areas/multi/user-stories
            endpoints/devops.py (get_user_stories_by_multiple_areas)
                  ├──► models/devops.py (db.query(UserStory))
                  └──► models/devops.py (db.query(Area) recursive get_child_ids)
```

### Feature 3: Test Case Generation
```
ApplicationForm.tsx (handleSubmit)
       │
       ▼
App.tsx (handleGenerate)
       │
       ▼
services/api.ts (generateTestCases)
       │
       ▼  POST /api/v1/generation/create
endpoints/generation.py (generate_test_cases)
       │
       ├──► api/deps.py (get_current_user -> verifies Bearer token)
       ├──► models/application.py (db.query(Application).filter(...))
       ├──► services/devops_service.py (get_work_item -> queries UserStory & Criteria)
       ├──► services/web_extractor.py (extract_multi_context -> httpx + BeautifulSoup4)
       └──► services/test_generator.py (generate_multi_requirement_test_suite)
                  │
                  ├──► RequirementRuleAnalyzer.analyze_requirement (Threshold & rule regex)
                  ├──► services/combination_engine.py (derive_combinations)
                  └──► services/deduplication_service.py (deduplicate via SequenceMatcher)
```

### Feature 4: Excel Export
```
TestCaseTable.tsx (Download Excel button click)
       │
       ▼
App.tsx (handleExportExcel)
       │
       ▼
services/api.ts (exportExcelWorkbook)
       │
       ▼  POST /api/v1/export/excel
endpoints/export.py (export_excel)
       │
       ├──► services/excel_exporter.py (generate_workbook via openpyxl)
       │          └──► Writes sheets, headers, styles, auto-filters, column widths
       │
       ▼  Binary Stream (.xlsx)
services/api.ts
       │
       ├──► Creates Blob from arrayBuffer
       ├──► Creates virtual <a download="Test_Suite_US_101.xlsx">
       └──► Triggers native browser download & cleans up URL
```

---

## 18. Error Handling

1. **Authentication Errors (401)**:
   - Handled in `api/deps.py`: If token is missing, expired, or user not found, raises `HTTP 401 Unauthorized`.
   - Frontend interceptor in `services/api.ts` (`handleResponseStatus`): Detects `status === 401`, clears token from `localStorage`, and triggers `sessionExpiredHandler()` in `App.tsx`, resetting the UI to the login screen with an explanatory message.
2. **Form Validation Errors**:
   - `ApplicationForm.tsx` performs pre-submission checks: Ensures an Area is selected, a User Story is active, and at least one Acceptance Criterion checkbox is checked. If invalid, displays a highlighted red banner preventing network calls.
3. **Invalid Application Links & URL Schemes**:
   - Handled in `web_extractor.py` and `ApplicationForm.tsx`: Blocks `javascript:`, `data:`, `file:`, etc.
   - Enforces valid HTTP/HTTPS URLs.
   - If an external application URL times out or returns HTTP 404/500, `web_extractor.py` catches the exception and returns a failed status; test generation continues using application specification and database business rules.
4. **Empty Data States**:
   - If an Area has no User Stories, `ApplicationForm.tsx` displays: `"Please select an Area to view available User Stories."`.
   - If a User Story has no criteria, displays: `"Please select a User Story to view its Acceptance Criteria."`.
   - If a table category has zero test cases, `TestCaseTable.tsx` displays: `"No matching test cases found for the selected filters."`.
5. **Network / Server Outages**:
   - In `services/api.ts`, all `fetch()` calls are wrapped in `try/catch` blocks that throw user-friendly error messages (e.g. `"Unable to connect to authentication server. Please try again."`).

---

## 19. Complete Example Workflow

### Scenario: Testing Online Banking Fund Transfers (`US-101`)

1. **User Sign In**:
   - User opens browser at `http://localhost:5173`.
   - Enters `admin@enterprise.com` and `password123`.
   - Clicks **"Sign In"**. Frontend receives Bearer token and mounts the dashboard.
2. **Area Selection**:
   - Under Step 1, the user expands `Finance` and selects `Payments` (`AREA-BANK-PAYMENTS`).
   - Frontend calls `GET /api/v1/devops/areas/multi/user-stories?area_ids=3`.
3. **Story Selection**:
   - Under Step 2, User Stories for Payments appear.
   - User clicks **`US-101: Fund Transfer & Multi-Factor Authorization`**.
   - Frontend calls `GET /api/v1/devops/user-stories/US-101/acceptance-criteria`.
4. **Acceptance Criteria Selection**:
   - Under Step 3, criteria load:
     - `[US-101-AC-01] Given user is logged into online banking, source account list shows active accounts only.`
     - `[US-101-AC-02] Given transfer amount exceeding $10,000, OTP verification screen is presented.`
     - `[US-101-AC-03] Given invalid OTP entered 3 consecutive times, transaction is blocked and account locked.`
     - `[US-101-AC-04] Given successful transfer, system debits source account immediately and issues receipt.`
   - All 4 checkboxes are selected.
5. **Application Link**:
   - Step 4 shows default link `https://www.amazon.in/` (or banking portal URL).
6. **Test Generation**:
   - User clicks **"Generate Test Cases"**.
   - Backend analyzes the criteria:
     - Detects currency threshold `$10,000` from AC-02.
     - Detects security counter `3 consecutive` attempts from AC-03.
     - Evaluates active banking business rules (transfers over $10,000 require secondary approval; daily limit $50,000).
   - Generates 15 comprehensive scenarios:
     - **Positive**: Compliant transfer of $5,000; valid OTP entry on first attempt; transfer within $50,000 daily limit.
     - **Negative**: Transfer exceeding $10,000 without OTP; 3 consecutive invalid OTP attempts causing 15-minute account lockout; transfer exceeding daily limit of $50,000.
     - **Edge**: Exact boundary transfer of $10,000.00; increment breach of $10,000.01; valid OTP on attempt #3 after 2 failed attempts.
7. **Inspection & Modification**:
   - MetricCards displays: Total: `15`, Positive: `6`, Negative: `4`, Edge: `5`.
   - User switches between **Positive**, **Negative**, and **Edge** tabs.
   - User expands row `TC-NEG-002` to inspect Preconditions, Steps, and Expected Outcome.
   - User clicks the **Edit** icon, modifies the description, and clicks "Save Changes".
8. **Export**:
   - User clicks **"Download Excel"**.
   - Receives formatted workbook `Test_Suite_US-101.xlsx` containing all 15 scenarios organized into styled Positive, Negative, and Edge worksheets.

---

## 20. Final Architecture Diagram

```
+-------------------------------------------------------------------------------+
|                                     USER                                      |
+---------------------------------------+---------------------------------------+
                                        │ (Clicks, Form Inputs, Toggles)
                                        ▼
+-------------------------------------------------------------------------------+
|                             FRONTEND UI LAYER                                 |
|                       (React 18, TypeScript, Tailwind)                        |
|                                                                               |
|   LoginPage  ──►  Header  ──►  AreaSelector  ──►  ApplicationForm             |
|                                                          │                    |
|   TestCaseTable  ◄──  EditModal  ◄──  MetricCards  ◄─────┘                    |
+---------------------------------------+---------------------------------------+
                                        │ (Async fetch with Bearer Token)
                                        ▼
+-------------------------------------------------------------------------------+
|                             API GATEWAY & ROUTING                             |
|                        (FastAPI v1 RESTful Endpoints)                         |
|                                                                               |
|   /auth/*  ──►  /applications/*  ──►  /devops/*  ──►  /generation/create      |
|                                                          │                    |
|                                           /export/excel ◄┘                    |
+---------------------------------------+---------------------------------------+
                                        │
                         ┌──────────────┴──────────────┐
                         ▼                             ▼
+---------------------------------+   +-----------------------------------------+
|        DATABASE LAYER           |   |            SERVICES LAYER               |
|      (SQLite + SQLAlchemy)      |   |         (Non-AI Engine Modules)         |
|                                 |   |                                         |
|  • users                        |   |  • devops_service.py (Data fetcher)     |
|  • applications                 |   |  • web_extractor.py  (HTML DOM scraper) |
|  • areas                        |   |  • test_generator.py (Rule analyzer)    |
|  • user_stories                 |   |  • deduplication.py  (SequenceMatcher)  |
|  • acceptance_criteria          |   |  • excel_exporter.py (OpenPyXL builder) |
+---------------------------------+   +-----------------------------------------+
                                                       │
                                                       ▼
+-------------------------------------------------------------------------------+
|                                OUTPUT ARTIFACTS                               |
|                                                                               |
|    1. Interactive Tabbed UI Table (Positive, Negative, and Edge Scenarios)    |
|    2. Microsoft Excel Workbook (.xlsx with colored headers and filters)       |
+-------------------------------------------------------------------------------+
```

---

## 21. Beginner Quick Reference

| Term | Simple Beginner Explanation |
| :--- | :--- |
| **API** (Application Programming Interface) | A formal communication bridge allowing the React frontend and FastAPI backend to exchange JSON data. |
| **Route / Endpoint** | A specific URL path on the backend (e.g. `POST /api/v1/auth/login`) configured to handle a specific request. |
| **Service** | A Python file containing pure business logic (e.g. parsing rules, scraping HTML, building Excel workbooks) separated from API route handling. |
| **Model** | An object-relational class (defined using SQLAlchemy) that directly represents a database table in SQLite. |
| **Schema** | A Pydantic data contract specifying the exact types and fields expected in request bodies and returned in API responses. |
| **Bearer Token** | A secure random 64-character string issued upon login that the frontend attaches to subsequent HTTP requests to verify identity. |
| **CORS** (Cross-Origin Resource Sharing) | A browser security mechanism configured on the FastAPI server to permit web requests originating from the Vite frontend port (`5173`). |
| **Positive Test Case** | A scenario verifying that the application works smoothly when given valid, compliant inputs under normal conditions (happy path). |
| **Negative Test Case** | A scenario verifying that the application correctly detects, rejects, and blocks invalid inputs or unauthorized actions with proper error alerts. |
| **Edge Test Case** | A scenario testing extreme boundary limits (e.g. values exactly at threshold limits, timeouts, or maximum string lengths). |

---

## How to Understand This Project in 30 Minutes

If you have only 30 minutes to understand this entire codebase, follow this prioritized 4-step path:

1. **Minute 00 - 05: Understand the Data Model**
   - Open [models/devops.py](file:///d:/3rd%20uc/backend/app/models/devops.py).
   - Notice the 3 connected database tables: `Area` (tree hierarchy) -> `UserStory` (requirements) -> `AcceptanceCriteria` (functional rules).
2. **Minute 05 - 15: Read the Core Generation Logic**
   - Open [services/test_generator.py](file:///d:/3rd%20uc/backend/app/services/test_generator.py).
   - Skim lines 103–302 (`Pattern 1: Numerical/Currency Limits`) and lines 570–655 (`Pattern 4: Security/OTP Attempts`).
   - Notice how it uses regular expressions to find numbers and limits, calculates boundary numbers mathematically, and creates `Positive`, `Negative`, and `Edge` test cases without any AI.
3. **Minute 15 - 23: Trace the UI Submission**
   - Open [frontend/src/components/ApplicationForm.tsx](file:///d:/3rd%20uc/frontend/src/components/ApplicationForm.tsx).
   - Read `handleSubmit()` (lines 275–323) to see how the selected Area, User Story, Acceptance Criteria IDs, and Application Links are packaged into a JSON request.
   - Open [backend/app/api/v1/endpoints/generation.py](file:///d:/3rd%20uc/backend/app/api/v1/endpoints/generation.py).
   - Read lines 25–124 to see how the request is received, passed to `devops_service`, `web_extractor`, and `test_generator_engine`.
4. **Minute 23 - 30: Trace the Excel Export**
   - Open [services/excel_exporter.py](file:///d:/3rd%20uc/backend/app/services/excel_exporter.py).
   - Inspect `generate_workbook()` (lines 19–198) to see how `openpyxl` creates the 3 sheets ("Positive", "Negative", "Edge"), applies dark navy header styling, colors high priorities red, and saves the binary `.xlsx` stream.
