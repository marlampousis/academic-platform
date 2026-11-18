
import unittest

import app.core.model_registry

from uuid import uuid4
from app.roles.models import Role

from sqlalchemy import func, select
from sqlalchemy.orm import configure_mappers

from app.ai.models import AIRun, AIArtifact, AIEvidence
from app.ai.schemas.extraction import (
    AcademicCVExtraction,
    ExtractedDegree,
    EvidenceReference,
)
from app.ai.services.persistence_service import (
    AIArtifactNotFound,
    create_ai_run,
    save_extraction_artifact,
    get_extraction_artifact,
)
from app.users.models import User

from db_setup import (
    isolated_test_session,
    verify_test_database,
    test_engine,
)


SOURCE_ID = "s02-synthetic-cv"

CV_TEXT = (
    "Alex Morgan received a PhD in Computer Science "
    "from Example University in 2022."
)

def sample_extraction():
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
                        source_id=SOURCE_ID,
                        excerpt="PhD in Computer Science",
                    )
                ],
            )
        ],
    )



def get_two_users(db):
    """
    Create two temporary test users inside the active
    rollback-protected integration-test transaction.

    No existing user records are required.
    """
    role_id = db.execute(
        select(Role.id).order_by(Role.id).limit(1)
    ).scalar_one_or_none()

    if role_id is None:
        raise AssertionError(
            "Test database has no roles. Seed test roles first."
        )

    unique_id = uuid4().hex

    owner = User(
        first_name="AI",
        last_name="TestOwner",
        email=f"ai-owner-{unique_id}@example.test",
        hashed_password="not-a-real-password",
        role_id=role_id,
    )

    other_user = User(
        first_name="AI",
        last_name="TestOther",
        email=f"ai-other-{unique_id}@example.test",
        hashed_password="not-a-real-password",
        role_id=role_id,
    )

    db.add_all([owner, other_user])
    db.flush()

    return owner.id, other_user.id


def make_successful_run(db, user_id):
    run = create_ai_run(
        db,
        user_id=user_id,
        task_type="CV_EXTRACTION",
        provider="gemini",
        model_name="gemini-3.5-flash-lite",
    )

    run.status = "SUCCEEDED"
    return run


class TestAIPersistence(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        verify_test_database()
        configure_mappers()

    def test_create_ai_run(self):
        with isolated_test_session() as db:
            user_id, _ = get_two_users(db)

            run = create_ai_run(
                db,
                user_id=user_id,
                task_type="CV_EXTRACTION",
                provider="gemini",
                model_name="gemini-3.5-flash-lite",
            )

            self.assertIsNotNone(run.id)
            self.assertEqual(run.status, "PENDING")
            self.assertEqual(run.user_id, user_id)

    def test_save_and_read_extraction(self):
        with isolated_test_session() as db:
            user_id, _ = get_two_users(db)

            run = make_successful_run(db, user_id)

            artifact = save_extraction_artifact(
                db,
                run=run,
                owner_user_id=user_id,
                extraction=sample_extraction(),
                source_id=SOURCE_ID,
                cv_text=CV_TEXT,
            )

            saved = get_extraction_artifact(
                db,
                artifact_id=artifact.id,
                owner_user_id=user_id,
            )

            self.assertEqual(saved.status, "REVIEW_REQUIRED")
            self.assertEqual(saved.artifact_type, "CV_EXTRACTION")
            self.assertEqual(
                saved.payload_json["degrees"][0]["end_year"],
                2022,
            )

            evidence = db.execute(
                select(AIEvidence).where(
                    AIEvidence.artifact_id == artifact.id
                )
            ).scalars().all()

            self.assertEqual(len(evidence), 1)
            self.assertEqual(evidence[0].source_id, SOURCE_ID)
            self.assertFalse(evidence[0].verified)

    def test_other_user_cannot_read_extraction(self):
        with isolated_test_session() as db:
            owner_id, other_user_id = get_two_users(db)

            run = make_successful_run(db, owner_id)

            artifact = save_extraction_artifact(
                db,
                run=run,
                owner_user_id=owner_id,
                extraction=sample_extraction(),
                source_id=SOURCE_ID,
                cv_text=CV_TEXT,
            )

            with self.assertRaises(AIArtifactNotFound):
                get_extraction_artifact(
                    db,
                    artifact_id=artifact.id,
                    owner_user_id=other_user_id,
                )

    def test_unsuccessful_run_rejected(self):
        with isolated_test_session() as db:
            user_id, _ = get_two_users(db)

            run = create_ai_run(
                db,
                user_id=user_id,
                task_type="CV_EXTRACTION",
                provider="gemini",
                model_name="gemini-3.5-flash-lite",
            )

            with self.assertRaises(ValueError):
                save_extraction_artifact(
                    db,
                    run=run,
                    owner_user_id=user_id,
                    extraction=sample_extraction(),
                    source_id=SOURCE_ID,
                    cv_text=CV_TEXT,
                )

    def test_mismatched_source_rejected(self):
        with isolated_test_session() as db:
            user_id, _ = get_two_users(db)
            run = make_successful_run(db, user_id)

            with self.assertRaises(ValueError):
                save_extraction_artifact(
                    db,
                    run=run,
                    owner_user_id=user_id,
                    extraction=sample_extraction(),
                    source_id="different-source",
                    cv_text=CV_TEXT,
                )

    def test_rollback_removes_test_records(self):
        verify_test_database()

        with test_engine.connect() as connection:
            before_runs = connection.scalar(
                select(func.count()).select_from(AIRun)
            )
            before_artifacts = connection.scalar(
                select(func.count()).select_from(AIArtifact)
            )

        with isolated_test_session() as db:
            user_id, _ = get_two_users(db)
            run = make_successful_run(db, user_id)

            artifact = save_extraction_artifact(
                db,
                run=run,
                owner_user_id=user_id,
                extraction=sample_extraction(),
                source_id=SOURCE_ID,
                cv_text=CV_TEXT,
            )

            self.assertIsNotNone(artifact.id)

            # Exercise the existing savepoint handling.
            db.commit()

        with test_engine.connect() as connection:
            after_runs = connection.scalar(
                select(func.count()).select_from(AIRun)
            )
            after_artifacts = connection.scalar(
                select(func.count()).select_from(AIArtifact)
            )

        self.assertEqual(before_runs, after_runs)
        self.assertEqual(before_artifacts, after_artifacts)

    def test_fabricated_evidence_rejected_by_persistence(self):
        with isolated_test_session() as db:
            user_id, _ = get_two_users(db)

            run = make_successful_run(db, user_id)

            invalid_extraction = sample_extraction()
            invalid_extraction.degrees[0].evidence[0].excerpt = (
                "A fabricated qualification not present in the CV"
            )

            with self.assertRaises(ValueError):
                save_extraction_artifact(
                    db,
                    run=run,
                    owner_user_id=user_id,
                    extraction=invalid_extraction,
                    source_id=SOURCE_ID,
                    cv_text=CV_TEXT,
                )

            artifacts = db.execute(
                select(AIArtifact).where(
                    AIArtifact.run_id == run.id
                )
            ).scalars().all()

            self.assertEqual(len(artifacts), 0)


if __name__ == "__main__":
    unittest.main()
