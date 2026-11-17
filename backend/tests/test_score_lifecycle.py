
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from fastapi import HTTPException

from app.evaluation_scores.router import (
    edit_evaluation_score,
    remove_evaluation_score,
)


class TestScoreLifecycle(unittest.TestCase):

    def setUp(self):
        self.db = MagicMock()
        self.reviewer = SimpleNamespace(id=1)

    @patch(
        "app.evaluation_scores.router."
        "get_committee_application_by_id"
    )
    @patch(
        "app.evaluation_scores.router."
        "get_evaluation_committee_by_id"
    )
    @patch(
        "app.evaluation_scores.router."
        "validate_reviewer_access"
    )
    def test_completed_committee_cannot_edit_score(
        self,
        mock_access,
        mock_committee,
        mock_assignment,
    ):
        mock_committee.return_value = SimpleNamespace(
            id=10,
            status="COMPLETED",
        )

        with self.assertRaises(HTTPException) as context:
            edit_evaluation_score(
                committee_id=10,
                assignment_id=25,
                score_id=50,
                score_data=SimpleNamespace(score=5),
                db=self.db,
                current_reviewer=self.reviewer,
            )

        self.assertEqual(context.exception.status_code, 400)
        mock_access.assert_called_once()
        mock_assignment.assert_not_called()

    @patch(
        "app.evaluation_scores.router."
        "get_committee_application_by_id"
    )
    @patch(
        "app.evaluation_scores.router."
        "get_evaluation_committee_by_id"
    )
    @patch(
        "app.evaluation_scores.router."
        "validate_reviewer_access"
    )
    def test_completed_committee_cannot_delete_score(
        self,
        mock_access,
        mock_committee,
        mock_assignment,
    ):
        mock_committee.return_value = SimpleNamespace(
            id=10,
            status="COMPLETED",
        )

        with self.assertRaises(HTTPException) as context:
            remove_evaluation_score(
                committee_id=10,
                assignment_id=25,
                score_id=50,
                db=self.db,
                current_reviewer=self.reviewer,
            )

        self.assertEqual(context.exception.status_code, 400)
        mock_access.assert_called_once()
        mock_assignment.assert_not_called()


if __name__ == "__main__":
    unittest.main()
