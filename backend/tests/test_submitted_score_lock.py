
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from fastapi import HTTPException

from app.evaluation_scores.router import (
    validate_scores_not_submitted,
)


class TestSubmittedScoreLock(unittest.TestCase):

    def setUp(self):
        self.db = MagicMock()

    @patch(
        "app.evaluation_scores.router.get_reviewer_report"
    )
    def test_submitted_report_blocks_scores(self, mock_report):
        mock_report.return_value = SimpleNamespace(
            status="SUBMITTED"
        )

        with self.assertRaises(HTTPException) as context:
            validate_scores_not_submitted(
                db=self.db,
                assignment_id=25,
                reviewer_id=1,
            )

        self.assertEqual(context.exception.status_code, 409)

        mock_report.assert_called_once_with(
            db=self.db,
            committee_application_id=25,
            reviewer_id=1,
        )

    @patch(
        "app.evaluation_scores.router.get_reviewer_report"
    )
    def test_draft_report_allows_scores(self, mock_report):
        mock_report.return_value = SimpleNamespace(
            status="DRAFT"
        )

        validate_scores_not_submitted(
            db=self.db,
            assignment_id=25,
            reviewer_id=1,
        )

    @patch(
        "app.evaluation_scores.router.get_reviewer_report"
    )
    def test_no_report_allows_scores(self, mock_report):
        mock_report.return_value = None

        validate_scores_not_submitted(
            db=self.db,
            assignment_id=25,
            reviewer_id=1,
        )


if __name__ == "__main__":
    unittest.main()
