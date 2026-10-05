import re
from typing import List, Dict, Any, Optional
from app.models.application import Application
from app.schemas.devops import DevOpsWorkItem
from app.schemas.test_case import TestCase, TestCaseGenerationResponse, CoverageSummary
from app.services.combination_engine import combination_engine
from app.services.deduplication_service import deduplication_service
from app.services.quality_validator import quality_validator


class ScenarioTemplate:
    """Represents a synthesized test scenario template with individual expected system behavior."""
    def __init__(
        self,
        category: str,
        priority: str,
        scenario: str,
        description: str,
        test_data: str,
        test_steps: List[str],
        expected_result: str
    ):
        self.category = category
        self.priority = priority
        self.scenario = scenario
        self.description = description
        self.test_data = test_data
        self.test_steps = test_steps
        self.expected_result = expected_result


class RequirementRuleAnalyzer:
    """
    Deterministic enterprise rule analyzer that extracts business conditions,
    thresholds, temporal constraints, and status rules to generate individual,
    scenario-specific Positive, Negative, and Edge test cases.
    """

    @staticmethod
    def clean_text(text: str) -> str:
        t = text.strip()
        # Remove leading numbering like '1. ', 'AC-01 - ', 'AC-1: ', '(1) '
        t = re.sub(r'^(?:[0-9]+[\.\)]\s*|AC-?[0-9]+[\s:-]*)+', '', t, flags=re.IGNORECASE).strip()
        return t

    @classmethod
    def matches_ac_filter(cls, story_id: str, idx: int, ac_raw: str, clean_ac: str, filter_items: Optional[List[str]]) -> bool:
        """Determines if an acceptance criterion matches the selected criteria filter."""
        if not filter_items:
            return True

        # Candidate identifiers for this AC
        candidates = {
            f"{story_id}-AC-{idx}".lower(),
            f"{story_id}-AC-{idx:02d}".lower(),
            f"{story_id} AC-{idx}".lower(),
            f"{story_id} AC-{idx:02d}".lower(),
            f"AC-{idx}".lower(),
            f"AC-{idx:02d}".lower(),
            str(idx),
            f"{idx:02d}"
        }

        # Check if raw text starts with explicit code like AC-01
        explicit_m = re.match(r'^(AC-?[0-9]+)', ac_raw.strip(), re.IGNORECASE)
        if explicit_m:
            code = explicit_m.group(1).lower()
            candidates.add(f"{story_id}-{code}".lower())
            candidates.add(f"{story_id} {code}".lower())
            candidates.add(code)

        for f_item in filter_items:
            f_norm = f_item.strip().lower()

            # If the filter item specifies a story prefix (e.g. us-101-ac-01, us-101 ac-1),
            # verify that the story prefix matches this story_id before matching
            story_prefix_m = re.match(r'^(us-[a-z0-9]+)[-_ ]', f_norm)
            if story_prefix_m and story_prefix_m.group(1) != story_id.lower():
                continue

            if f_norm in candidates:
                return True

            # Check if filter item matches AC number with story prefix (e.g. US-101-AC-01)
            num_m = re.search(r'(?:ac-?|#)?([0-9]+)$', f_norm)
            if num_m and story_id.lower() in f_norm:
                if int(num_m.group(1)) == idx:
                    return True

            # Textual matching (only when no conflicting story prefix)
            if not story_prefix_m:
                if clean_ac.lower() in f_norm or (len(f_norm) > 8 and f_norm in clean_ac.lower()):
                    return True

        return False

    @classmethod
    def analyze_requirement(
        cls,
        text: str,
        ref_code: str,
        story_id: str,
        page_name: str,
        page_url: str,
        action_btn: str,
        field_1: Optional[str],
        field_2: Optional[str],
        roles: List[str],
        is_verified: bool
    ) -> List[ScenarioTemplate]:
        """
        Synthesizes individual, scenario-specific Positive, Negative, and Edge test cases
        derived directly from the semantic conditions of the requirement.
        """
        clean = cls.clean_text(text)
        lower = clean.lower()
        role = roles[0] if roles else "Standard User"
        nav_step = f"1. Navigate to {page_name} ({page_url})." if page_url else f"1. Navigate to {page_name or 'application interface'}."
        btn = action_btn or "Submit"

        scenarios: List[ScenarioTemplate] = []

        # -----------------------------------------------------------------
        # Pattern 1: Numerical, Currency, and Quantitative Limit Thresholds
        # -----------------------------------------------------------------
        curr_m = re.search(
            r'(?:over|exceeding|greater than|more than|above|>|limit is|maximum of|cap is|capped at|up to)\s*\$([0-9,]+(?:\.[0-9]+)?)',
            clean,
            re.IGNORECASE
        )
        if not curr_m:
            curr_m = re.search(r'\$([0-9,]+(?:\.[0-9]+)?)\s*(?:limit|cap|threshold)?', clean)
            if curr_m and not any(k in lower for k in ['over', 'exceed', 'limit', 'above', '>', 'cap', 'threshold', 'maximum']):
                curr_m = None

        unit_m = None
        if not curr_m:
            unit_m = re.search(
                r'(?:longer than|exceeding|greater than|more than|above|>|over|at least|limit is|cap is)\s*([0-9,]+(?:\.[0-9]+)?)\s*(consecutive\s*days?|days?|hours?|minutes?|weeks?|months?|%|percent)',
                clean,
                re.IGNORECASE
            )
            if not unit_m:
                unit_m = re.search(
                    r'(?:risk score|score|discount|override|cap)\s*(?:>|>=|is|of)?\s*([0-9,]+(?:\.[0-9]+)?)\s*(%|percent)?',
                    clean,
                    re.IGNORECASE
                )

        if curr_m or unit_m:
            is_currency = curr_m is not None
            if is_currency:
                raw_num = curr_m.group(1).replace(',', '')
                num_val = float(raw_num)
                formatted_thresh = f"${int(num_val):,}" if num_val.is_integer() else f"${num_val:,.2f}"
                val_at_limit = formatted_thresh
                val_just_above = f"${num_val + 0.01:,.2f}"
                val_compliant = f"${int(num_val * 0.5):,}" if num_val >= 2 else f"${num_val * 0.5:.2f}"
                val_exceeded = f"${int(num_val * 1.5):,}" if num_val >= 2 else f"${num_val * 1.5:.2f}"
            else:
                raw_num = unit_m.group(1).replace(',', '')
                num_val = float(raw_num)
                unit_str = unit_m.group(2) if len(unit_m.groups()) >= 2 and unit_m.group(2) else ""
                unit_str = unit_str.strip()
                formatted_thresh = f"{int(num_val) if num_val.is_integer() else num_val} {unit_str}".strip().replace(" %", "%")
                val_at_limit = formatted_thresh
                step = 1 if num_val >= 1 else 0.1
                val_just_above = f"{int(num_val + step) if (num_val + step).is_integer() else num_val + step} {unit_str}".strip().replace(" %", "%")
                val_compliant = f"{int(num_val - step) if (num_val - step).is_integer() and (num_val - step) > 0 else (num_val - step)} {unit_str}".strip().replace(" %", "%") if num_val > step else formatted_thresh
                val_exceeded = f"{int(num_val + step * 5) if (num_val + step * 5).is_integer() else num_val + step * 5} {unit_str}".strip().replace(" %", "%")

            # Subject identification
            if 'discount' in lower:
                subject = "Discount"
            elif any(w in lower for w in ['transfer', 'payment', 'fund']):
                subject = "Transfer"
            elif 'claim' in lower:
                subject = "Claim"
            elif any(w in lower for w in ['order', 'checkout', 'cart']):
                subject = "Order"
            elif 'leave' in lower:
                subject = "Leave Request"
            elif any(w in lower for w in ['risk score', 'property', 'underwrite', 'policy']):
                subject = "Property Risk Evaluation"
            else:
                subject = "Transaction"

            # Consequence / Requirement identification
            if any(w in lower for w in ['secondary approval', 'second approval']):
                req_action = "secondary approval"
            elif any(w in lower for w in ['otp verification', 'otp']):
                req_action = "OTP verification"
            elif any(w in lower for w in ['senior audit', 'senior claims auditor', 'manual review']):
                req_action = "Senior Audit Review"
            elif any(w in lower for w in ['fraud risk', 'fraud']):
                req_action = "fraud risk scoring verification"
            elif any(w in lower for w in ['line manager and hr', 'hr approval', 'manager approval']):
                req_action = "Line Manager and HR Approval"
            elif any(w in lower for w in ['on-site physical audit', 'on-site survey', 'mandatory on-site']):
                req_action = "mandatory on-site physical survey"
            elif any(w in lower for w in ['daily transfer limit', 'daily limit']):
                req_action = "daily limit restriction"
            elif 'override' in lower or 'cap' in lower:
                req_action = "delegation authorization"
            else:
                req_action = "additional authorization review"

            is_daily_limit = 'daily' in lower and 'limit' in lower

            # Positive Test Case
            if is_daily_limit:
                pos_scen = f"[{ref_code}] Verify {subject} Within Allowed Daily Limit ({val_at_limit})"
                pos_desc = f"Ensure system accepts transfers that do not exceed the daily cumulative limit of {val_at_limit}."
                pos_exp = f"When daily transfers remain within the {val_at_limit} limit, the system accepts and processes the transfer successfully for verified users."
            else:
                pos_scen = f"[{ref_code}] Verify {subject} Submission Within Standard Threshold ({val_at_limit} or below)"
                pos_desc = f"Ensure system accepts compliant {subject.lower()} of {val_at_limit} or below without requiring {req_action}."
                pos_exp = f"When a {subject.lower()} of {val_at_limit} is submitted with all required valid details, the system accepts the {subject.lower()} without requiring {req_action}."

            scenarios.append(ScenarioTemplate(
                category="Positive",
                priority="High",
                scenario=pos_scen,
                description=pos_desc,
                test_data=f"{subject} Amount/Value: {val_at_limit}; Role: {role}",
                test_steps=[
                    nav_step,
                    f"2. Authenticate as authorized '{role}'.",
                    f"3. Input {subject.lower()} test data with compliant value '{val_at_limit}'.",
                    f"4. Click '{btn}' button to submit."
                ],
                expected_result=pos_exp
            ))

            # Negative Test Case
            if is_daily_limit:
                neg_scen = f"[{ref_code}] Verify Rejection When {subject} Exceeds {val_at_limit} Daily Limit"
                neg_desc = f"Validate that system blocks transfers exceeding the daily quota of {val_at_limit}."
                neg_exp = f"When a {subject.lower()} exceeds the {val_at_limit} daily limit, the system blocks completion and indicates that the daily limit has been exceeded."
            else:
                neg_scen = f"[{ref_code}] Verify {subject} Above {val_at_limit} Without {req_action.title()} Is Blocked"
                neg_desc = f"Validate that system halts processing when {subject.lower()} exceeds {val_at_limit} without fulfilling {req_action}."
                neg_exp = f"When a {subject.lower()} above {val_at_limit} is submitted without {req_action}, the system prevents completion and indicates that {req_action} is required."

            scenarios.append(ScenarioTemplate(
                category="Negative",
                priority="High",
                scenario=neg_scen,
                description=neg_desc,
                test_data=f"{subject} Amount/Value: {val_exceeded} (Exceeds {val_at_limit}); Missing: {req_action}",
                test_steps=[
                    nav_step,
                    f"2. Authenticate as '{role}'.",
                    f"3. Input {subject.lower()} value of '{val_exceeded}' exceeding allowed boundary.",
                    f"4. Attempt to finalize submission without providing required '{req_action}'."
                ],
                expected_result=neg_exp
            ))

            # Edge Case 1: Exactly at threshold
            if is_daily_limit:
                edg1_scen = f"[{ref_code}] Verify Boundary: Cumulative Daily {subject} Exactly At {val_at_limit} Limit"
                edg1_desc = f"Test system behavior when daily total reaches exactly 100% of the {val_at_limit} quota."
                edg1_exp = f"When cumulative daily {subject.lower()}s reach exactly {val_at_limit}, the system processes the {subject.lower()} according to the threshold rule without exceeding the daily cap."
            else:
                edg1_scen = f"[{ref_code}] Verify Boundary: {subject} Exactly At Allowed Threshold ({val_at_limit})"
                edg1_desc = f"Test system behavior when {subject.lower()} value is submitted at the exact threshold boundary of {val_at_limit}."
                edg1_exp = f"When a {subject.lower()} of exactly {val_at_limit} is submitted, the system processes the {subject.lower()} according to the threshold rule without triggering the above-{val_at_limit} {req_action} requirement."

            scenarios.append(ScenarioTemplate(
                category="Edge",
                priority="Medium",
                scenario=edg1_scen,
                description=edg1_desc,
                test_data=f"Exact Boundary Value: {val_at_limit}",
                test_steps=[
                    nav_step,
                    f"2. Enter exact boundary amount '{val_at_limit}'.",
                    f"3. Submit via '{btn}' button.",
                    "4. Verify boundary rule evaluation."
                ],
                expected_result=edg1_exp
            ))

            # Edge Case 2: Just above threshold
            if is_daily_limit:
                edg2_scen = f"[{ref_code}] Verify Boundary: {subject} Exceeding Daily Limit By Minimum Increment ({val_just_above})"
                edg2_desc = f"Verify system detects daily limit breach at smallest incremental value over {val_at_limit}."
                edg2_exp = f"When cumulative daily {subject.lower()}s reach {val_just_above}, the system identifies that the {val_at_limit} daily limit has been exceeded and rejects the transfer."
            else:
                edg2_scen = f"[{ref_code}] Verify Boundary: {subject} Just Above Threshold Limit ({val_just_above})"
                edg2_desc = f"Verify system immediately triggers {req_action} at the smallest increment above {val_at_limit}."
                edg2_exp = f"When a {subject.lower()} of {val_just_above} is submitted, the system identifies that the threshold has been exceeded and requires {req_action}."

            scenarios.append(ScenarioTemplate(
                category="Edge",
                priority="High",
                scenario=edg2_scen,
                description=edg2_desc,
                test_data=f"Smallest Increment Above Boundary: {val_just_above}",
                test_steps=[
                    nav_step,
                    f"2. Enter amount '{val_just_above}' (threshold + delta).",
                    f"3. Submit via '{btn}' button.",
                    f"4. Confirm prompt for '{req_action}'."
                ],
                expected_result=edg2_exp
            ))

            return scenarios

        # -----------------------------------------------------------------
        # Pattern 2: Temporal, Inactivity, Expiration, and Timeout Rules
        # -----------------------------------------------------------------
        time_m = re.search(
            r'(?:times?\s*out|expires?|reserved for|within|at least)\s*(?:after\s*)?([0-9,]+)\s*(minutes?|seconds?|hours?|days?)',
            clean,
            re.IGNORECASE
        )
        past_date_m = 'past' in lower and ('date' in lower or 'effective' in lower)

        if time_m or past_date_m:
            if time_m:
                time_val = time_m.group(1)
                time_unit = time_m.group(2)
                timeframe = f"{time_val} {time_unit}"
            else:
                timeframe = "historical date (in the past)"

            if 'session' in lower:
                subject = "Session"
            elif 'reset link' in lower:
                subject = "Reset Link"
            elif 'inventory' in lower:
                subject = "Inventory Reservation"
            elif 'claim' in lower:
                subject = "Duplicate Claim Protection"
            elif 'leave' in lower or 'request' in lower:
                subject = "Advance Notice Submission"
            elif 'policy' in lower or 'effective' in lower:
                subject = "Policy Effective Date"
            else:
                subject = "Session Timer"

            if past_date_m:
                pos_scen = f"[{ref_code}] Verify {subject} Validated With Current or Future Date"
                pos_desc = f"Ensure system accepts {subject.lower()} when effective date is scheduled on current date or future date."
                pos_exp = f"When policy effective date is set to current or future date, the system validates the effective date and proceeds with underwriting."

                neg_scen = f"[{ref_code}] Verify Rejection When {subject} Is Set in the Past"
                neg_desc = f"Validate system blocks policy submission when effective date is set prior to current date."
                neg_exp = f"When policy effective date is set in the past, the system rejects the submission with validation error indicating effective date cannot be in the past."

                edg_scen = f"[{ref_code}] Verify Boundary: {subject} Set Exactly to Current Date / Timestamp"
                edg_desc = f"Test boundary where effective date is set to today's active date."
                edg_exp = f"When policy effective date is set to the current system date and time, the system accepts it as the earliest valid effective timestamp."
            else:
                pos_scen = f"[{ref_code}] Verify {subject} Maintained During Active Usage Within {timeframe}"
                pos_desc = f"Ensure system keeps {subject.lower()} active while user interacts within allowable {timeframe} window."
                pos_exp = f"When user activity occurs within {timeframe}, the system maintains the active session without requiring re-login."

                neg_scen = f"[{ref_code}] Verify {subject} Expiration and Invalidation After {timeframe} Inactivity"
                neg_desc = f"Validate system terminates {subject.lower()} when inactivity exceeds {timeframe}."
                neg_exp = f"When {timeframe} of inactivity elapse, the system expires the session according to the timeout rule and redirects the user to the login screen."

                edg_scen = f"[{ref_code}] Verify Boundary: {subject} Evaluated Exactly At {timeframe} Boundary"
                edg_desc = f"Test system behavior at exact {timeframe} threshold mark."
                edg_exp = f"When inactivity reaches exactly {timeframe}, the system expires the session according to the timeout rule."

                edg2_scen = f"[{ref_code}] Verify Boundary: {subject} Interaction Just Before Timeout Cutoff"
                edg2_desc = f"Verify user action dispatched immediately prior to {timeframe} resets expiration timer."
                edg2_exp = f"When user activity is detected just before the {timeframe} threshold, the system resets the inactivity timer and keeps the session active."

                scenarios.append(ScenarioTemplate(
                    category="Edge",
                    priority="Medium",
                    scenario=edg2_scen,
                    description=edg2_desc,
                    test_data=f"Inactivity Duration: Just Before {timeframe} Threshold",
                    test_steps=[
                        nav_step,
                        f"2. Maintain idle state until immediately before {timeframe}.",
                        f"3. Dispatch user action via '{btn}'.",
                        "4. Verify session timer resets."
                    ],
                    expected_result=edg2_exp
                ))

            scenarios.append(ScenarioTemplate(
                category="Positive",
                priority="High" if past_date_m else "Medium",
                scenario=pos_scen,
                description=pos_desc,
                test_data=f"Time Parameter: Compliant within {timeframe}",
                test_steps=[
                    nav_step,
                    f"2. Authenticate as authorized '{role}'.",
                    f"3. Perform transaction within allowable timeframe.",
                    f"4. Confirm operation completes successfully."
                ],
                expected_result=pos_exp
            ))

            scenarios.append(ScenarioTemplate(
                category="Negative",
                priority="High",
                scenario=neg_scen,
                description=neg_desc,
                test_data=f"Time Parameter: Violates {timeframe} threshold",
                test_steps=[
                    nav_step,
                    f"2. Allow {timeframe} condition to be violated.",
                    f"3. Attempt to submit transaction.",
                    "4. Verify system blocks transaction and displays expiration/date error."
                ],
                expected_result=neg_exp
            ))

            scenarios.append(ScenarioTemplate(
                category="Edge",
                priority="Medium",
                scenario=edg_scen,
                description=edg_desc,
                test_data=f"Exact Boundary: Exactly {timeframe}",
                test_steps=[
                    nav_step,
                    f"2. Set timing parameter to exact {timeframe} boundary.",
                    f"3. Execute transaction check via '{btn}'.",
                    "4. Verify boundary policy enforcement."
                ],
                expected_result=edg_exp
            ))

            return scenarios

        # -----------------------------------------------------------------
        # Pattern 3: State, Prerequisite, and Account Standing Conditions
        # -----------------------------------------------------------------
        state_patterns = [
            'active and non-frozen', 'non-frozen', 'active', 'frozen', 'expired',
            'coverage', 'negative leave', 'combined', 'stackable', 'compatibility',
            'duplicate claim', 'out of stock', 'overlapping'
        ]

        if any(sp in lower for sp in state_patterns):
            if 'frozen' in lower or 'non-frozen' in lower or ('account' in lower and 'active' in lower):
                subject = "Transfer"
                pos_scen = f"[{ref_code}] Verify Outbound Payment Initiation From Active Non-Frozen Account"
                pos_desc = "Ensure system validates account standing and allows outbound transfer when account is active and non-frozen."
                pos_exp = "When a transfer is initiated from an active and non-frozen account, the system verifies account standing and proceeds with the transaction successfully."

                neg_scen = f"[{ref_code}] Verify Rejection of Transfer Attempt From Frozen Account"
                neg_desc = "Validate that system blocks outbound payment initiation when source account is in frozen state."
                neg_exp = "When a transfer is attempted from a frozen account, the system rejects the transaction and displays an account restriction error."

                edg_scen = f"[{ref_code}] Verify Boundary: Account Status Transitions Concurrently During In-Flight Transfer"
                edg_desc = "Test system behavior when account state changes to frozen while payment settlement is in-flight."
                edg_exp = "System checks real-time account status at final execution, detects frozen state, and immediately aborts the transaction preventing balance debit."

            elif 'coverage' in lower:
                subject = "Medical Claim"
                pos_scen = f"[{ref_code}] Verify Claim Adjudication For Patient With Active Coverage"
                pos_desc = "Ensure claim is accepted for adjudication when patient coverage is active on the date of service."
                pos_exp = "When patient coverage is active on the service date, the system verifies eligibility and accepts the claim for processing."

                neg_scen = f"[{ref_code}] Verify Automatic Rejection When Patient Coverage Is Expired"
                neg_desc = "Ensure claim is rejected automatically when service date falls outside active coverage period."
                neg_exp = "When patient coverage is expired on date of service, the claim is automatically rejected with code ERR-COV-EXP."

                edg_scen = f"[{ref_code}] Verify Boundary: Service Date Matches Exact Midnight Coverage Termination"
                edg_desc = "Test boundary where service date coincides with exact policy inception or expiration timestamp."
                edg_exp = "System evaluates coverage eligibility at midnight boundary of policy termination, adhering strictly to timestamp coverage rules."

            elif 'negative leave' in lower or 'leave balance' in lower:
                subject = "Leave Request"
                pos_scen = f"[{ref_code}] Verify Leave Submission Within Available Positive Balance"
                pos_desc = "Ensure leave submission succeeds when requested days are within available positive leave balance."
                pos_exp = "When an employee submits a leave request within available positive balance, the system accepts the request and updates leave ledger."

                neg_scen = f"[{ref_code}] Verify Rejection of Leave Request Exceeding Available Balance"
                neg_desc = "Validate system prevents submission resulting in negative leave balance without emergency approval."
                neg_exp = "When requested leave duration exceeds current balance, the system rejects the submission with insufficient balance error."

                edg_scen = f"[{ref_code}] Verify Boundary: Leave Request Reducing Balance to Exactly Zero Days"
                edg_desc = "Test boundary where requested days equal exactly total available leave balance."
                edg_exp = "When leave request reduces balance to exactly 0.00 days, the system accepts the request and updates remaining balance to zero without overdraft."

            elif 'coupon' in lower or 'stackable' in lower:
                subject = "Promotional Coupon"
                pos_scen = f"[{ref_code}] Verify Application of Single Valid Promotional Coupon"
                pos_desc = "Ensure promotional coupon code is applied successfully to decrease order subtotal."
                pos_exp = "When a valid promotional coupon code is applied, the system decreases total subtotal by the discount percentage."

                neg_scen = f"[{ref_code}] Verify Rejection When Combining Multiple Non-Stackable Coupons"
                neg_desc = "Ensure system blocks concurrent application of multiple non-stackable coupons."
                neg_exp = "When multiple non-stackable coupon codes are applied concurrently, the system rejects the secondary coupon and displays combination restriction notice."

                edg_scen = f"[{ref_code}] Verify Boundary: Coupon Applied At Exact Minimum Order Value Threshold"
                edg_desc = "Test coupon application when cart value equals exact minimum qualifying spend."
                edg_exp = "When order total matches the exact minimum qualifying spend threshold, the system applies the coupon discount cleanly."

            elif 'compatibility' in lower or 'cpt' in lower or 'diagnosis' in lower:
                subject = "Clinical Code Compatibility"
                pos_scen = f"[{ref_code}] Verify Acceptance of Compatible Diagnosis (ICD-10) and Procedure (CPT) Codes"
                pos_desc = "Ensure system validates clinical pairing of diagnosis and procedure codes."
                pos_exp = "When diagnosis code (ICD-10) matches procedure code (CPT) compatibility rules, the system validates the claim line and proceeds."

                neg_scen = f"[{ref_code}] Verify Rejection on Incompatible Diagnosis and Procedure Pairing"
                neg_desc = "Ensure system halts submission when ICD-10 code conflicts with CPT procedure."
                neg_exp = "When diagnosis code is incompatible with procedure code rules, the system halts submission and displays clinical incompatibility validation error."

                edg_scen = f"[{ref_code}] Verify Boundary: Secondary Supporting Diagnosis Code at Compatibility Perimeter"
                edg_desc = "Test boundary where secondary diagnosis code meets borderline procedure compatibility criteria."
                edg_exp = "System verifies secondary diagnosis code against CPT coverage matrix and routes for specialized review if borderline."

            else:
                subject = "Entity State"
                pos_scen = f"[{ref_code}] Verify Successful Workflow Under Compliant Business State"
                pos_desc = f"Ensure system accepts transaction when all conditions for '{clean[:45]}' are met."
                pos_exp = f"When valid business conditions conforming to '{clean[:50]}' are satisfied, the system accepts and processes the request successfully."

                neg_scen = f"[{ref_code}] Verify Rejection on Violation of Business Condition"
                neg_desc = f"Validate system prevents completion when conditions for '{clean[:45]}' are violated."
                neg_exp = f"When operation violates business rule '{clean[:50]}', the system halts processing and displays appropriate validation error."

                edg_scen = f"[{ref_code}] Verify Boundary Condition Evaluation for Business State"
                edg_desc = f"Test system behavior at state boundary limits for '{clean[:45]}'."
                edg_exp = f"System safely handles boundary state transitions for '{clean[:50]}', preventing state corruption and enforcing data integrity."

            scenarios.append(ScenarioTemplate(
                category="Positive",
                priority="High",
                scenario=pos_scen,
                description=pos_desc,
                test_data=f"Prerequisite Status: Active / Valid; Role: {role}",
                test_steps=[
                    nav_step,
                    f"2. Verify prerequisite status is active and compliant.",
                    f"3. Input required transaction fields.",
                    f"4. Click '{btn}' button to submit."
                ],
                expected_result=pos_exp
            ))

            scenarios.append(ScenarioTemplate(
                category="Negative",
                priority="High",
                scenario=neg_scen,
                description=neg_desc,
                test_data=f"Prerequisite Status: Invalid / Restricted / Expired",
                test_steps=[
                    nav_step,
                    f"2. Set prerequisite condition to restricted/invalid state.",
                    f"3. Attempt to trigger operation via '{btn}'.",
                    "4. Confirm system blocks submission and displays validation error."
                ],
                expected_result=neg_exp
            ))

            scenarios.append(ScenarioTemplate(
                category="Edge",
                priority="Medium",
                scenario=edg_scen,
                description=edg_desc,
                test_data="Boundary State / Concurrent State Modification",
                test_steps=[
                    nav_step,
                    "2. Initialize operation in boundary state.",
                    f"3. Submit request via '{btn}'.",
                    "4. Confirm transaction handles boundary without unhandled exceptions."
                ],
                expected_result=edg_exp
            ))

            return scenarios

        # -----------------------------------------------------------------
        # Pattern 4: Security, Authentication, and Attempt Counters
        # -----------------------------------------------------------------
        if any(w in lower for w in ['otp', 'lockout', 'locked', 'consecutive', 'credentials', 'password']):
            count_m = re.search(r'([0-9]+)\s*consecutive', clean, re.IGNORECASE)
            limit_num = int(count_m.group(1)) if count_m else 3

            def ordinal(n: int) -> str:
                return f"{n}th" if 11 <= (n % 100) <= 13 else {1: "1st", 2: "2nd", 3: "3rd"}.get(n % 10, f"{n}th")

            pos_scen = f"[{ref_code}] Verify Successful Verification On First Valid Attempt"
            pos_desc = "Ensure user completes authentication smoothly on initial valid credential submission."
            pos_exp = "When valid verification credentials are submitted on the first attempt, the system authorizes the user and completes the operation immediately."

            neg_scen = f"[{ref_code}] Verify Account Lockout Triggered After {limit_num} Consecutive Invalid Attempts"
            neg_desc = f"Validate system blocks transaction and locks account upon reaching {limit_num} consecutive failed verification attempts."
            neg_exp = f"When invalid verification credentials are entered {limit_num} consecutive times, the system blocks the transaction, locks the account for 15 minutes, and logs a security event."

            edg_scen = f"[{ref_code}] Verify Boundary: Successful Entry On Final Allowed Attempt ({limit_num-1} Failed + 1 Valid)"
            edg_desc = f"Test boundary where {limit_num-1} invalid attempts are followed immediately by valid submission."
            edg_exp = f"When invalid credentials are entered {limit_num-1} times followed by valid credentials on the final attempt, the system accepts the valid attempt, resets failure count, and avoids lockout."

            edg2_scen = f"[{ref_code}] Verify Exact Lockout Boundary On Attempt #{limit_num}"
            edg2_desc = f"Ensure account lockout transitions immediately upon submission of the {ordinal(limit_num)} failed attempt."
            edg2_exp = f"When the {ordinal(limit_num)} consecutive failed attempt is submitted, the system immediately locks the account and disables further input."

            scenarios.append(ScenarioTemplate(
                category="Positive",
                priority="High",
                scenario=pos_scen,
                description=pos_desc,
                test_data="Valid Verification Code / Credentials",
                test_steps=[
                    nav_step,
                    "2. Trigger verification challenge.",
                    "3. Enter valid verification credentials on Attempt 1.",
                    "4. Confirm transaction proceeds without lockout."
                ],
                expected_result=pos_exp
            ))

            scenarios.append(ScenarioTemplate(
                category="Negative",
                priority="High",
                scenario=neg_scen,
                description=neg_desc,
                test_data=f"Invalid Credentials entered {limit_num} times consecutively",
                test_steps=[
                    nav_step,
                    f"2. Enter invalid verification inputs {limit_num} times consecutively.",
                    f"3. Submit {ordinal(limit_num)} failed attempt.",
                    "4. Confirm account is locked and security alert is displayed."
                ],
                expected_result=neg_exp
            ))

            scenarios.append(ScenarioTemplate(
                category="Edge",
                priority="High",
                scenario=edg_scen,
                description=edg_desc,
                test_data=f"{limit_num-1} Invalid Attempts followed by 1 Valid Attempt",
                test_steps=[
                    nav_step,
                    f"2. Enter {limit_num-1} incorrect attempts sequentially.",
                    f"3. Enter valid correct credentials on final attempt {limit_num}.",
                    "4. Verify successful authorization without triggering lockout."
                ],
                expected_result=edg_exp
            ))

            scenarios.append(ScenarioTemplate(
                category="Edge",
                priority="Medium",
                scenario=edg2_scen,
                description=edg2_desc,
                test_data=f"Exact Boundary: Submission #{limit_num}",
                test_steps=[
                    nav_step,
                    f"2. Reach attempt #{limit_num}.",
                    "3. Submit invalid attempt.",
                    "4. Verify lockout state triggers immediately on threshold."
                ],
                expected_result=edg2_exp
            ))

            return scenarios

        # -----------------------------------------------------------------
        # Pattern 5: General Requirements and User Story AC Fallback
        # -----------------------------------------------------------------
        pos_scen = f"[{ref_code}] Verify Compliant Execution: {clean[:45]}"
        pos_desc = f"Ensure system successfully processes workflow adhering to requirement: {clean}"
        pos_exp = f"When valid inputs conforming to '{clean[:55]}' are submitted, the system accepts the request and updates state successfully."

        neg_scen = f"[{ref_code}] Verify Validation Error on Non-Compliant Input: {clean[:40]}"
        neg_desc = f"Ensure system halts processing and displays inline validation error when inputs violate: {clean}"
        neg_exp = f"When operation violates requirement ('{clean[:50]}'), the system halts processing and displays highlighted validation error."

        edg_scen = f"[{ref_code}] Verify Boundary Values & Data Extremes: {clean[:40]}"
        edg_desc = f"Test system resilience with boundary field lengths, null values, or extreme inputs for: {clean}"
        edg_exp = f"System safely handles boundary and extreme values for '{clean[:50]}', enforcing business constraints without server errors."

        scenarios.append(ScenarioTemplate(
            category="Positive",
            priority="High",
            scenario=pos_scen,
            description=pos_desc,
            test_data=f"Valid Compliant Test Data; Role: {role}",
            test_steps=[
                nav_step,
                f"2. Authenticate as '{role}'.",
                f"3. Enter valid data satisfying: {clean[:60]}.",
                f"4. Click '{btn}' button."
            ],
            expected_result=pos_exp
        ))

        scenarios.append(ScenarioTemplate(
            category="Negative",
            priority="High",
            scenario=neg_scen,
            description=neg_desc,
            test_data="Invalid or Non-Compliant Data Payload",
            test_steps=[
                nav_step,
                "2. Enter invalid or missing test inputs.",
                f"3. Attempt submission via '{btn}' button.",
                "4. Confirm validation error is displayed."
            ],
            expected_result=neg_exp
        ))

        scenarios.append(ScenarioTemplate(
            category="Edge",
            priority="Medium",
            scenario=edg_scen,
            description=edg_desc,
            test_data="Boundary Lengths, Empty Nulls, Extreme Special Characters",
            test_steps=[
                nav_step,
                "2. Input boundary values (min/max lengths, edge characters).",
                f"3. Submit via '{btn}' button.",
                "4. Verify clean handling without unhandled exceptions."
            ],
            expected_result=edg_exp
        ))

        return scenarios


