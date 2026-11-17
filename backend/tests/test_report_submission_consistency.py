
import unittest
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from fastapi import HTTPException

from app.evaluation_reports.router import (
    submit_my_evaluation_report,
)


ROUTER = "app.evaluation_reports.router"


class TestReportSubmissionConsistency(unittest.TestCase):

    def setUp(self):
        self.db = MagicMock()
        self.reviewer = SimpleNamespace(id=1)

        self.assignment = SimpleNamespace(
            id=25,
            committee_id=10,
            status="IN_EVALUATION",
        )

        self.report = SimpleNamespace(
            id=50,
            committee_application_id=25,
            reviewer_id=1,
            status="DRAFT",
            weighted_score=Decimal("60.00"),
        )

        self.patchers = [
            patch(f"{ROUTER}.validate_report_reviewer"),
            patch(
                f"{ROUTER}.get_evaluation_committee_by_id",
                return_value=SimpleNamespace(
                    id=10,
                    status="ACTIVE",
                ),
            ),
            patch(
                f"{ROUTER}.get_committee_application_by_id",
                return_value=self.assignment,
            ),
            patch(
                f"{ROUTER}.get_evaluation_report_by_id",
                return_value=self.report,
            ),
            patch(
                f"{ROUTER}.reviewer_scoring_is_complete",
                return_value=True,
            ),
            patch(
                f"{ROUTER}.calculate_reviewer_weighted_score",
                return_value=Decimal("85.00"),
            ),
            patch(f"{ROUTER}.submit_evaluation_report"),
        ]

        self.mocks = [p.start() for p in self.patchers]

        for p in self.patchers:
            self.addCleanup(p.stop)

    def submit(self):
        return submit_my_evaluation_report(
            committee_id=10,
            assignment_id=25,
            report_id=50,
            db=self.db,
            current_reviewer=self.reviewer,
        )

    def test_submission_recalculates_weighted_score(self):
        self.submit()

        self.assertEqual(
            self.report.weighted_score,
            Decimal("85.00"),
        )

        self.mocks[5].assert_called_once_with(
            db=self.db,
            committee_application_id=25,
            reviewer_id=1,
        )

        self.mocks[6].assert_called_once_with(
            db=self.db,
            report=self.report,
        )

    def test_incomplete_scores_block_submission(self):
        self.mocks[4].return_value = False

        with self.assertRaises(HTTPException) as context:
            self.submit()

        self.assertEqual(context.exception.status_code, 409)
        self.assertEqual(
            self.report.weighted_score,
            Decimal("60.00"),
        )
        self.mocks[6].assert_not_called()

    def test_invalid_assignment_status_blocks_submission(self):
        self.assignment.status = "COMPLETED"

        with self.assertRaises(HTTPException) as context:
            self.submit()

        self.assertEqual(context.exception.status_code, 409)
        self.mocks[5].assert_not_called()
        self.mocks[6].assert_not_called()


if __name__ == "__main__":
    unittest.main()
