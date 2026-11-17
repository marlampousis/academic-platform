import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.main import app
from app.core.database import get_db
from app.users.router import get_current_user


class TestPositionHTTPPermissions(unittest.TestCase):

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

    def test_candidate_cannot_create(self):
        self.set_user("CANDIDATE")
        response = self.client.post("/positions/", json={})
        self.assertEqual(response.status_code, 403)

    def test_candidate_cannot_delete(self):
        self.set_user("CANDIDATE")
        response = self.client.delete("/positions/10")
        self.assertEqual(response.status_code, 403)

    def test_institution_admin_cannot_delete(self):
        self.set_user("INSTITUTION_ADMIN")
        response = self.client.delete("/positions/10")
        self.assertEqual(response.status_code, 403)

    def test_reviewer_cannot_update(self):
        self.set_user("REVIEWER")
        response = self.client.put("/positions/10", json={})
        self.assertEqual(response.status_code, 403)

    def test_super_admin_create_reaches_validation(self):
        self.set_user("SUPER_ADMIN")
        response = self.client.post("/positions/", json={})
        self.assertEqual(response.status_code, 422)

    @patch(
        "app.academic_positions.router.get_position_by_id",
        return_value=None,
    )
    def test_super_admin_delete_reaches_lookup(self, mock_lookup):
        self.set_user("SUPER_ADMIN")
        response = self.client.delete("/positions/10")
        self.assertEqual(response.status_code, 404)
        mock_lookup.assert_called_once_with(self.db, 10)

    @patch(
        "app.academic_positions.router.get_position_by_id",
        return_value=None,
    )
    def test_super_admin_update_reaches_lookup(self, mock_lookup):
        self.set_user("SUPER_ADMIN")
        response = self.client.put("/positions/10", json={})
        self.assertEqual(response.status_code, 404)
        mock_lookup.assert_called_once_with(self.db, 10)

    def test_unauthenticated_delete_denied(self):
        response = self.client.delete("/positions/10")
        self.assertIn(response.status_code, (401, 403))


if __name__ == "__main__":
    unittest.main()
