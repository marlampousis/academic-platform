
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import get_db
from app.users.router import get_current_user


REVIEWS = "app.application_reviews.router"
HISTORY = "app.application_status_history.router"


class TestApplicationAdminHTTPPermissions(unittest.TestCase):

    def setUp(self):
        self.db = MagicMock()
        app.dependency_overrides[get_db] = lambda: self.db
        self.client = TestClient(app)

    def tearDown(self):
        self.client.close()
        app.dependency_overrides.clear()

    def set_user(self, role):
        user = SimpleNamespace(
            id=1,
            role=SimpleNamespace(code=role),
        )
        app.dependency_overrides[get_current_user] = lambda: user

    @patch(f"{REVIEWS}.get_applications_for_position")
    def test_institution_admin_cannot_list(self, mock_service):
        self.set_user("INSTITUTION_ADMIN")

        response = self.client.get(
            "/admin/positions/10/applications"
        )

        self.assertEqual(response.status_code, 403)
        mock_service.assert_not_called()

    @patch(f"{REVIEWS}.get_application_for_review")
    def test_institution_admin_cannot_read(self, mock_service):
        self.set_user("INSTITUTION_ADMIN")

        response = self.client.get("/admin/applications/25")

        self.assertEqual(response.status_code, 403)
        mock_service.assert_not_called()

    @patch(f"{REVIEWS}.get_application_for_review")
    def test_institution_admin_cannot_change_status(
        self, mock_service
    ):
        self.set_user("INSTITUTION_ADMIN")

        response = self.client.patch(
            "/admin/applications/25/status",
            json={
                "status": "UNDER_REVIEW",
                "comment": "Review started",
            },
        )

        self.assertEqual(response.status_code, 403)
        mock_service.assert_not_called()

    @patch(f"{HISTORY}.get_application_for_review")
    def test_institution_admin_cannot_read_history(
        self, mock_service
    ):
        self.set_user("INSTITUTION_ADMIN")

        response = self.client.get(
            "/admin/applications/25/history"
        )

        self.assertEqual(response.status_code, 403)
        mock_service.assert_not_called()

    @patch(
        f"{REVIEWS}.get_applications_for_position",
        return_value=[],
    )
    def test_super_admin_can_list(self, mock_service):
        self.set_user("SUPER_ADMIN")

        response = self.client.get(
            "/admin/positions/10/applications"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

        mock_service.assert_called_once_with(
            db=self.db,
            position_id=10,
            application_status=None,
        )

    @patch(f"{REVIEWS}.get_application_for_review")
    def test_super_admin_reaches_application_lookup(
        self, mock_service
    ):
        self.set_user("SUPER_ADMIN")

        mock_service.side_effect = HTTPException(
            status_code=404,
            detail="Application not found",
        )

        response = self.client.get("/admin/applications/25")

        self.assertEqual(response.status_code, 404)
        mock_service.assert_called_once_with(
            db=self.db,
            application_id=25,
        )

    @patch(f"{REVIEWS}.get_application_for_review")
    def test_super_admin_reaches_status_lookup(
        self, mock_service
    ):
        self.set_user("SUPER_ADMIN")

        mock_service.side_effect = HTTPException(
            status_code=404,
            detail="Application not found",
        )

        response = self.client.patch(
            "/admin/applications/25/status",
            json={
                "status": "UNDER_REVIEW",
                "comment": "Review started",
            },
        )

        self.assertEqual(response.status_code, 404)
        mock_service.assert_called_once_with(
            db=self.db,
            application_id=25,
        )

    @patch(f"{HISTORY}.get_application_for_review")
    def test_super_admin_reaches_history_lookup(
        self, mock_service
    ):
        self.set_user("SUPER_ADMIN")

        mock_service.side_effect = HTTPException(
            status_code=404,
            detail="Application not found",
        )

        response = self.client.get(
            "/admin/applications/25/history"
        )

        self.assertEqual(response.status_code, 404)
        mock_service.assert_called_once_with(
            db=self.db,
            application_id=25,
        )


if __name__ == "__main__":
    unittest.main()
