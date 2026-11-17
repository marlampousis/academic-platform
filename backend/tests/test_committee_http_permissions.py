import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.main import app
from app.core.database import get_db
from app.users.router import get_current_user

from decimal import Decimal

BASE_URL = "/evaluation-committees/10/applications"


class TestCommitteeHTTPPermissions(unittest.TestCase):

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

    def test_unauthenticated_denied(self):
        response = self.client.get(BASE_URL)
        self.assertIn(response.status_code, (401, 403))

    @patch(
        "app.committee_applications.router."
        "get_evaluation_committee_by_id"
    )
    def test_candidate_denied(self, mock_committee):
        self.set_user("CANDIDATE")
        response = self.client.get(BASE_URL)
        self.assertEqual(response.status_code, 403)

    @patch(
        "app.committee_applications.router."
        "get_evaluation_committee_by_id"
    )
    def test_unassigned_reviewer_denied(self, mock_committee):
        self.set_user("REVIEWER")
        mock_committee.return_value = SimpleNamespace(id=10)

        self.db.query.return_value.filter.return_value.first.return_value = None

        response = self.client.get(BASE_URL)
        self.assertEqual(response.status_code, 403)

    @patch(
        "app.committee_applications.router."
        "get_committee_applications",
        return_value=[],
    )
    @patch(
        "app.committee_applications.router."
        "get_evaluation_committee_by_id"
    )
    def test_active_reviewer_allowed(
        self, mock_committee, mock_applications
    ):
        self.set_user("REVIEWER")
        mock_committee.return_value = SimpleNamespace(id=10)

        self.db.query.return_value.filter.return_value.first.return_value = (
            SimpleNamespace(is_active=True)
        )

        response = self.client.get(BASE_URL)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    @patch(
        "app.committee_applications.router."
        "get_evaluation_committee_by_id"
    )
    def test_inactive_reviewer_denied(self, mock_committee):
        self.set_user("REVIEWER")
        mock_committee.return_value = SimpleNamespace(id=10)

        # The database filter excludes inactive memberships.
        self.db.query.return_value.filter.return_value.first.return_value = None

        response = self.client.get(BASE_URL)
        self.assertEqual(response.status_code, 403)

    @patch(
        "app.committee_applications.router."
        "get_evaluation_committee_by_id"
    )
    def test_institution_admin_denied(self, mock_committee):
        self.set_user("INSTITUTION_ADMIN")
        mock_committee.return_value = SimpleNamespace(id=10)

        response = self.client.get(BASE_URL)
        self.assertEqual(response.status_code, 403)

    @patch(
        "app.committee_applications.router."
        "get_committee_applications",
        return_value=[],
    )
    @patch(
        "app.committee_applications.router."
        "get_evaluation_committee_by_id"
    )
    def test_super_admin_allowed(
        self, mock_committee, mock_applications
    ):
        self.set_user("SUPER_ADMIN")
        mock_committee.return_value = SimpleNamespace(id=10)

        response = self.client.get(BASE_URL)
        self.assertEqual(response.status_code, 200)


    @patch(
        "app.committee_applications.router."
        "get_evaluation_committee_by_id"
    )
    def test_individual_application_unassigned_reviewer_denied(
        self, mock_committee
    ):
        self.set_user("REVIEWER")
        mock_committee.return_value = SimpleNamespace(id=10)

        self.db.query.return_value.filter.return_value.first.return_value = None

        response = self.client.get(
            "/evaluation-committees/10/applications/25"
        )

        self.assertEqual(response.status_code, 403)

    @patch(
        "app.committee_applications.router."
        "get_committee_application_by_id",
        return_value=None,
    )
    @patch(
        "app.committee_applications.router."
        "get_evaluation_committee_by_id"
    )
    def test_individual_application_super_admin_reaches_lookup(
        self, mock_committee, mock_assignment
    ):
        self.set_user("SUPER_ADMIN")
        mock_committee.return_value = SimpleNamespace(id=10)

        response = self.client.get(
            "/evaluation-committees/10/applications/25"
        )

        self.assertEqual(response.status_code, 404)
        mock_assignment.assert_called_once()


    @patch(
        "app.evaluation_scores.router."
        "get_evaluation_committee_by_id"
    )
    def test_scores_unassigned_reviewer_denied(
        self, mock_committee
    ):
        self.set_user("REVIEWER")
        mock_committee.return_value = SimpleNamespace(id=10)

        self.db.query.return_value.filter.return_value.first.return_value = None

        response = self.client.get(
            "/evaluation-committees/10/applications/25/scores"
        )

        self.assertEqual(response.status_code, 403)

    @patch(
        "app.evaluation_scores.router."
        "get_committee_application_by_id",
        return_value=None,
    )
    @patch(
        "app.evaluation_scores.router."
        "get_evaluation_committee_by_id"
    )
    def test_scores_super_admin_reaches_lookup(
        self, mock_committee, mock_assignment
    ):
        self.set_user("SUPER_ADMIN")
        mock_committee.return_value = SimpleNamespace(id=10)

        response = self.client.get(
            "/evaluation-committees/10/applications/25/scores"
        )

        self.assertEqual(response.status_code, 404)
        mock_assignment.assert_called_once_with(
            self.db, 25
        )

    @patch(
        "app.evaluation_scores.router."
        "get_scores_for_assignment",
        return_value=[],
    )
    @patch(
        "app.evaluation_scores.router."
        "get_committee_application_by_id"
    )
    @patch(
        "app.evaluation_scores.router."
        "get_evaluation_committee_by_id"
    )
    def test_scores_active_reviewer_allowed(
        self, mock_committee, mock_assignment, mock_scores
    ):
        self.set_user("REVIEWER")
        mock_committee.return_value = SimpleNamespace(id=10)
        mock_assignment.return_value = SimpleNamespace(
            id=25,
            committee_id=10,
        )

        # Simulates an active committee membership.
        self.db.query.return_value.filter.return_value.first.return_value = (
            SimpleNamespace(is_active=True)
        )

        response = self.client.get(
            "/evaluation-committees/10/applications/25/scores"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])
        mock_scores.assert_called_once_with(
            db=self.db,
            committee_application_id=25,
        )

    
    @patch(
        "app.committee_members.router."
        "get_evaluation_committee_by_id"
    )
    def test_members_unassigned_reviewer_denied(
        self, mock_committee
    ):
        self.set_user("REVIEWER")
        mock_committee.return_value = SimpleNamespace(id=10)

        # No active membership in this committee.
        self.db.query.return_value.filter.return_value.first.return_value = None

        response = self.client.get(
            "/evaluation-committees/10/members"
        )

        self.assertEqual(response.status_code, 403)

    @patch(
        "app.committee_members.router."
        "get_evaluation_committee_by_id"
    )
    def test_individual_member_unassigned_reviewer_denied(
        self, mock_committee
    ):
        self.set_user("REVIEWER")
        mock_committee.return_value = SimpleNamespace(id=10)

        # The reviewer does not belong to Committee 10.
        self.db.query.return_value.filter.return_value.first.return_value = None

        response = self.client.get(
            "/evaluation-committees/10/members/25"
        )

        self.assertEqual(response.status_code, 403)


    @patch(
        "app.evaluation_criteria.router."
        "get_evaluation_committee_by_id"
    )
    def test_criteria_unassigned_reviewer_denied(
        self, mock_committee
    ):
        self.set_user("REVIEWER")
        mock_committee.return_value = SimpleNamespace(id=10)

        self.db.query.return_value.filter.return_value.first.return_value = None

        paths = [
            "/evaluation-committees/10/criteria",
            "/evaluation-committees/10/criteria/summary",
            "/evaluation-committees/10/criteria/25",
        ]

        for path in paths:
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 403)


    @patch(
        "app.evaluation_committees.router."
        "get_evaluation_committee_by_id"
    )
    def test_committee_details_unassigned_reviewer_denied(
        self, mock_committee
    ):
        self.set_user("REVIEWER")
        mock_committee.return_value = SimpleNamespace(id=10)

        self.db.query.return_value.filter.return_value.first.return_value = None

        response = self.client.get(
            "/evaluation-committees/10"
        )

        self.assertEqual(response.status_code, 403)

    @patch(
        "app.evaluation_committees.router."
        "get_evaluation_committee_by_id",
        return_value=None,
    )
    def test_committee_details_super_admin_reaches_lookup(
        self, mock_committee
    ):
        self.set_user("SUPER_ADMIN")

        response = self.client.get(
            "/evaluation-committees/10"
        )

        self.assertEqual(response.status_code, 404)
        mock_committee.assert_called_once_with(
            self.db, 10
        )
 
    @patch(
        "app.evaluation_committees.router."
        "get_evaluation_committee_by_position"
    )
    def test_committee_by_position_unassigned_reviewer_denied(
        self, mock_committee
    ):
        self.set_user("REVIEWER")
        mock_committee.return_value = SimpleNamespace(id=10)

        self.db.query.return_value.filter.return_value.first.return_value = None

        response = self.client.get(
            "/evaluation-committees/position/20"
        )

        self.assertEqual(response.status_code, 403)
        mock_committee.assert_called_once_with(self.db, 20)



    def test_committee_list_reviewer_denied(self):
        self.set_user("REVIEWER")

        response = self.client.get("/evaluation-committees/")

        self.assertEqual(response.status_code, 403)

    @patch(
        "app.evaluation_committees.router.get_evaluation_committees",
        return_value=[],
    )
    def test_committee_list_super_admin_allowed(self, mock_committees):
        self.set_user("SUPER_ADMIN")

        response = self.client.get("/evaluation-committees/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])
        mock_committees.assert_called_once_with(self.db)

    def test_institution_admin_cannot_create_committee(self):
        self.set_user("INSTITUTION_ADMIN")

        response = self.client.post(
            "/evaluation-committees/",
            json={},
        )

        self.assertEqual(response.status_code, 403)

    def test_institution_admin_cannot_add_committee_member(self):
        self.set_user("INSTITUTION_ADMIN")

        response = self.client.post(
            "/evaluation-committees/10/members",
            json={},
        )

        self.assertEqual(response.status_code, 403)

    def test_institution_admin_cannot_add_evaluation_criterion(self):
        self.set_user("INSTITUTION_ADMIN")

        response = self.client.post(
            "/evaluation-committees/10/criteria",
            json={},
        )

        self.assertEqual(response.status_code, 403)

    @patch(
        "app.committee_members.router."
        "get_committee_member_by_id",
        return_value=None,
    )
    @patch(
        "app.committee_members.router."
        "get_evaluation_committee_by_id",
    )
    def test_active_reviewer_reaches_member_lookup(
        self, mock_committee, mock_member
    ):
        self.set_user("REVIEWER")

        mock_committee.return_value = SimpleNamespace(
            id=10
        )

        self.db.query.return_value.filter.return_value.first.return_value = (
            SimpleNamespace(is_active=True)
        )

        response = self.client.get(
            "/evaluation-committees/10/members/25"
        )

        self.assertEqual(response.status_code, 404)
        mock_member.assert_called_once()

    def test_active_reviewer_can_read_criteria_summary(self):
        self.set_user("REVIEWER")

        self.db.query.return_value.filter.return_value.first.return_value = (
            SimpleNamespace(is_active=True)
        )

        with (
            patch(
                "app.evaluation_criteria.router."
                "get_evaluation_committee_by_id",
                return_value=SimpleNamespace(id=10),
            ) as mock_committee,
            patch(
                "app.evaluation_criteria.router."
                "get_evaluation_criteria",
                return_value=[],
            ) as mock_criteria,
            patch(
                "app.evaluation_criteria.router."
                "get_total_active_weight",
                return_value=Decimal("0"),
            ) as mock_weight,
        ):
            response = self.client.get(
                "/evaluation-committees/10/criteria/summary"
            )

        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertEqual(data["committee_id"], 10)
        self.assertEqual(data["criteria_count"], 0)
        self.assertEqual(data["active_criteria_count"], 0)
        self.assertFalse(data["is_weight_complete"])

        mock_committee.assert_called_once_with(self.db, 10)
        mock_criteria.assert_called_once_with(
            db=self.db,
            committee_id=10,
        )
        mock_weight.assert_called_once_with(self.db, 10)

    def test_institution_admin_cannot_assign_application(self):
        self.set_user("INSTITUTION_ADMIN")

        response = self.client.post(
            "/evaluation-committees/10/applications",
            json={},
        )

        self.assertEqual(response.status_code, 403)

    def test_institution_admin_cannot_edit_assignment(self):
        self.set_user("INSTITUTION_ADMIN")

        response = self.client.put(
            "/evaluation-committees/10/applications/25",
            json={},
        )

        self.assertEqual(response.status_code, 403)

    def test_institution_admin_cannot_delete_assignment(self):
        self.set_user("INSTITUTION_ADMIN")

        response = self.client.delete(
            "/evaluation-committees/10/applications/25"
        )

        self.assertEqual(response.status_code, 403)

if __name__ == "__main__":
    unittest.main()