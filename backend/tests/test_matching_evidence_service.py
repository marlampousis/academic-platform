
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from app.ai.schemas.candidate_context import (
    DegreeEvidence,
)
from app.ai.services.candidate_context_service import (
    CandidateProfileAccessDenied,
)
from app.ai.services.matching_retrieval_service import (
    MatchingArtifactInvalid,
)
from app.ai.services.matching_evidence_service import (
    get_matching_evidence_details,
)


MODULE = "app.ai.services.matching_evidence_service"


class TestMatchingEvidenceService(unittest.TestCase):

    def setUp(self):
        self.db = Mock()

        self.reference = SimpleNamespace(
            collection="degrees",
            record_id=7,
        )

        self.report = SimpleNamespace(
            artifact_id=9,
            matching_draft=SimpleNamespace(
                application_id=11,
                profile_id=2,
                matches=[
                    SimpleNamespace(
                        requirement_id="REQ-001",
                        evidence=[self.reference],
                    )
                ],
            ),
        )

        self.context = SimpleNamespace(
            profile_id=2,
            user_id=5,
            degrees=[
                DegreeEvidence(
                    id=7,
                    degree_type="PhD",
                    title="PhD in Computer Science",
                    institution_name="University of Edinburgh",
                )
            ],
            publications=[],
            research_projects=[],
            teaching_experience=[],
        )

    def resolve(self):
        with (
            patch(
                MODULE + ".get_saved_matching_report",
                return_value=self.report,
            ),
            patch(
                MODULE + ".get_candidate_academic_context",
                return_value=self.context,
            ),
        ):
            return get_matching_evidence_details(
                self.db,
                artifact_id=9,
                owner_user_id=5,
            )

    def test_resolves_real_degree_title(self):
        result = self.resolve()

        evidence = result["matches"][0]["evidence"][0]

        self.assertTrue(evidence["available"])
        self.assertEqual(evidence["record_id"], 7)
        self.assertEqual(
            evidence["title"],
            "PhD in Computer Science",
        )
        self.assertEqual(
            evidence["details"]["institution_name"],
            "University of Edinburgh",
        )

        self.db.commit.assert_not_called()

    def test_deleted_record_is_identified(self):
        self.context.degrees = []

        result = self.resolve()
        evidence = result["matches"][0]["evidence"][0]

        self.assertFalse(evidence["available"])
        self.assertIsNone(evidence["details"])

    def test_wrong_profile_identity_rejected(self):
        self.context.profile_id = 999

        with self.assertRaises(MatchingArtifactInvalid):
            self.resolve()

    def test_profile_access_denied(self):
        with (
            patch(
                MODULE + ".get_saved_matching_report",
                return_value=self.report,
            ),
            patch(
                MODULE + ".get_candidate_academic_context",
                side_effect=CandidateProfileAccessDenied(),
            ),
        ):
            with self.assertRaises(MatchingArtifactInvalid):
                get_matching_evidence_details(
                    self.db,
                    artifact_id=9,
                    owner_user_id=5,
                )

    def test_only_cited_records_are_returned(self):
        self.context.degrees.append(
            DegreeEvidence(
                id=8,
                degree_type="MSc",
                title="Uncited Degree",
                institution_name="Example University",
            )
        )

        result = self.resolve()
        evidence = result["matches"][0]["evidence"]

        self.assertEqual(len(evidence), 1)
        self.assertEqual(evidence[0]["record_id"], 7)


if __name__ == "__main__":
    unittest.main()
