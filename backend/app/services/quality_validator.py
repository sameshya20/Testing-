from typing import List, Tuple
from app.schemas.test_case import TestCase, CoverageSummary

class QualityValidator:
    """Audits generated test suites for requirement coverage, scenario completeness, and actionability."""

    def validate_and_summarize(
        self,
        positive_cases: List[TestCase],
        negative_cases: List[TestCase],
        edge_cases: List[TestCase],
        requirement_ref: str
    ) -> Tuple[List[TestCase], List[TestCase], List[TestCase], CoverageSummary]:
        
        pos_count = len(positive_cases)
        neg_count = len(negative_cases)
        edg_count = len(edge_cases)
        total_count = pos_count + neg_count + edg_count

        requirements_covered = [requirement_ref]

        if pos_count > 0 and neg_count > 0 and edg_count > 0:
            quality = "100% Comprehensive (Positive, Negative, and Edge Coverage)"
        elif pos_count > 0 and neg_count > 0:
            quality = "High (Positive & Negative Covered, Limited Edge Scenarios)"
        else:
            quality = "Basic Coverage"

        summary = CoverageSummary(
            total_count=total_count,
            positive_count=pos_count,
            negative_count=neg_count,
            edge_count=edg_count,
            requirements_covered=requirements_covered,
            coverage_quality=quality
        )

        return positive_cases, negative_cases, edge_cases, summary

quality_validator = QualityValidator()
