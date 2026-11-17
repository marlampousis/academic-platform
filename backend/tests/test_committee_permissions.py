
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock

from fastapi import HTTPException

from app.auth.permissions import require_committee_access


class TestCommitteePermissions(unittest.TestCase):

    def setUp(self):
        self.db = MagicMock()

    def make_user(self, role, user_id=1):
        return SimpleNamespace(
            id=user_id,
            role=SimpleNamespace(code=role),
        )

    def test_super_admin_allowed(self):
        user = self.make_user("SUPER_ADMIN")

        require_committee_access(
            db=self.db,
            committee_id=10,
            current_user=user,
        )

    def test_active_reviewer_allowed(self):
        user = self.make_user("REVIEWER")

        self.db.query.return_value.filter.return_value.first.return_value = (
            SimpleNamespace(is_active=True)
        )

        require_committee_access(
            db=self.db,
            committee_id=10,
            current_user=user,
        )

    def test_reviewer_without_membership_denied(self):
        user = self.make_user("REVIEWER")

        self.db.query.return_value.filter.return_value.first.return_value = None

        with self.assertRaises(HTTPException) as context:
            require_committee_access(
                db=self.db,
                committee_id=10,
                current_user=user,
            )

        self.assertEqual(context.exception.status_code, 403)

    def test_candidate_denied(self):
        user = self.make_user("CANDIDATE")

        with self.assertRaises(HTTPException) as context:
            require_committee_access(
                db=self.db,
                committee_id=10,
                current_user=user,
            )

        self.assertEqual(context.exception.status_code, 403)

    def test_institution_admin_denied(self):
        user = self.make_user("INSTITUTION_ADMIN")

        with self.assertRaises(HTTPException) as context:
            require_committee_access(
                db=self.db,
                committee_id=10,
                current_user=user,
            )

        self.assertEqual(context.exception.status_code, 403)


if __name__ == "__main__":
    unittest.main()
