
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from fastapi import HTTPException

from app.evaluation_scores.router import (
    add_evaluation_score,
    edit_evaluation_score,
    remove_evaluation_score,
)


ROUTER = "app.evaluation_scores.router"


class TestSubmittedScoreEndpoints(unittest.TestCase):

    def setUp(self):
        from unittest.mock import MagicMock

        self.db = MagicMock()
        self.reviewer = SimpleNamespace(id=1)

        self.patches = [
            patch(f"{ROUTER}.validate_reviewer_access"),
            patch(
                f"{ROUTER}.get_evaluation_committee_by_id",
                return_value=SimpleNamespace(
                    id=10,
                    status="ACTIVE",
                ),
            ),
            patch(
                f"{ROUTER}.get_committee_application_by_id",
                return_value=SimpleNamespace(
                    id=25,
                    committee_id=10,
                    status="IN_EVALUATION",
                ),
            ),
            patch(
                f"{ROUTER}.get_evaluation_score_by_id",
                return_value=SimpleNamespace(
                    id=50,
                    committee_application_id=25,
                    reviewer_id=1,
                ),
            ),
            patch(
                f"{ROUTER}.get_reviewer_report",
                return_value=SimpleNamespace(
                    status="SUBMITTED",
                ),
            ),
        ]

        for item in self.patches:
            item.start()
            self.addCleanup(item.stop)

    @patch(f"{ROUTER}.create_evaluation_score")
    def test_submitted_report_blocks_create(self, mock_create):
        with self.assertRaises(HTTPException) as context:
            add_evaluation_score(
                committee_id=10,
                assignment_id=25,
                score_data=SimpleNamespace(
                    criterion_id=1,
                    score=5,
                ),
                db=self.db,
                current_reviewer=self.reviewer,
            )

        self.assertEqual(context.exception.status_code, 409)
        mock_create.assert_not_called()

    @patch(f"{ROUTER}.update_evaluation_score")
    def test_submitted_report_blocks_edit(self, mock_update):
        with self.assertRaises(HTTPException) as context:
            edit_evaluation_score(
                committee_id=10,
                assignment_id=25,
                score_id=50,
                score_data=SimpleNamespace(score=5),
                db=self.db,
                current_reviewer=self.reviewer,
            )

        self.assertEqual(context.exception.status_code, 409)
        mock_update.assert_not_called()

    @patch(f"{ROUTER}.delete_evaluation_score")
    def test_submitted_report_blocks_delete(self, mock_delete):
        with self.assertRaises(HTTPException) as context:
            remove_evaluation_score(
                committee_id=10,
                assignment_id=25,
                score_id=50,
                db=self.db,
                current_reviewer=self.reviewer,
            )

        self.assertEqual(context.exception.status_code, 409)
        mock_delete.assert_not_called()


if __name__ == "__main__":
    unittest.main()
