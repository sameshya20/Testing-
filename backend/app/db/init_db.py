from app.db.session import engine, SessionLocal, Base
from app.models.application import Application
from app.models.user import User
from app.models.devops import Area, UserStory, AcceptanceCriteria
from app.core.security import hash_password

def init_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    if db.query(User).count() == 0:
        seed_users = [
            User(
                email="admin@enterprise.com",
                full_name="Enterprise Admin",
                hashed_password=hash_password("password123"),
                is_active=True
            ),
            User(
                email="qa@enterprise.com",
                full_name="QA Lead",
                hashed_password=hash_password("password123"),
                is_active=True
            )
        ]
        db.add_all(seed_users)
        db.commit()
        print("Database initialized with seed users.")

    if db.query(Application).count() == 0:
        seed_applications = [
            Application(
                name="Enterprise Banking Portal",
                code="BANK-PORTAL",
                domain="Financial Services & Core Banking",
                description="Core retail and commercial online banking platform handling funds transfer, bill payment, account management, and multi-factor authorization.",
                default_url="https://banking.enterprise.internal/app",
                business_rules="1. Transfers over $10,000 require Secondary Approval.\n2. Daily transfer limit is $50,000 for verified retail users.\n3. Account must be active and non-frozen to initiate outbound payments.\n4. Session times out after 15 minutes of inactivity.",
                user_roles="Retail Customer, Commercial User, Compliance Officer, System Administrator",
                key_modules="Accounts Summary, Wire Transfer, Bill Pay, Security Settings, Transaction Audit"
            ),
            Application(
                name="Healthcare Claims Management System",
                code="HEALTH-CLAIMS",
                domain="Healthcare & Health Insurance",
                description="End-to-end medical claims submission, adjudication, pre-authorization, and provider reimbursement platform.",
                default_url="https://claims.healthcore.internal",
                business_rules="1. Claim amounts exceeding $5,000 require manual review by Senior Claims Auditor.\n2. Diagnosis Code (ICD-10) must match Procedure Code (CPT) compatibility rules.\n3. Duplicate claim submissions within 30 days are automatically flagged.\n4. Patient coverage must be active on the service date.",
                user_roles="Healthcare Provider, Patient, Claims Specialist, Medical Auditor, Admin",
                key_modules="Claim Submission, Pre-Authorization, Eligibility Verification, Adjudication Engine, Remittance"
            ),
            Application(
                name="Global E-Commerce & Checkout Engine",
                code="ECOMM-CORE",
                domain="Retail & Digital Commerce",
                description="Omnichannel shopping cart, promotion application, payment gateway integration, and order fulfillment system.",
                default_url="https://storefront.retailglobal.com",
                business_rules="1. Promotional coupon codes cannot be combined unless explicitly marked stackable.\n2. Shipping calculation depends on total weight, dimensions, and destination country.\n3. Orders above $500 require Fraud Risk Scoring verification.\n4. Inventory is reserved for 15 minutes during checkout process.",
                user_roles="Guest Buyer, Registered Customer, Store Administrator, Inventory Manager",
                key_modules="Product Catalog, Shopping Cart, Promo Code Engine, Payment Checkout, Order Tracking"
            ),
            Application(
                name="Enterprise HR & Leave Management",
                code="HR-LEAVE",
                domain="Human Resources & Operations",
                description="Internal employee portal for annual leave requests, sick leave tracking, manager approvals, and payroll sync.",
                default_url="https://hrportal.enterprise.com",
                business_rules="1. Leave requests longer than 5 consecutive days require Line Manager and HR Approval.\n2. Employees cannot submit negative leave balances unless emergency leave is granted.\n3. Requests must be submitted at least 48 hours prior to start date.",
                user_roles="Standard Employee, Line Manager, HR Administrator, Payroll Officer",
                key_modules="Leave Calendar, Time-off Request, Approval Workflow, Balance History"
            ),
            Application(
                name="Commercial Insurance Underwriting Suite",
                code="INS-UNDERWRITE",
                domain="Insurance & Risk Assessment",
                description="Automated risk assessment, premium calculation, and policy issuance engine for commercial property and casualty policies.",
                default_url="https://underwriting.insuretech.com",
                business_rules="1. High-risk commercial properties (Risk Score > 75) trigger Mandatory On-site Survey.\n2. Policy effective date cannot be in the past.\n3. Discount threshold cap is 20% for standard underwriter delegation authority.",
                user_roles="Underwriter, Actuary, Insurance Agent, Risk Analyst, Executive Approver",
                key_modules="Risk Evaluator, Premium Calculator, Policy Authoring, Binding Engine"
            )
        ]
        db.add_all(seed_applications)
        db.commit()
        print("Database initialized with seed applications.")

    if db.query(Area).count() == 0:
        bank_app = db.query(Application).filter(Application.code == "BANK-PORTAL").first()
        health_app = db.query(Application).filter(Application.code == "HEALTH-CLAIMS").first()
        ecomm_app = db.query(Application).filter(Application.code == "ECOMM-CORE").first()
        hr_app = db.query(Application).filter(Application.code == "HR-LEAVE").first()
        ins_app = db.query(Application).filter(Application.code == "INS-UNDERWRITE").first()

        root_project = Area(
            name="Project",
            code="AREA-PROJECT",
            description="Root Project Area Path",
            parent_id=None
        )
        db.add(root_project)
        db.commit()

        # Level 1 Categories
        finance_area = Area(name="Finance", code="AREA-FINANCE", description="Finance and Banking Services", parent_id=root_project.id)
        hr_area = Area(name="HR", code="AREA-HR", description="Human Resources and Operations", parent_id=root_project.id)
        health_area = Area(name="Healthcare", code="AREA-HEALTH", description="Healthcare and Medical Systems", parent_id=root_project.id)
        sales_area = Area(name="Sales", code="AREA-SALES", description="Sales and E-Commerce Portal", parent_id=root_project.id)
        ins_area = Area(name="Insurance", code="AREA-INSURANCE", description="Commercial Insurance Systems", parent_id=root_project.id)

        db.add_all([finance_area, hr_area, health_area, sales_area, ins_area])
        db.commit()

        # Level 2 Specific Leaf Areas
        payments_area = Area(name="Payments", code="AREA-BANK-PAYMENTS", description="Payments and Fund Transfers", parent_id=finance_area.id, application_id=bank_app.id if bank_app else 1)
        banking_area = Area(name="Banking", code="AREA-BANK-CORE", description="Core Account & Banking Services", parent_id=finance_area.id, application_id=bank_app.id if bank_app else 1)
        
        recruitment_area = Area(name="Recruitment", code="AREA-USER-SEC", description="User Onboarding & Recruitment", parent_id=hr_area.id, application_id=bank_app.id if bank_app else 1)
        payroll_area = Area(name="Payroll", code="AREA-HR-LEAVE", description="Leave Management & Payroll", parent_id=hr_area.id, application_id=hr_app.id if hr_app else 4)

        claims_area = Area(name="Claims", code="AREA-HEALTH-CLAIMS", description="Medical Claims Submission", parent_id=health_area.id, application_id=health_app.id if health_app else 2)
        
        orders_area = Area(name="Orders", code="AREA-ECOMM-CHECKOUT", description="E-Commerce Checkout & Orders", parent_id=sales_area.id, application_id=ecomm_app.id if ecomm_app else 3)
        customers_area = Area(name="Customers", code="AREA-SALES-CUST", description="Customer Relationship Management", parent_id=sales_area.id, application_id=ecomm_app.id if ecomm_app else 3)

        underwriting_area = Area(name="Underwriting", code="AREA-INS-UNDERWRITE", description="Property Risk Evaluation", parent_id=ins_area.id, application_id=ins_app.id if ins_app else 5)

        db.add_all([payments_area, banking_area, recruitment_area, payroll_area, claims_area, orders_area, customers_area, underwriting_area])
        db.commit()
        print("Database initialized with Azure DevOps-style hierarchical seed areas.")

    if db.query(UserStory).count() == 0:
        payments_area = db.query(Area).filter(Area.code == "AREA-BANK-PAYMENTS").first()
        banking_area = db.query(Area).filter(Area.code == "AREA-BANK-CORE").first()
        recruitment_area = db.query(Area).filter(Area.code == "AREA-USER-SEC").first()
        payroll_area = db.query(Area).filter(Area.code == "AREA-HR-LEAVE").first()
        claims_area = db.query(Area).filter(Area.code == "AREA-HEALTH-CLAIMS").first()
        orders_area = db.query(Area).filter(Area.code == "AREA-ECOMM-CHECKOUT").first()
        underwriting_area = db.query(Area).filter(Area.code == "AREA-INS-UNDERWRITE").first()

        seed_stories = [
            UserStory(
                id="US-001",
                title="Login functionality",
                description="As a user, I want to securely log into the system with my credentials so that I can access protected features.",
                state="Active",
                assigned_to="Authentication Squad",
                area_id=banking_area.id if banking_area else 4
            ),
            UserStory(
                id="US-002",
                title="User registration",
                description="As a new user, I want to register an account so that I can use the enterprise platform.",
                state="Active",
                assigned_to="User Experience Team",
                area_id=recruitment_area.id if recruitment_area else 6
            ),
            UserStory(
                id="US-003",
                title="Password reset",
                description="As a registered user, I want to reset my password via email verification if I forget it.",
                state="Approved",
                assigned_to="Security Pod",
                area_id=recruitment_area.id if recruitment_area else 6
            ),
            UserStory(
                id="US-004",
                title="Dashboard access",
                description="As an authenticated user, I want to view my personalized dashboard with system status and summary metrics.",
                state="Active",
                assigned_to="Core UI Team",
                area_id=recruitment_area.id if recruitment_area else 6
            ),
            UserStory(
                id="US-101",
                title="Payment Processing",
                description="As an Online Banking Customer, I want to process payments and transfer funds with mandatory MFA verification for amounts exceeding threshold limits.",
                state="Active",
                assigned_to="Core Banking Squad",
                area_id=payments_area.id if payments_area else 3
            ),
            UserStory(
                id="US-102",
                title="Payment Validation",
                description="As a Banking Customer, I want to validate payment details prior to confirmation.",
                state="Active",
                assigned_to="Core Banking Squad",
                area_id=payments_area.id if payments_area else 3
            ),
            UserStory(
                id="US-103",
                title="Payment Failure",
                description="As a Banking Customer, I want clear error messaging when a payment fails due to insufficient funds or timeout.",
                state="Active",
                assigned_to="Core Banking Squad",
                area_id=payments_area.id if payments_area else 3
            ),
            UserStory(
                id="US-104",
                title="Employee Annual Leave Request & Manager Approval",
                description="As an Employee, I want to submit annual leave requests through the HR portal for my manager's review.",
                state="Active",
                assigned_to="HR Operations Team",
                area_id=payroll_area.id if payroll_area else 7
            ),
            UserStory(
                id="US-105",
                title="Commercial Risk Assessment & Policy Underwriting",
                description="As an Insurance Underwriter, I want to calculate property risk scores and issue policy quotes.",
                state="Approved",
                assigned_to="Underwriting Tech",
                area_id=underwriting_area.id if underwriting_area else 14
            )
        ]
        db.add_all(seed_stories)
        db.commit()
        print("Database initialized with seed user stories.")

    if db.query(AcceptanceCriteria).count() == 0:
        seed_criteria = [
            # US-001 Login functionality
            AcceptanceCriteria(id="US-001-AC-01", user_story_id="US-001", criteria_number=1, text="AC-01 - User should be able to enter valid credentials"),
            AcceptanceCriteria(id="US-001-AC-02", user_story_id="US-001", criteria_number=2, text="AC-02 - User should receive an error for invalid credentials"),
            AcceptanceCriteria(id="US-001-AC-03", user_story_id="US-001", criteria_number=3, text="AC-03 - User should be redirected to dashboard after login"),

            # US-002 User registration
            AcceptanceCriteria(id="US-002-AC-01", user_story_id="US-002", criteria_number=1, text="AC-01 - User should enter valid registration details (name, email, password)"),
            AcceptanceCriteria(id="US-002-AC-02", user_story_id="US-002", criteria_number=2, text="AC-02 - System should validate unique email address during registration"),
            AcceptanceCriteria(id="US-002-AC-03", user_story_id="US-002", criteria_number=3, text="AC-03 - Confirmation email should be sent upon successful registration"),

            # US-003 Password reset
            AcceptanceCriteria(id="US-003-AC-01", user_story_id="US-003", criteria_number=1, text="AC-01 - User can request password reset link using registered email address"),
            AcceptanceCriteria(id="US-003-AC-02", user_story_id="US-003", criteria_number=2, text="AC-02 - Reset link expires after 15 minutes of inactivity"),
            AcceptanceCriteria(id="US-003-AC-03", user_story_id="US-003", criteria_number=3, text="AC-03 - New password must meet mandatory complexity rules"),

            # US-004 Dashboard access
            AcceptanceCriteria(id="US-004-AC-01", user_story_id="US-004", criteria_number=1, text="AC-01 - User should see personalized dashboard widgets and metrics"),
            AcceptanceCriteria(id="US-004-AC-02", user_story_id="US-004", criteria_number=2, text="AC-02 - Navigation menu items should be displayed based on user roles"),
            AcceptanceCriteria(id="US-004-AC-03", user_story_id="US-004", criteria_number=3, text="AC-03 - Session timeout after 15 minutes redirects user to login screen"),

            # US-101 Fund Transfer & Multi-Factor Authorization
            AcceptanceCriteria(id="US-101-AC-01", user_story_id="US-101", criteria_number=1, text="AC-01 - Given the user is logged into online banking, source account list shows active accounts only."),
            AcceptanceCriteria(id="US-101-AC-02", user_story_id="US-101", criteria_number=2, text="AC-02 - Given transfer amount exceeding $10,000, OTP verification screen is presented."),
            AcceptanceCriteria(id="US-101-AC-03", user_story_id="US-101", criteria_number=3, text="AC-03 - Given invalid OTP entered 3 consecutive times, transaction is blocked and account locked."),
            AcceptanceCriteria(id="US-101-AC-04", user_story_id="US-101", criteria_number=4, text="AC-04 - Given successful transfer, system debits source account immediately and issues receipt."),

            # US-102 Medical Claim Submission & Pre-Authorization
            AcceptanceCriteria(id="US-102-AC-01", user_story_id="US-102", criteria_number=1, text="AC-01 - Given provider submits claim missing diagnosis code (ICD-10), system raises validation error."),
            AcceptanceCriteria(id="US-102-AC-02", user_story_id="US-102", criteria_number=2, text="AC-02 - Given total claim amount > $5,000, status transitions to Pending Senior Audit Review."),
            AcceptanceCriteria(id="US-102-AC-03", user_story_id="US-102", criteria_number=3, text="AC-03 - Given patient coverage is expired on date of service, claim is automatically rejected."),
            AcceptanceCriteria(id="US-102-AC-04", user_story_id="US-102", criteria_number=4, text="AC-04 - Given valid submission, system generates Claim Reference Number within 3 seconds."),

            # US-103 Shopping Cart Checkout & Coupon Application
            AcceptanceCriteria(id="US-103-AC-01", user_story_id="US-103", criteria_number=1, text="AC-01 - Given valid promotional coupon code, total subtotal decreases by discount percentage."),
            AcceptanceCriteria(id="US-103-AC-02", user_story_id="US-103", criteria_number=2, text="AC-02 - Given expired or invalid code, error message 'Invalid Coupon Code' is displayed."),
            AcceptanceCriteria(id="US-103-AC-03", user_story_id="US-103", criteria_number=3, text="AC-03 - Given order value exceeds $500, secondary payment authorization check is triggered."),
            AcceptanceCriteria(id="US-103-AC-04", user_story_id="US-103", criteria_number=4, text="AC-04 - Given cart items out of stock during checkout, system prevents payment."),

            # US-104 Employee Annual Leave Request & Manager Approval
            AcceptanceCriteria(id="US-104-AC-01", user_story_id="US-104", criteria_number=1, text="AC-01 - Given requested leave duration exceeds current balance, submission is rejected."),
            AcceptanceCriteria(id="US-104-AC-02", user_story_id="US-104", criteria_number=2, text="AC-02 - Given leave request > 5 consecutive days, manager approval and HR notification required."),
            AcceptanceCriteria(id="US-104-AC-03", user_story_id="US-104", criteria_number=3, text="AC-03 - Given overlapping leave dates already approved, system blocks duplicate request."),
            AcceptanceCriteria(id="US-104-AC-04", user_story_id="US-104", criteria_number=4, text="AC-04 - Given manager approves leave, employee leave balance is deducted."),

            # US-105 Commercial Risk Assessment & Policy Underwriting
            AcceptanceCriteria(id="US-105-AC-01", user_story_id="US-105", criteria_number=1, text="AC-01 - Given commercial property risk score > 75, policy binding requires On-site Physical Audit."),
            AcceptanceCriteria(id="US-105-AC-02", user_story_id="US-105", criteria_number=2, text="AC-02 - Given property in flood zone, mandatory flood rider premium must be appended."),
            AcceptanceCriteria(id="US-105-AC-03", user_story_id="US-105", criteria_number=3, text="AC-03 - Given policy effective date in past, system blocks submission."),
            AcceptanceCriteria(id="US-105-AC-04", user_story_id="US-105", criteria_number=4, text="AC-04 - Given authorized underwriter delegation, maximum discount override is 20%.")
        ]
        db.add_all(seed_criteria)
        db.commit()
        print("Database initialized with seed acceptance criteria.")

    db.close()

if __name__ == "__main__":
    init_db()
