
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient

from app.main import app
from app.core.database import get_db
from app.users.router import get_current_user
from app.ai.schemas.matching import AcademicMatchingDraft


ENDPOINT_11 = "/ai/applications/11/matching-drafts"
ENDPOINT_12 = "/ai/applications/12/matching-drafts"


class TestAIMatchingRouter(unittest.TestCase):

    def setUp(self):
        self.db = Mock()

        app.dependency_overrides[get_db] = (
            lambda: self.db
        )

        self.client = TestClient(app)

    def tearDown(self):
        app.dependency_overrides.clear()
        self.client.close()

    def authenticate(self, user_id, role="CANDIDATE"):
        fake_user = SimpleNamespace(
            id=user_id,
            role=SimpleNamespace(code=role),
        )

        app.dependency_overrides[get_current_user] = (
            lambda: fake_user
        )

    def mock_application(
        self,
        application_id,
        owner_id,
        status="DRAFT",
    ):
        self.db.get.return_value = SimpleNamespace(
            id=application_id,
            user_id=owner_id,
            status=status,
        )

    def test_unauthenticated_access_rejected(self):
        response = self.client.post(ENDPOINT_11)

        self.assertIn(
            response.status_code,
            (401, 403),
        )

    def test_alex_cannot_access_daniel_application(self):
        self.authenticate(user_id=5)
        self.mock_application(12, owner_id=7)

        response = self.client.post(ENDPOINT_12)

        self.assertEqual(response.status_code, 404)

    def test_daniel_cannot_access_alex_application(self):
        self.authenticate(user_id=7)
        self.mock_application(11, owner_id=5)

        response = self.client.post(ENDPOINT_11)

        self.assertEqual(response.status_code, 404)

    def test_missing_application_returns_404(self):
        self.authenticate(user_id=5)
        self.db.get.return_value = None

        response = self.client.post(
            "/ai/applications/999/matching-drafts"
        )

        self.assertEqual(response.status_code, 404)

    def test_reviewer_cannot_access_candidate_endpoint(self):
        self.authenticate(user_id=7, role="REVIEWER")
        self.mock_application(12, owner_id=7)

        response = self.client.post(ENDPOINT_12)

        self.assertEqual(response.status_code, 403)
        self.db.get.assert_not_called()

    def test_non_draft_application_rejected(self):
        self.authenticate(user_id=5)
        self.mock_application(
            11,
            owner_id=5,
            status="SUBMITTED",
        )

        response = self.client.post(ENDPOINT_11)

        self.assertEqual(response.status_code, 409)

    def test_authorized_candidate_reaches_matching(self):
        self.authenticate(user_id=5)
        self.mock_application(11, owner_id=5)

        context = SimpleNamespace(
            application_id=11,
            position=SimpleNamespace(position_id=18),
        )

        requirements = SimpleNamespace(
            requirements=[SimpleNamespace(
                requirement_id="REQ-001"
            )],
        )

        draft = AcademicMatchingDraft.model_validate({
            "application_id": 11,
            "position_id": 18,
            "profile_id": 2,
            "matches": [
                {
                    "requirement_id": "REQ-001",
                    "finding": "INSUFFICIENT_EVIDENCE",
                    "explanation": (
                        "Evidence requires human review."
                    ),
                    "evidence": [],
                    "uncertainty": (
                        "The available records are incomplete."
                    ),
                }
            ],
            "summary": "Provisional matching preview.",
            "requires_human_review": True,
        })

        matching_service = Mock()
        matching_service.match.return_value = draft

        with (
            patch(
                "app.ai.matching_router."
                "get_application_matching_context",
                return_value=context,
            ),
            patch(
                "app.ai.matching_router."
                "create_gemini_requirements_service",
                return_value=Mock(),
            ),
            patch(
                "app.ai.matching_router."
                "extract_requirements_for_position",
                return_value=requirements,
            ),
            patch(
                "app.ai.matching_router."
                "create_matching_service",
                return_value=matching_service,
            ),
            patch(
                "app.ai.matching_router.start_matching_run",
                return_value=42,
            ) as start_run,
            patch(
                "app.ai.matching_router.complete_matching_run",
                return_value=77,
            ) as complete_run,
        ):
            response = self.client.post(ENDPOINT_11)

        self.assertEqual(
            response.status_code,
            200,
            response.text,
        )

        payload = response.json()

        self.assertEqual(payload["application_id"], 11)
        self.assertEqual(payload["position_id"], 18)
        self.assertEqual(payload["profile_id"], 2)
        self.assertTrue(payload["requires_human_review"])

        matching_service.match.assert_called_once()

        start_run.assert_called_once()
        complete_run.assert_called_once()

        self.assertEqual(
            complete_run.call_args.kwargs["application_id"],
            11,
        )

        self.assertEqual(
            complete_run.call_args.kwargs["user_id"],
            5,
        )


    def test_owner_can_list_saved_matching_reports(self):
        self.authenticate(user_id=5)
        self.mock_application(11, owner_id=5)

        saved_reports = [
            {
                "artifact_id": 9,
                "run_id": 10,
                "application_id": 11,
                "status": "REVIEW_REQUIRED",
                "created_at": "2026-11-22T22:57:26",
            }
        ]

        with patch(
            "app.ai.matching_router.list_saved_matching_reports",
            return_value=saved_reports,
        ) as list_reports:
            response = self.client.get(
                "/ai/applications/11/matching-artifacts"
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()[0]["artifact_id"],
            9,
        )
        list_reports.assert_called_once_with(
            self.db,
            application_id=11,
            owner_user_id=5,
        )

    def test_alex_cannot_list_daniel_saved_reports(self):
        self.authenticate(user_id=5)
        self.mock_application(12, owner_id=7)

        with patch(
            "app.ai.matching_router.list_saved_matching_reports"
        ) as list_reports:
            response = self.client.get(
                "/ai/applications/12/matching-artifacts"
            )

        self.assertEqual(response.status_code, 404)
        list_reports.assert_not_called()

    def test_unauthenticated_saved_report_list_rejected(self):
        response = self.client.get(
            "/ai/applications/11/matching-artifacts"
        )

        self.assertIn(
            response.status_code,
            (401, 403),
        )

    def test_missing_application_cannot_list_reports(self):
        self.authenticate(user_id=5)
        self.db.get.return_value = None

        with patch(
            "app.ai.matching_router.list_saved_matching_reports"
        ) as list_reports:
            response = self.client.get(
                "/ai/applications/999/matching-artifacts"
            )

        self.assertEqual(response.status_code, 404)
        list_reports.assert_not_called()


    def test_owner_can_read_matching_evidence(self):
        self.authenticate(user_id=5)

        expected = {
            "artifact_id": 9,
            "application_id": 11,
            "profile_id": 2,
            "evidence_source": "CURRENT_DATABASE_RECORDS",
            "matches": [
                {
                    "requirement_id": "REQ-001",
                    "evidence": [
                        {
                            "collection": "degrees",
                            "record_id": 7,
                            "available": True,
                            "title": "PhD in Computer Science",
                            "details": {
                                "id": 7,
                                "title": "PhD in Computer Science",
                                "institution_name": "University of Edinburgh",
                            },
                        }
                    ],
                }
            ],
        }

        with patch(
            "app.ai.matching_router.get_matching_evidence_details",
            return_value=expected,
        ) as service:
            response = self.client.get(
                "/ai/matching-artifacts/9/evidence"
            )

        self.assertEqual(
            response.status_code,
            200,
            response.text,
        )
        self.assertEqual(response.json(), expected)

        service.assert_called_once_with(
            self.db,
            artifact_id=9,
            owner_user_id=5,
        )

    def test_other_candidate_evidence_is_denied(self):
        self.authenticate(user_id=7)

        from app.ai.services.matching_retrieval_service import (
            MatchingArtifactNotFound,
        )

        with patch(
            "app.ai.matching_router.get_matching_evidence_details",
            side_effect=MatchingArtifactNotFound(),
        ):
            response = self.client.get(
                "/ai/matching-artifacts/9/evidence"
            )

        self.assertEqual(response.status_code, 404)

    def test_unauthenticated_evidence_request_rejected(self):
        response = self.client.get(
            "/ai/matching-artifacts/9/evidence"
        )

        self.assertIn(
            response.status_code,
            (401, 403),
        )

    def test_invalid_evidence_artifact_id_rejected(self):
        self.authenticate(user_id=5)

        with patch(
            "app.ai.matching_router.get_matching_evidence_details"
        ) as service:
            response = self.client.get(
                "/ai/matching-artifacts/0/evidence"
            )

        self.assertEqual(response.status_code, 422)
        service.assert_not_called()


    def test_matching_failure_records_failed_run(self):
        self.authenticate(user_id=5)
        self.mock_application(11, owner_id=5)

        with (
            patch(
                "app.ai.matching_router.start_matching_run",
                return_value=42,
            ) as start_run,
            patch(
                "app.ai.matching_router."
                "get_application_matching_context",
                side_effect=RuntimeError("Simulated AI workflow failure"),
            ),
            patch(
                "app.ai.matching_router.complete_matching_run",
            ) as complete_run,
            patch(
                "app.ai.matching_router.fail_matching_run",
            ) as fail_run,
        ):
            response = self.client.post(ENDPOINT_11)

        self.assertEqual(response.status_code, 502)
        self.assertEqual(
            response.json()["detail"],
            "AI matching failed or evidence was invalid",
        )

        start_run.assert_called_once()
        complete_run.assert_not_called()
        fail_run.assert_called_once()

        self.assertEqual(
            fail_run.call_args.kwargs["run_id"],
            42,
        )
        self.assertEqual(
            fail_run.call_args.kwargs["error_code"],
            "MATCHING_PROCESSING_ERROR",
        )

    def test_matching_audit_start_failure_stops_workflow(self):
        self.authenticate(user_id=5)
        self.mock_application(11, owner_id=5)

        from app.ai.services.matching_persistence_service import (
            MatchingPersistenceError,
        )

        with (
            patch(
                "app.ai.matching_router.start_matching_run",
                side_effect=MatchingPersistenceError(
                    "Simulated audit start failure"
                ),
            ),
            patch(
                "app.ai.matching_router."
                "get_application_matching_context",
            ) as load_context,
            patch(
                "app.ai.matching_router.complete_matching_run",
            ) as complete_run,
        ):
            response = self.client.post(ENDPOINT_11)

        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            response.json()["detail"],
            "Could not initialize matching audit",
        )

        load_context.assert_not_called()
        complete_run.assert_not_called()

    def test_matching_failure_audit_failure_returns_500(self):
        self.authenticate(user_id=5)
        self.mock_application(11, owner_id=5)

        from app.ai.services.matching_persistence_service import (
            MatchingPersistenceError,
        )

        with (
            patch(
                "app.ai.matching_router.start_matching_run",
                return_value=42,
            ),
            patch(
                "app.ai.matching_router."
                "get_application_matching_context",
                side_effect=RuntimeError(
                    "Simulated matching failure"
                ),
            ),
            patch(
                "app.ai.matching_router.fail_matching_run",
                side_effect=MatchingPersistenceError(
                    "Simulated failure recording error"
                ),
            ) as fail_run,
            patch(
                "app.ai.matching_router.complete_matching_run",
            ) as complete_run,
        ):
            response = self.client.post(ENDPOINT_11)

        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            response.json()["detail"],
            "Could not finalize matching audit",
        )

        fail_run.assert_called_once()
        complete_run.assert_not_called()

if __name__ == "__main__":
    unittest.main()