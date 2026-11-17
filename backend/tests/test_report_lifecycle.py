
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from fastapi import HTTPException

from app.evaluation_reports.router import (
    edit_my_evaluation_report,
    submit_my_evaluation_report,
)


ROUTER = "app.evaluation_reports.router"


class TestReportLifecycle(unittest.TestCase):

    def setUp(self):
        self.db = MagicMock()
        self.reviewer = SimpleNamespace(id=1)

    @patch(f"{ROUTER}.update_evaluation_report")
    @patch(f"{ROUTER}.get_committee_application_by_id")
    @patch(f"{ROUTER}.get_evaluation_committee_by_id")
    @patch(f"{ROUTER}.validate_report_reviewer")
    def test_completed_committee_cannot_edit_report(
        self, mock_access, mock_committee,
        mock_assignment, mock_update
    ):
        mock_committee.return_value = SimpleNamespace(
            id=10, status="COMPLETED"
        )

        with self.assertRaises(HTTPException) as context:
            edit_my_evaluation_report(
                committee_id=10,
                assignment_id=25,
                report_id=50,
                report_data=SimpleNamespace(
                    final_comment="Updated"
                ),
                db=self.db,
                current_reviewer=self.reviewer,
            )

        self.assertEqual(context.exception.status_code, 400)
        mock_assignment.assert_not_called()
        mock_update.assert_not_called()

    @patch(f"{ROUTER}.submit_evaluation_report")
    @patch(f"{ROUTER}.get_committee_application_by_id")
    @patch(f"{ROUTER}.get_evaluation_committee_by_id")
    @patch(f"{ROUTER}.validate_report_reviewer")
    def test_completed_committee_cannot_submit_report(
        self, mock_access, mock_committee,
        mock_assignment, mock_submit
    ):
        mock_committee.return_value = SimpleNamespace(
            id=10, status="COMPLETED"
        )

        with self.assertRaises(HTTPException) as context:
            submit_my_evaluation_report(
                committee_id=10,
                assignment_id=25,
                report_id=50,
                db=self.db,
                current_reviewer=self.reviewer,
            )

        self.assertEqual(context.exception.status_code, 400)
        mock_assignment.assert_not_called()
        mock_submit.assert_not_called()


if __name__ == "__main__":
    unittest.main()
