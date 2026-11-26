
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from app.ai.models import AIArtifact

# Register all SQLAlchemy models before constructing ORM instances.
import app.core.model_registry

from app.ai.services.matching_persistence_service import (
    MatchingPersistenceError,
    start_matching_run,
    complete_matching_run,
    fail_matching_run,
)


class TestMatchingPersistenceService(unittest.TestCase):

    def setUp(self):
        self.db = Mock()

    def test_start_matching_run(self):
        run = SimpleNamespace(
            id=42,
            status="PENDING",
        )

        with patch(
            "app.ai.services.matching_persistence_service."
            "create_ai_run",
            return_value=run,
        ) as create:
            result = start_matching_run(
                self.db,
                user_id=5,
                model_name="gemini-test",
            )

        self.assertEqual(result, 42)
        self.assertEqual(run.status, "RUNNING")
        self.db.commit.assert_called_once()

        create.assert_called_once_with(
            self.db,
            user_id=5,
            task_type="ACADEMIC_MATCHING",
            provider="gemini",
            model_name="gemini-test",
        )

    def test_start_failure_rolls_back(self):
        with patch(
            "app.ai.services.matching_persistence_service."
            "create_ai_run",
            side_effect=RuntimeError("DB error"),
        ):
            with self.assertRaises(MatchingPersistenceError):
                start_matching_run(
                    self.db,
                    user_id=5,
                    model_name="gemini-test",
                )

        self.db.rollback.assert_called_once()

    def test_complete_matching_run(self):
        run = SimpleNamespace(
            id=42,
            user_id=5,
            task_type="ACADEMIC_MATCHING",
            status="RUNNING",
        )
        self.db.get.return_value = run

        requirements = Mock()
        requirements.position_id = 18
        requirements.model_dump.return_value = {
            "position_id": 18,
            "requirements": [],
        }

        draft = Mock()
        draft.application_id = 11
        draft.position_id = 18
        draft.requires_human_review = True
        draft.model_dump.return_value = {
            "application_id": 11,
            "matches": [],
            "requires_human_review": True,
        }

        def assign_artifact_id(obj):
            if isinstance(obj, AIArtifact):
                obj.id = 77

        self.db.add.side_effect = assign_artifact_id

        artifact_id = complete_matching_run(
            self.db,
            run_id=42,
            user_id=5,
            application_id=11,
            requirements=requirements,
            draft=draft,
            latency_ms=1200,
        )

        self.assertEqual(artifact_id, 77)
        self.assertEqual(run.status, "SUCCEEDED")
        self.assertEqual(run.latency_ms, 1200)

        artifact = self.db.add.call_args.args[0]
        self.assertEqual(artifact.application_id, 11)
        self.assertEqual(artifact.owner_user_id, 5)
        self.assertEqual(
            artifact.artifact_type,
            "ACADEMIC_MATCHING",
        )
        self.assertEqual(
            artifact.status,
            "REVIEW_REQUIRED",
        )
        self.db.commit.assert_called_once()

    def test_wrong_run_owner_rejected(self):
        self.db.get.return_value = SimpleNamespace(
            user_id=7,
            task_type="ACADEMIC_MATCHING",
            status="RUNNING",
        )

        requirements = Mock(position_id=18)
        draft = Mock(
            application_id=11,
            position_id=18,
            requires_human_review=True,
        )

        with self.assertRaises(MatchingPersistenceError):
            complete_matching_run(
                self.db,
                run_id=42,
                user_id=5,
                application_id=11,
                requirements=requirements,
                draft=draft,
                latency_ms=100,
            )

        self.db.rollback.assert_called_once()
        self.db.commit.assert_not_called()

    def test_failed_run_records_error(self):
        run = SimpleNamespace(
            task_type="ACADEMIC_MATCHING",
            status="RUNNING",
        )
        self.db.get.return_value = run

        fail_matching_run(
            self.db,
            run_id=42,
            error_code="MATCHING_VALIDATION_ERROR",
            latency_ms=500,
        )

        self.assertEqual(run.status, "FAILED")
        self.assertEqual(
            run.error_code,
            "MATCHING_VALIDATION_ERROR",
        )
        self.assertEqual(run.latency_ms, 500)
        self.db.commit.assert_called_once()


if __name__ == "__main__":
    unittest.main()
