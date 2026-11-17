
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from fastapi import HTTPException

from app.evaluation_results.service import (
    validate_ranking_completeness,
)


class TestRankingCompleteness(unittest.TestCase):

    def setUp(self):
        self.db = MagicMock()
        self.assignments = [
            SimpleNamespace(id=25),
        ]

    @patch(
        "app.evaluation_results.service.get_reports_for_assignment"
    )
    @patch(
        "app.evaluation_results.service.get_committee_members"
    )
    def test_missing_reviewer_report_blocks_ranking(
        self,
        mock_members,
        mock_reports,
    ):
        mock_members.return_value = [
            SimpleNamespace(user_id=1, is_active=True),
            SimpleNamespace(user_id=2, is_active=True),
        ]

        mock_reports.return_value = [
            SimpleNamespace(
                reviewer_id=1,
                status="SUBMITTED",
            ),
        ]

        with self.assertRaises(HTTPException) as context:
            validate_ranking_completeness(
                self.db, 10, self.assignments
            )

        self.assertEqual(context.exception.status_code, 409)

    @patch(
        "app.evaluation_results.service.get_reports_for_assignment"
    )
    @patch(
        "app.evaluation_results.service.get_committee_members"
    )
    def test_all_reports_submitted_allows_ranking(
        self,
        mock_members,
        mock_reports,
    ):
        mock_members.return_value = [
            SimpleNamespace(user_id=1, is_active=True),
            SimpleNamespace(user_id=2, is_active=True),
        ]

        mock_reports.return_value = [
            SimpleNamespace(
                reviewer_id=1,
                status="SUBMITTED",
            ),
            SimpleNamespace(
                reviewer_id=2,
                status="SUBMITTED",
            ),
        ]

        validate_ranking_completeness(
            self.db, 10, self.assignments
        )

        mock_reports.assert_called_once_with(
            db=self.db,
            committee_application_id=25,
        )

    @patch(
        "app.evaluation_results.service.get_committee_members"
    )
    def test_no_active_reviewers_blocks_ranking(
        self,
        mock_members,
    ):
        mock_members.return_value = []

        with self.assertRaises(HTTPException) as context:
            validate_ranking_completeness(
                self.db, 10, self.assignments
            )

        self.assertEqual(context.exception.status_code, 409)


    @patch(
        "app.evaluation_results.service."
        "validate_ranking_completeness"
    )
    @patch(
        "app.evaluation_results.service."
        "get_evaluation_result_by_assignment"
    )
    def test_generation_checks_completeness_before_writes(
        self,
        mock_result,
        mock_validate,
    ):
        from app.evaluation_results.service import (
            generate_committee_ranking,
        )

        mock_result.return_value = None

        mock_validate.side_effect = HTTPException(
            status_code=409,
            detail="Incomplete evaluation reports",
        )

        self.db.query.return_value.filter.return_value.all.return_value = (
            self.assignments
        )

        with self.assertRaises(HTTPException) as context:
            generate_committee_ranking(
                db=self.db,
                committee_id=10,
            )

        self.assertEqual(context.exception.status_code, 409)

        mock_validate.assert_called_once_with(
            db=self.db,
            committee_id=10,
            assignments=self.assignments,
        )

        self.db.commit.assert_not_called()


if __name__ == "__main__":
    unittest.main()
