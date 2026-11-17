
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from fastapi import HTTPException

from app.application_reviews.service import (
    update_application_review_status,
)


SERVICE = "app.application_reviews.service"


class TestApplicationStatusTransaction(unittest.TestCase):

    def setUp(self):
        self.db = MagicMock()

        self.application = SimpleNamespace(
            id=25,
            status="SUBMITTED",
            updated_at=None,
        )

    @patch(f"{SERVICE}.create_status_history_entry")
    def test_valid_transition_commits_status_and_history(
        self,
        mock_history,
    ):
        result = update_application_review_status(
            db=self.db,
            application=self.application,
            new_status="UNDER_REVIEW",
            changed_by=1,
            comment="Eligibility review started",
        )

        self.assertEqual(
            result.status,
            "UNDER_REVIEW",
        )

        mock_history.assert_called_once_with(
            db=self.db,
            application_id=25,
            previous_status="SUBMITTED",
            new_status="UNDER_REVIEW",
            changed_by=1,
            comment="Eligibility review started",
        )

        self.db.commit.assert_called_once()
        self.db.rollback.assert_not_called()

    @patch(f"{SERVICE}.create_status_history_entry")
    def test_invalid_transition_does_not_write(
        self,
        mock_history,
    ):
        with self.assertRaises(HTTPException) as context:
            update_application_review_status(
                db=self.db,
                application=self.application,
                new_status="ELIGIBLE",
                changed_by=1,
            )

        self.assertEqual(
            context.exception.status_code,
            400,
        )

        self.assertEqual(
            self.application.status,
            "SUBMITTED",
        )

        mock_history.assert_not_called()
        self.db.commit.assert_not_called()

    @patch(f"{SERVICE}.create_status_history_entry")
    def test_commit_failure_triggers_rollback(
        self,
        mock_history,
    ):
        self.db.commit.side_effect = RuntimeError(
            "Database commit failed"
        )

        with self.assertRaises(RuntimeError):
            update_application_review_status(
                db=self.db,
                application=self.application,
                new_status="UNDER_REVIEW",
                changed_by=1,
            )

        mock_history.assert_called_once()
        self.db.commit.assert_called_once()
        self.db.rollback.assert_called_once()


if __name__ == "__main__":
    unittest.main()
