
import unittest
from unittest.mock import patch
from uuid import uuid4

import app.core.model_registry

from jose import jwt
from sqlalchemy import select

from app.core.config import settings
from app.users.models import User
from app.roles.models import Role
from app.ai.models import AIRun, AIArtifact, AIEvidence
from app.ai.schemas.extraction import (
    AcademicCVExtraction,
    ExtractedDegree,
    EvidenceReference,
)
from app.ai.services.extraction_service import AIExtractionError

from db_setup import isolated_api_client


CV_TEXT = (
    "Alex Morgan received a PhD in Computer Science "
    "from Example University in 2022."
)


def create_candidate(db):
    role_id = db.execute(
        select(Role.id).where(Role.code == "CANDIDATE")
    ).scalar_one()

    user = User(
        first_name="AI",
        last_name="Candidate",
        email=f"candidate-{uuid4().hex}@example.test",
        hashed_password="integration-test-only",
        role_id=role_id,
    )

    db.add(user)
    db.flush()

    return user


def auth_headers(user):
    token = jwt.encode(
        {"sub": str(user.id)},
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
    return {"Authorization": f"Bearer {token}"}


class FakeExtractionService:
    def extract(self, cv_text, source_id):
        return AcademicCVExtraction(
            specialization="Artificial Intelligence",
            degrees=[
                ExtractedDegree(
                    degree_type="PhD",
                    title="PhD in Computer Science",
                    institution_name="Example University",
                    end_year=2022,
                    evidence=[
                        EvidenceReference(
                            source_id=source_id,
                            excerpt="PhD in Computer Science",
                        )
                    ],
                )
            ],
        )


class TestAIExtractionAPI(unittest.TestCase):

    def test_post_creates_extraction_draft(self):
        with isolated_api_client() as (client, db):
            user = create_candidate(db)

            with patch(
                "app.ai.router.create_gemini_extraction_service",
                return_value=FakeExtractionService(),
            ):
                response = client.post(
                    "/ai/extractions",
                    headers=auth_headers(user),
                    json={"cv_text": CV_TEXT},
                )

            self.assertEqual(
                response.status_code,
                201,
                response.text,
            )

            body = response.json()

            self.assertEqual(
                body["status"],
                "REVIEW_REQUIRED",
            )
            self.assertEqual(
                body["extraction"]["degrees"][0]["end_year"],
                2022,
            )

            artifact = db.get(
                AIArtifact,
                body["artifact_id"],
            )
            run = db.get(AIRun, body["run_id"])

            self.assertIsNotNone(artifact)
            self.assertIsNotNone(run)
            self.assertEqual(artifact.owner_user_id, user.id)
            self.assertEqual(run.status, "SUCCEEDED")

            evidence = db.execute(
                select(AIEvidence).where(
                    AIEvidence.artifact_id == artifact.id
                )
            ).scalars().all()

            self.assertEqual(len(evidence), 1)

    def test_get_returns_own_extraction(self):
        with isolated_api_client() as (client, db):
            user = create_candidate(db)
            headers = auth_headers(user)

            with patch(
                "app.ai.router.create_gemini_extraction_service",
                return_value=FakeExtractionService(),
            ):
                created = client.post(
                    "/ai/extractions",
                    headers=headers,
                    json={"cv_text": CV_TEXT},
                )

            self.assertEqual(created.status_code, 201)

            artifact_id = created.json()["artifact_id"]

            response = client.get(
                f"/ai/extractions/{artifact_id}",
                headers=headers,
            )

            self.assertEqual(response.status_code, 200)
            self.assertEqual(
                response.json()["status"],
                "REVIEW_REQUIRED",
            )

    def test_another_candidate_cannot_read_artifact(self):
        with isolated_api_client() as (client, db):
            owner = create_candidate(db)
            other = create_candidate(db)

            with patch(
                "app.ai.router.create_gemini_extraction_service",
                return_value=FakeExtractionService(),
            ):
                created = client.post(
                    "/ai/extractions",
                    headers=auth_headers(owner),
                    json={"cv_text": CV_TEXT},
                )

            self.assertEqual(created.status_code, 201)

            artifact_id = created.json()["artifact_id"]

            response = client.get(
                f"/ai/extractions/{artifact_id}",
                headers=auth_headers(other),
            )

            self.assertEqual(response.status_code, 404)

    def test_unauthenticated_request_is_rejected(self):
        with isolated_api_client() as (client, db):
            response = client.post(
                "/ai/extractions",
                json={"cv_text": CV_TEXT},
            )

            # Current FastAPI/HTTPBearer behavior may return
            # 401 or 403 depending on the installed version.
            self.assertIn(response.status_code, (401, 403))

    def test_empty_cv_is_rejected(self):
        with isolated_api_client() as (client, db):
            user = create_candidate(db)

            response = client.post(
                "/ai/extractions",
                headers=auth_headers(user),
                json={"cv_text": "   "},
            )

            self.assertEqual(response.status_code, 422)

    def test_gemini_failure_returns_502(self):
        with isolated_api_client() as (client, db):
            user = create_candidate(db)

            failing_service = FakeExtractionService()

            # Simulate a Gemini provider failure.
            with patch.object(
                failing_service,
                "extract",
                side_effect=AIExtractionError(
                    "Simulated provider failure"
                ),
            ):
                with patch(
                    "app.ai.router.create_gemini_extraction_service",
                    return_value=failing_service,
                ):
                    with self.assertLogs(
                        "app.ai.router",
                        level="WARNING",
                    ) as captured_logs:
                        response = client.post(
                            "/ai/extractions",
                            headers=auth_headers(user),
                            json={"cv_text": CV_TEXT},
                        )

            # 1. Verify the HTTP error response.
            self.assertEqual(response.status_code, 502)
            self.assertEqual(
                response.json()["detail"],
                "AI extraction failed or evidence was invalid",
            )

            # 2. Verify the failure was logged.
            self.assertTrue(
                any(
                    "AI run" in message
                    and "AI_EXTRACTION_ERROR" in message
                    for message in captured_logs.output
                )
            )

            # 3. Verify the failed AI run was saved in PostgreSQL.
            failed_runs = db.execute(
                select(AIRun).where(
                    AIRun.user_id == user.id,
                    AIRun.status == "FAILED",
                )
            ).scalars().all()

            self.assertEqual(len(failed_runs), 1)

            failed_run = failed_runs[0]

            # 4. Verify execution metadata.
            self.assertEqual(
                failed_run.error_code,
                "AI_EXTRACTION_ERROR",
            )
            self.assertIsNotNone(failed_run.completed_at)
            self.assertIsNotNone(failed_run.latency_ms)
            self.assertGreaterEqual(failed_run.latency_ms, 0)

            # 5. A failed extraction must not create an artifact.
            artifacts = db.execute(
                select(AIArtifact).where(
                    AIArtifact.run_id == failed_run.id
                )
            ).scalars().all()

            self.assertEqual(len(artifacts), 0)

    def test_invalid_source_evidence_is_rejected(self):
        with isolated_api_client() as (client, db):
            user = create_candidate(db)

            class InvalidEvidenceService:
                def extract(self, cv_text, source_id):
                    return AcademicCVExtraction(
                        specialization="Artificial Intelligence",
                        degrees=[
                            ExtractedDegree(
                                degree_type="PhD",
                                title="PhD in Computer Science",
                                institution_name="Example University",
                                end_year=2022,
                                evidence=[
                                    EvidenceReference(
                                        source_id=source_id,
                                        excerpt=(
                                            "This qualification does not "
                                            "appear in the source CV"
                                        ),
                                    )
                                ],
                            )
                        ],
                    )

            with patch(
                "app.ai.router.create_gemini_extraction_service",
                return_value=InvalidEvidenceService(),
            ):
                response = client.post(
                    "/ai/extractions",
                    headers=auth_headers(user),
                    json={"cv_text": CV_TEXT},
                )

            self.assertEqual(response.status_code, 502)

            artifacts = db.execute(
                select(AIArtifact).where(
                    AIArtifact.owner_user_id == user.id
                )
            ).scalars().all()

            self.assertEqual(len(artifacts), 0)

    def test_invalid_token_rejected(self):
        with isolated_api_client() as (client, db):
            response = client.get(
                "/ai/extractions/1",
                headers={
                    "Authorization": "Bearer invalid.jwt.token"
                },
            )

            self.assertEqual(response.status_code, 401)

    def test_reviewer_cannot_access_candidate_extractions(self):
        with isolated_api_client() as (client, db):
            reviewer = create_candidate(db)

            reviewer.role_id = db.execute(
                select(Role.id).where(Role.code == "REVIEWER")
            ).scalar_one()
            db.flush()

            headers = auth_headers(reviewer)

            post_response = client.post(
                "/ai/extractions",
                headers=headers,
                json={"cv_text": CV_TEXT},
            )

            get_response = client.get(
                "/ai/extractions/1",
                headers=headers,
            )

            self.assertEqual(post_response.status_code, 403)
            self.assertEqual(get_response.status_code, 403)

    def test_persistence_failure_records_failed_run(self):
        with isolated_api_client() as (client, db):
            user = create_candidate(db)

            with patch(
                "app.ai.router.create_gemini_extraction_service",
                return_value=FakeExtractionService(),
            ):
                with patch(
                    "app.ai.router.save_extraction_artifact",
                    side_effect=RuntimeError(
                        "Simulated database persistence failure"
                    ),
                ):
                    with self.assertLogs(
                        "app.ai.router",
                        level="ERROR",
                    ):
                        response = client.post(
                            "/ai/extractions",
                            headers=auth_headers(user),
                            json={"cv_text": CV_TEXT},
                        )

            # API should return a controlled error.
            self.assertEqual(response.status_code, 500)
            self.assertEqual(
                response.json()["detail"],
                "Could not save AI extraction",
            )

            # The AI run should be marked FAILED.
            runs = db.execute(
                select(AIRun).where(
                    AIRun.user_id == user.id,
                )
            ).scalars().all()

            self.assertEqual(len(runs), 1)

            run = runs[0]

            self.assertEqual(run.status, "FAILED")
            self.assertEqual(
                run.error_code,
                "PERSISTENCE_ERROR",
            )
            self.assertIsNotNone(run.completed_at)
            self.assertIsNotNone(run.latency_ms)

            # No artifact should have been saved.
            artifacts = db.execute(
                select(AIArtifact).where(
                    AIArtifact.run_id == run.id,
                )
            ).scalars().all()

            self.assertEqual(len(artifacts), 0)

    def test_extraction_does_not_modify_official_records(self):
        from sqlalchemy import text

        with isolated_api_client() as (client, db):
            user = create_candidate(db)

            official_tables = (
                "degrees",
                "publications",
                "research_projects",
                "teaching_experience",
            )

            def record_counts():
                return {
                    table: db.execute(
                        text(f"SELECT COUNT(*) FROM {table}")
                    ).scalar_one()
                    for table in official_tables
                }

            before = record_counts()

            with patch(
                "app.ai.router.create_gemini_extraction_service",
                return_value=FakeExtractionService(),
            ):
                response = client.post(
                    "/ai/extractions",
                    headers=auth_headers(user),
                    json={"cv_text": CV_TEXT},
                )

            self.assertEqual(
                response.status_code,
                201,
                response.text,
            )

            after = record_counts()

            self.assertEqual(
                before,
                after,
                "AI extraction modified official academic records",
            )

            artifact = db.get(
                AIArtifact,
                response.json()["artifact_id"],
            )

            self.assertIsNotNone(artifact)
            self.assertEqual(
                artifact.status,
                "REVIEW_REQUIRED",
            )

if __name__ == "__main__":
    unittest.main()
