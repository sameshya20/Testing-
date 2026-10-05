from typing import List
from difflib import SequenceMatcher
from app.schemas.test_case import TestCase

class DeduplicationService:
    """Detects exact duplicates and consolidates semantically identical test cases while preserving distinct scenario conditions."""

    def _similarity_ratio(self, str1: str, str2: str) -> float:
        return SequenceMatcher(None, str1.lower().strip(), str2.lower().strip()).ratio()

    def deduplicate(self, test_cases: List[TestCase], threshold: float = 0.88) -> List[TestCase]:
        """Filters out truly redundant test scenarios while preserving distinct boundary conditions, test inputs, and expected outcomes."""
        unique_cases: List[TestCase] = []

        for tc in test_cases:
            is_duplicate = False
            for existing in unique_cases:
                # Test cases in different categories are never duplicates
                if tc.category != existing.category:
                    continue

                # Test cases for different user stories are never duplicates
                if tc.user_story and existing.user_story and tc.user_story.strip().upper() != existing.user_story.strip().upper():
                    continue

                # Exact duplicates by requirement_ref and scenario
                if tc.requirement_ref and existing.requirement_ref and tc.requirement_ref == existing.requirement_ref and tc.scenario.strip().lower() == existing.scenario.strip().lower():
                    is_duplicate = True
                    break

                # Compare scenario, description, test_data, and expected_result
                scenario_sim = self._similarity_ratio(tc.scenario, existing.scenario)
                desc_sim = self._similarity_ratio(tc.description, existing.description)
                data_sim = self._similarity_ratio(tc.test_data, existing.test_data)
                exp_sim = self._similarity_ratio(tc.expected_result, existing.expected_result)

                # Distinct inputs or distinct expected results represent distinct test scenarios (e.g. boundary values)
                if data_sim < 0.80 or exp_sim < 0.80:
                    continue

                # Duplicate if scenarios and expected outcomes are both virtually identical
                if (scenario_sim >= threshold and exp_sim >= 0.85) or (scenario_sim > 0.75 and desc_sim > 0.80 and exp_sim > 0.85 and data_sim > 0.85):
                    is_duplicate = True
                    break

            if not is_duplicate:
                unique_cases.append(tc)

        # Re-index unique test case IDs sequentially
        for idx, tc in enumerate(unique_cases, start=1):
            category_prefix = tc.category[:3].upper()
            tc.id = f"TC-{category_prefix}-{idx:03d}"

        return unique_cases

deduplication_service = DeduplicationService()
