
import unittest
from types import SimpleNamespace
from unittest.mock import Mock

import app.core.model_registry

from app.ai.models import AIArtifact, AIRun
from app.ai.services.matching_retrieval_service import (
    MatchingArtifactNotFound,
    MatchingArtifactInvalid,
    get_saved_matching_report,
)


class TestMatchingRetrievalService(unittest.TestCase):

    def setUp(self):
        self.db = Mock()

        self.requirements = {
            "position_id": 18,
            "position_title": "Assistant Professor in AI",
            "requirements": [
                {
                    "requirement_id": "REQ-001",
                    "category": "DEGREE",
                    "priority": "REQUIRED",
                    "description": "Relevant PhD",
                    "source_excerpt": "Relevant PhD",
                }
            ],
        }

        self.draft = {
            "application_id": 11,
            "position_id": 18,
            "profile_id": 2,
            "matches": [
                {
                    "requirement_id": "REQ-001",
                    "finding": "SUPPORTED",
                    "explanation": "Relevant PhD documented.",
                    "evidence": [
                        {
                            "collection": "degrees",
                            "record_id": 7,
                        }
                    ],
                    "uncertainty": None,
                }
            ],
            "summary": "Provisional assessment.",
            "requires_human_review": True,
        }

        self.artifact = SimpleNamespace(
            id=9,
            run_id=10,
            owner_user_id=5,
            application_id=11,
            artifact_type="ACADEMIC_MATCHING",
            status="REVIEW_REQUIRED",
            payload_json={
                "position_requirements": self.requirements,
                "matching_draft": self.draft,
            },
        )

        self.run = SimpleNamespace(
            id=10,
            user_id=5,
            task_type="ACADEMIC_MATCHING",
            status="SUCCEEDED",
        )

        def get_record(model, record_id):
            if model is AIArtifact and record_id == 9:
                return self.artifact
            if model is AIRun and record_id == 10:
                return self.run
            return None

        self.db.get.side_effect = get_record

    def test_owner_can_retrieve_report(self):
        report = get_saved_matching_report(
            self.db,
            artifact_id=9,
            owner_user_id=5,
        )

        self.assertEqual(report.artifact_id, 9)
        self.assertEqual(report.run_id, 10)
        self.assertEqual(
            report.matching_draft.application_id, 11
        )
        self.assertEqual(
            len(report.requirements.requirements), 1
        )

        self.db.commit.assert_not_called()

    def test_other_candidate_is_denied(self):
        with self.assertRaises(MatchingArtifactNotFound):
            get_saved_matching_report(
                self.db,
                artifact_id=9,
                owner_user_id=7,
            )

    def test_missing_artifact_is_denied(self):
        with self.assertRaises(MatchingArtifactNotFound):
            get_saved_matching_report(
                self.db,
                artifact_id=99999,
                owner_user_id=5,
            )

    def test_wrong_artifact_type_is_denied(self):
        self.artifact.artifact_type = "CV_EXTRACTION"

        with self.assertRaises(MatchingArtifactNotFound):
            get_saved_matching_report(
                self.db,
                artifact_id=9,
                owner_user_id=5,
            )

    def test_failed_ai_run_is_rejected(self):
        self.run.status = "FAILED"

        with self.assertRaises(MatchingArtifactInvalid):
            get_saved_matching_report(
                self.db,
                artifact_id=9,
                owner_user_id=5,
            )

    def test_inconsistent_application_is_rejected(self):
        self.draft["application_id"] = 12

        with self.assertRaises(MatchingArtifactInvalid):
            get_saved_matching_report(
                self.db,
                artifact_id=9,
                owner_user_id=5,
            )

    def test_human_review_cannot_be_disabled(self):
        self.draft["requires_human_review"] = False

        with self.assertRaises(MatchingArtifactInvalid):
            get_saved_matching_report(
                self.db,
                artifact_id=9,
                owner_user_id=5,
            )


if __name__ == "__main__":
    unittest.main()