class TestGeneratorEngine:
    """Enterprise multi-requirement analyzer and deterministic test case generation engine."""

    def generate_multi_requirement_test_suite(
        self,
        app: Application,
        stories: List[DevOpsWorkItem],
        selected_ac_filter: Optional[List[str]],
        url_metadata: Optional[Dict[str, Any]] = None,
        url_analyzed: bool = False,
        url_message: str = "",
        page_contexts: Optional[List[Dict[str, Any]]] = None
    ) -> TestCaseGenerationResponse:
        
        # Normalize page contexts
        contexts_list: List[Dict[str, Any]] = page_contexts if page_contexts is not None else []
        if not contexts_list and url_metadata and url_metadata.get("page_title"):
            contexts_list = [url_metadata]

        successful_contexts = [c for c in contexts_list if c.get("status") == "success"]

        roles = [r.strip() for r in (app.user_roles or "Standard User, Administrator").split(",")]
        rules = [r.strip() for r in (app.business_rules or "").split("\n") if r.strip()]

        positive_cases: List[TestCase] = []
        negative_cases: List[TestCase] = []
        edge_cases: List[TestCase] = []
        
        covered_story_ids = list(dict.fromkeys(s.id for s in stories))
        total_ac_evaluated = 0
        evaluated_story_ids = set()

        # --- 1. Evaluate User Stories and Acceptance Criteria ---
        for story_index, story in enumerate(stories):
            # Page context association
            specific_ctx = None
            if contexts_list:
                for ctx in contexts_list:
                    req_ref = ctx.get("requirement_ref")
                    if req_ref and (req_ref.upper() == story.id.upper() or story.id.upper() in req_ref.upper()):
                        specific_ctx = ctx
                        break
                if not specific_ctx:
                    specific_ctx = contexts_list[story_index % len(contexts_list)]

            is_verified = specific_ctx.get("status") == "success" if specific_ctx else False
            page_name = specific_ctx.get("name") or specific_ctx.get("page_title") or "" if specific_ctx else ""
            page_url = specific_ctx.get("url") or "" if specific_ctx else ""

            # Extract verified DOM elements if accessible
            detected_inputs = specific_ctx.get("detected_inputs", []) if (specific_ctx and is_verified) else []
            detected_actions = specific_ctx.get("detected_actions", []) if (specific_ctx and is_verified) else []
            observed_errors = specific_ctx.get("observed_errors", []) if (specific_ctx and is_verified) else []

            field_1 = detected_inputs[0] if len(detected_inputs) > 0 else None
            field_2 = detected_inputs[1] if len(detected_inputs) > 1 else None
            action_btn = detected_actions[0] if len(detected_actions) > 0 else ("Submit" if not is_verified else "Action")

            nav_step = f"1. Navigate to {page_name} ({page_url})." if page_url else f"1. Navigate to {app.name} interface."

            # Preconditions builder
            if is_verified and page_name and detected_inputs:
                base_precond = f"User is authenticated on verified page '{page_name}' ({page_url}). Observed UI controls: [{', '.join(detected_inputs[:3])}]."
            elif page_url and not is_verified:
                base_precond = f"User is authenticated for {app.name}. Application link '{page_url}' could not be accessed (unverified page context). Derived from requirement specification."
            else:
                base_precond = f"User is authenticated as '{roles[0]}' in {app.name}. Database state active."

            ac_lines = [line.strip() for line in (story.acceptance_criteria or "").split("\n") if line.strip()]
            if not ac_lines:
                ac_lines = [story.description if story.description else f"System must process requirement {story.id} according to rules."]

            for idx, ac in enumerate(ac_lines, start=1):
                clean_ac = RequirementRuleAnalyzer.clean_text(ac)
                ac_code = f"AC-{idx:02d}"
                full_ac_ref = f"{story.id} {ac_code}"

                # Robust Acceptance Criteria Matching against filter
                if not RequirementRuleAnalyzer.matches_ac_filter(story.id, idx, ac, clean_ac, selected_ac_filter):
                    continue

                total_ac_evaluated += 1
                evaluated_story_ids.add(story.id)

                # Synthesize Positive, Negative, and Edge templates from AC semantics
                scenario_templates = RequirementRuleAnalyzer.analyze_requirement(
                    text=ac,
                    ref_code=story.id,
                    story_id=story.id,
                    page_name=page_name or app.name,
                    page_url=page_url,
                    action_btn=action_btn,
                    field_1=field_1,
                    field_2=field_2,
                    roles=roles,
                    is_verified=is_verified
                )

                for tmpl in scenario_templates:
                    # Link awareness integration: reflect verified fields and page context
                    tmpl_steps = list(tmpl.test_steps)
                    tmpl_scenario = tmpl.scenario
                    tmpl_expected = tmpl.expected_result

                    if is_verified and field_1 and tmpl.category == "Positive" and idx == 1:
                        tmpl_scenario = f"[{story.id}] Verify '{action_btn}' Workflow on {page_name}: {clean_ac[:45]}"
                        tmpl_steps = [
                            nav_step,
                            f"2. Authenticate as authorized user role '{roles[0]}'.",
                            f"3. Input valid test data into verified '{field_1}' field."
                        ]
                        if field_2:
                            tmpl_steps.append(f"4. Input valid test data into verified '{field_2}' field.")
                        tmpl_steps.append(f"{len(tmpl_steps)+1}. Click '{action_btn}' button.")
                        tmpl_expected = f"When valid '{field_1}' credentials are submitted on {page_name}, system authenticates '{roles[0]}' successfully, triggers '{action_btn}', and updates state."

                    tc_obj = TestCase(
                        id=f"TC-{tmpl.category[:3].upper()}-TEMP",
                        requirement_ref=full_ac_ref,
                        user_story=story.id,
                        acceptance_criteria=f"{ac_code}: {clean_ac[:60]}",
                        application_page=page_name or (app.name if not page_url else f"Unverified Link ({page_url})"),
                        application_link=page_url,
                        category=tmpl.category,
                        priority=tmpl.priority,
                        scenario=tmpl_scenario,
                        description=tmpl.description,
                        preconditions=base_precond,
                        test_data=tmpl.test_data,
                        test_steps=tmpl_steps,
                        expected_result=tmpl_expected
                    )

                    if tmpl.category == "Positive":
                        positive_cases.append(tc_obj)
                    elif tmpl.category == "Negative":
                        negative_cases.append(tc_obj)
                    else:
                        edge_cases.append(tc_obj)

                # Secondary Role Positive Case if multiple roles exist
                if len(roles) > 1 and idx == 1:
                    secondary_role = roles[1]
                    positive_cases.append(
                        TestCase(
                            id="TC-POS-TEMP",
                            requirement_ref=full_ac_ref,
                            user_story=story.id,
                            acceptance_criteria=f"{ac_code}: {clean_ac[:60]}",
                            application_page=page_name or app.name,
                            application_link=page_url,
                            category="Positive",
                            priority="Medium",
                            scenario=f"[{story.id}] Verify Multi-Role Access ({secondary_role}): {clean_ac[:45]}",
                            description=f"Ensure secondary role '{secondary_role}' can complete operations for {story.id} without permission errors.",
                            preconditions=f"User logged in as '{secondary_role}' on {page_name if page_name else 'application page'}.",
                            test_data=f"Valid Credentials for {secondary_role}",
                            test_steps=[
                                f"1. Log into {app.name} ({page_name if page_name else 'page'}) as '{secondary_role}'.",
                                f"2. Select target module related to {story.title}.",
                                f"3. Submit valid transaction data via '{action_btn}' button.",
                                "4. Verify successful execution."
                            ],
                            expected_result=f"When '{secondary_role}' initiates operation, the system authorizes role permissions, completes workflow smoothly, and records audit trail."
                        )
                    )

        # Multi-Page Workflow End-to-End Case
        if len(successful_contexts) > 1:
            ref_story = stories[0].id if stories else "US-101"
            pages_summary = " → ".join(c.get("name", c.get("page_title", "Page")) for c in successful_contexts[:3])
            
            multi_steps = []
            for i, ctx in enumerate(successful_contexts[:4], start=1):
                p_n = ctx.get("name") or ctx.get("page_title") or f"Page {i}"
                p_u = ctx.get("url", "")
                p_inputs = ctx.get("detected_inputs", [])
                p_actions = ctx.get("detected_actions", [])
                f_name = p_inputs[0] if p_inputs else "required fields"
                btn_name = p_actions[0] if p_actions else "Continue"
                multi_steps.append(f"{i}. Navigate to {p_n} ({p_u}) and fill verified '{f_name}', then click '{btn_name}'.")

            multi_steps.append(f"{len(multi_steps)+1}. Verify complete multi-step journey finishes successfully across all connected pages.")

            positive_cases.append(
                TestCase(
                    id="TC-POS-TEMP",
                    requirement_ref=f"{ref_story} E2E-WORKFLOW",
                    user_story=ref_story,
                    acceptance_criteria="End-to-End Multi-Page User Journey Workflow",
                    application_page=pages_summary,
                    application_link=successful_contexts[0].get("url", ""),
                    category="Positive",
                    priority="High",
                    scenario=f"[{ref_story}] Verify Multi-Page End-to-End Journey ({pages_summary})",
                    description=f"Validate complete user journey passing across multiple verified application pages: {pages_summary}",
                    preconditions=f"User is authenticated for multi-page transaction flow across: {pages_summary}.",
                    test_data="Multi-step End-to-End Journey Payload",
                    test_steps=multi_steps,
                    expected_result="When complete end-to-end journey is executed across connected application pages, the workflow finishes seamlessly and transaction state persists."
                )
            )

        # --- 2. Evaluate Application Business Rules (Generating Positive, Negative, and Edge Cases) ---
        for idx, rule in enumerate(rules, start=1):
            ref_story = stories[0].id if stories else "APP"
            first_ctx = successful_contexts[0] if successful_contexts else (contexts_list[0] if contexts_list else {})
            app_page = first_ctx.get("name", first_ctx.get("page_title", app.name))
            app_url = first_ctx.get("url", "")
            br_ref = f"{ref_story} BR-{idx}"

            # Analyze business rule into individual, scenario-specific Positive, Negative, and Edge test cases
            br_templates = RequirementRuleAnalyzer.analyze_requirement(
                text=rule,
                ref_code=f"BR-{idx}",
                story_id=ref_story,
                page_name=app_page,
                page_url=app_url,
                action_btn="Submit",
                field_1=None,
                field_2=None,
                roles=roles,
                is_verified=bool(successful_contexts)
            )

            for tmpl in br_templates:
                tc_obj = TestCase(
                    id=f"TC-{tmpl.category[:3].upper()}-TEMP",
                    requirement_ref=br_ref,
                    user_story=ref_story,
                    acceptance_criteria=f"BR-{idx}: {rule[:50]}",
                    application_page=app_page,
                    application_link=app_url,
                    category=tmpl.category,
                    priority=tmpl.priority,
                    scenario=tmpl.scenario,
                    description=tmpl.description,
                    preconditions=f"System environment initialized for {app.name}. User authenticated as '{roles[0]}'.",
                    test_data=tmpl.test_data,
                    test_steps=tmpl.test_steps,
                    expected_result=tmpl.expected_result
                )

                if tmpl.category == "Positive":
                    positive_cases.append(tc_obj)
                elif tmpl.category == "Negative":
                    negative_cases.append(tc_obj)
                else:
                    edge_cases.append(tc_obj)

        # Deduplicate across test cases within each category
        positive_cases = deduplication_service.deduplicate(positive_cases)
        negative_cases = deduplication_service.deduplicate(negative_cases)
        edge_cases = deduplication_service.deduplicate(edge_cases)

        # Re-assign sequential IDs
        for i, tc in enumerate(positive_cases, 1):
            tc.id = f"TC-POS-{i:03d}"
        for i, tc in enumerate(negative_cases, 1):
            tc.id = f"TC-NEG-{i:03d}"
        for i, tc in enumerate(edge_cases, 1):
            tc.id = f"TC-EDG-{i:03d}"

        if evaluated_story_ids:
            covered_story_ids = [s.id for s in stories if s.id in evaluated_story_ids]

        total_count = len(positive_cases) + len(negative_cases) + len(edge_cases)
        
        summary = CoverageSummary(
            total_count=total_count,
            positive_count=len(positive_cases),
            negative_count=len(negative_cases),
            edge_count=len(edge_cases),
            user_stories_count=len(covered_story_ids),
            acceptance_criteria_count=total_ac_evaluated,
            application_pages_count=len(successful_contexts),
            application_links_analyzed=[c.get("name") or c.get("page_title") or c.get("url", "") for c in successful_contexts if c.get("name") or c.get("page_title") or c.get("url")],
            requirements_covered=covered_story_ids,
            coverage_quality="Comprehensive Enterprise Coverage (Positive, Negative, and Edge)"
        )

        stories_str = ", ".join(covered_story_ids)
        analysis_summary = (
            f"Batch Analysis for {len(covered_story_ids)} User Stories ({stories_str}) completed against {app.name} business rules. "
            f"Synthesized {total_count} total test cases ({len(positive_cases)} Positive, "
            f"{len(negative_cases)} Negative, {len(edge_cases)} Edge)."
        )

        return TestCaseGenerationResponse(
            positive_test_cases=positive_cases,
            negative_test_cases=negative_cases,
            edge_test_cases=edge_cases,
            coverage_summary=summary,
            analysis_summary=analysis_summary,
            url_context_analyzed=url_analyzed,
            url_analysis_message=url_message
        )

    def generate_test_suite(
        self,
        app: Application,
        story: DevOpsWorkItem,
        req_ref: str,
        url_metadata: Dict[str, Any],
        url_analyzed: bool,
        url_message: str
    ) -> TestCaseGenerationResponse:
        """Backward compatible single-story generation wrapper."""
        return self.generate_multi_requirement_test_suite(
            app=app,
            stories=[story],
            selected_ac_filter=None,
            url_metadata=url_metadata,
            url_analyzed=url_analyzed,
            url_message=url_message
        )


test_generator_engine = TestGeneratorEngine()
