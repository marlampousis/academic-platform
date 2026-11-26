
import copy
import unittest
from types import SimpleNamespace

from app.ai.schemas.matching import PositionRequirements
from app.ai.schemas.candidate_context import (
    CandidateAcademicContext,
)
from app.ai.services.academic_matching_service import (
    AcademicMatchingService,
    AcademicMatchingError,
)


class FakeRunnable:
    def __init__(self, result):
        self.result = result

    def invoke(self, prompt):
        return copy.deepcopy(self.result)


class TestAcademicMatchingService(unittest.TestCase):

    def setUp(self):
        self.candidate = CandidateAcademicContext.model_validate({
            "profile_id": 2,
            "user_id": 5,
            "degrees": [
                {
                    "id": 7,
                    "degree_type": "PhD",
                    "title": "PhD in Computer Science",
                    "institution_name": "Example University",
                }
            ],
            "publications": [],
            "research_projects": [],
            "teaching_experience": [],
        })

        self.context = SimpleNamespace(
            application_id=11,
            position=SimpleNamespace(
                position_id=18,
                title="Assistant Professor in AI",
            ),
            candidate=self.candidate,
        )

        self.requirements = PositionRequirements.model_validate({
            "position_id": 18,
            "position_title": "Assistant Professor in AI",
            "requirements": [
                {
                    "requirement_id": "REQ-001",
                    "category": "DEGREE",
                    "priority": "REQUIRED",
                    "description": "PhD in Computer Science",
                    "source_excerpt": "PhD in Computer Science",
                }
            ],
        })

    def valid_result(self):
        return {
            "application_id": 999,
            "position_id": 999,
            "profile_id": 999,
            "summary": "Candidate has a relevant PhD.",
            "requires_human_review": True,
            "matches": [
                {
                    "requirement_id": "REQ-001",
                    "finding": "SUPPORTED",
                    "explanation": "Relevant PhD is listed.",
                    "evidence": [
                        {
                            "collection": "degrees",
                            "record_id": 7,
                        }
                    ],
                }
            ],
        }

    def run_match(self, result):
        return AcademicMatchingService(
            FakeRunnable(result)
        ).match(
            context=self.context,
            requirements=self.requirements,
        )

    def test_valid_matching_draft(self):
        result = self.run_match(self.valid_result())

        self.assertEqual(result.application_id, 11)
        self.assertEqual(result.position_id, 18)
        self.assertEqual(result.profile_id, 2)
        self.assertEqual(len(result.matches), 1)

    def test_other_candidate_evidence_rejected(self):
        result = self.valid_result()
        result["matches"][0]["evidence"][0][
            "record_id"
        ] = 999

        with self.assertRaises(AcademicMatchingError):
            self.run_match(result)

    def test_missing_requirement_rejected(self):
        result = self.valid_result()
        result["matches"] = []

        with self.assertRaises(AcademicMatchingError):
            self.run_match(result)

    def test_supported_finding_without_evidence_rejected(self):
        result = self.valid_result()
        result["matches"][0]["evidence"] = []

        with self.assertRaises(AcademicMatchingError):
            self.run_match(result)

    def test_insufficient_evidence_allowed(self):
        result = self.valid_result()
        result["matches"][0]["finding"] = (
            "INSUFFICIENT_EVIDENCE"
        )
        result["matches"][0]["evidence"] = []
        result["matches"][0]["uncertainty"] = (
            "Degree information is incomplete."
        )

        output = self.run_match(result)

        self.assertEqual(
            output.matches[0].finding.value,
            "INSUFFICIENT_EVIDENCE",
        )

    def test_human_review_is_required(self):
        result = self.valid_result()
        result["requires_human_review"] = False

        with self.assertRaises(AcademicMatchingError):
            self.run_match(result)

    def test_mismatched_position_rejected(self):
        self.requirements.position_id = 17

        with self.assertRaises(ValueError):
            self.run_match(self.valid_result())


    def test_insufficient_evidence_requires_explanation(self):
        result = self.valid_result()

        result["matches"][0]["finding"] = (
            "INSUFFICIENT_EVIDENCE"
        )
        result["matches"][0]["evidence"] = []
        result["matches"][0]["uncertainty"] = None

        with self.assertRaises(AcademicMatchingError):
            self.run_match(result)

    def test_partial_support_requires_uncertainty(self):
        result = self.valid_result()

        result["matches"][0]["finding"] = (
            "PARTIALLY_SUPPORTED"
        )
        result["matches"][0]["uncertainty"] = "   "

        with self.assertRaises(AcademicMatchingError):
            self.run_match(result)

    def test_duplicate_evidence_reference_rejected(self):
        result = self.valid_result()

        result["matches"][0]["evidence"].append({
            "collection": "degrees",
            "record_id": 7,
        })

        with self.assertRaises(AcademicMatchingError):
            self.run_match(result)

    def test_unsupported_requires_uncertainty_explanation(self):
        result = self.valid_result()

        result["matches"][0]["finding"] = "UNSUPPORTED"
        result["matches"][0]["uncertainty"] = None

        with self.assertRaises(AcademicMatchingError):
            self.run_match(result)

    def test_unsupported_with_explanation_allowed(self):
        result = self.valid_result()

        result["matches"][0]["finding"] = "UNSUPPORTED"
        result["matches"][0]["uncertainty"] = (
            "Available records suggest a different "
            "specialization. Related-field eligibility "
            "requires human assessment."
        )

        output = self.run_match(result)

        self.assertEqual(
            output.matches[0].finding.value,
            "UNSUPPORTED",
        )

if __name__ == "__main__":
    unittest.main()
