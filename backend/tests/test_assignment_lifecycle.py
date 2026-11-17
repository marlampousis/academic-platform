
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from fastapi import HTTPException

from app.committee_applications.router import (
    edit_committee_application,
)


ROUTER = "app.committee_applications.router"


class TestAssignmentLifecycle(unittest.TestCase):

    def setUp(self):
        self.db = MagicMock()
        self.admin = SimpleNamespace(id=1)

    @patch(f"{ROUTER}.update_committee_application")
    @patch(f"{ROUTER}.get_committee_application_by_id")
    @patch(f"{ROUTER}.get_evaluation_committee_by_id")
    def test_completed_committee_cannot_edit_assignment(
        self,
        mock_committee,
        mock_assignment,
        mock_update,
    ):
        mock_committee.return_value = SimpleNamespace(
            id=10,
            status="COMPLETED",
        )

        with self.assertRaises(HTTPException) as context:
            edit_committee_application(
                committee_id=10,
                assignment_id=25,
                assignment_data=SimpleNamespace(
                    status="COMPLETED",
                ),
                db=self.db,
                current_admin=self.admin,
            )

        self.assertEqual(context.exception.status_code, 409)
        mock_assignment.assert_not_called()
        mock_update.assert_not_called()

    @patch(f"{ROUTER}.update_committee_application")
    @patch(f"{ROUTER}.get_committee_application_by_id")
    @patch(f"{ROUTER}.get_evaluation_committee_by_id")
    def test_inactive_committee_cannot_edit_assignment(
        self,
        mock_committee,
        mock_assignment,
        mock_update,
    ):
        mock_committee.return_value = SimpleNamespace(
            id=10,
            status="DRAFT",
        )

        with self.assertRaises(HTTPException) as context:
            edit_committee_application(
                committee_id=10,
                assignment_id=25,
                assignment_data=SimpleNamespace(
                    status="IN_EVALUATION",
                ),
                db=self.db,
                current_admin=self.admin,
            )

        self.assertEqual(context.exception.status_code, 409)
        mock_assignment.assert_not_called()
        mock_update.assert_not_called()


if __name__ == "__main__":
    unittest.main()
