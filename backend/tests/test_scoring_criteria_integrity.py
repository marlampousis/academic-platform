from app.main import app
import unittest
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock

from app.evaluation_reports.service import (
    reviewer_scoring_is_complete,
    calculate_reviewer_weighted_score,
)


class TestScoringCriteriaIntegrity(unittest.TestCase):

    def setUp(self):
        self.db = MagicMock()

    def configure_criteria(self, active_ids, scored_ids):
        # The first query returns active criterion IDs.
        # The second returns scored criterion IDs.
        query_criteria = MagicMock()
        query_scores = MagicMock()

        query_criteria.filter.return_value.all.return_value = [
            (criterion_id,) for criterion_id in active_ids
        ]

        query_scores.filter.return_value.all.return_value = [
            (criterion_id,) for criterion_id in scored_ids
        ]

        self.db.query.side_effect = [
            query_criteria,
            query_scores,
        ]

    def check_complete(self):
        return reviewer_scoring_is_complete(
            db=self.db,
            committee_id=10,
            committee_application_id=25,
            reviewer_id=1,
        )

    def test_all_active_criteria_scored(self):
        self.configure_criteria(
            active_ids=[1, 2, 3],
            scored_ids=[1, 2, 3],
        )

        self.assertTrue(self.check_complete())

    def test_missing_active_criterion(self):
        self.configure_criteria(
            active_ids=[1, 2, 3],
            scored_ids=[1, 2],
        )

        self.assertFalse(self.check_complete())

    def test_inactive_score_cannot_replace_active_score(self):
        self.configure_criteria(
            active_ids=[1, 2, 3],
            scored_ids=[1, 2, 4],
        )

        self.assertFalse(self.check_complete())

    def test_empty_active_criteria_rejected(self):
        self.configure_criteria(
            active_ids=[],
            scored_ids=[],
        )

        self.assertFalse(self.check_complete())

    def test_weighted_score_excludes_inactive_criteria(self):
        query = self.db.query.return_value

        active_score = SimpleNamespace(
            score=Decimal("8"),
            criterion=SimpleNamespace(
                is_active=True,
                max_score=Decimal("10"),
                weight=Decimal("60"),
            ),
        )

        inactive_score = SimpleNamespace(
            score=Decimal("10"),
            criterion=SimpleNamespace(
                is_active=False,
                max_score=Decimal("10"),
                weight=Decimal("40"),
            ),
        )

        query.options.return_value.filter.return_value.all.return_value = [
            active_score,
            inactive_score,
        ]

        result = calculate_reviewer_weighted_score(
            db=self.db,
            committee_application_id=25,
            reviewer_id=1,
        )

        self.assertEqual(result, Decimal("48.00"))


if __name__ == "__main__":
    unittest.main()
