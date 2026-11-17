from app.main import app
import unittest
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from app.evaluation_results.service import (
    generate_committee_ranking,
    create_or_update_evaluation_result,
)


SERVICE = "app.evaluation_results.service"


class TestRankingAtomicity(unittest.TestCase):

    def setUp(self):
        self.db = MagicMock()

        self.assignments = [
            SimpleNamespace(id=10),
            SimpleNamespace(id=20),
        ]

        self.db.query.return_value.filter.return_value.all.return_value = (
            self.assignments
        )

    @patch(
        f"{SERVICE}.get_evaluation_result_by_assignment",
        return_value=None,
    )
    def test_deferred_result_creation_does_not_commit(
        self,
        mock_lookup,
    ):
        create_or_update_evaluation_result(
            db=self.db,
            committee_application_id=10,
            final_score=Decimal("80.00"),
            commit=False,
        )

        self.db.add.assert_called_once()
        self.db.commit.assert_not_called()
        self.db.refresh.assert_not_called()

    @patch(f"{SERVICE}.create_or_update_evaluation_result")
    @patch(f"{SERVICE}.calculate_application_final_score")
    @patch(f"{SERVICE}.validate_ranking_completeness")
    @patch(f"{SERVICE}.get_evaluation_result_by_assignment")
    def test_successful_ranking_commits_once(
        self,
        mock_lookup,
        mock_validate,
        mock_score,
        mock_create,
    ):
        mock_lookup.return_value = None

        scores = {
            10: Decimal("70.00"),
            20: Decimal("90.00"),
        }

        mock_score.side_effect = (
            lambda db, committee_application_id:
            scores[committee_application_id]
        )

        def create_result(
            db,
            committee_application_id,
            final_score,
            commit,
        ):
            self.assertFalse(commit)

            return SimpleNamespace(
                committee_application_id=committee_application_id,
                final_score=final_score,
                rank_position=None,
            )

        mock_create.side_effect = create_result

        results = generate_committee_ranking(
            db=self.db,
            committee_id=5,
        )

        self.assertEqual(
            [assignment.id for assignment, _ in results],
            [20, 10],
        )

        self.assertEqual(
            [result.rank_position for _, result in results],
            [1, 2],
        )

        self.db.commit.assert_called_once()
        self.db.rollback.assert_not_called()

    @patch(f"{SERVICE}.create_or_update_evaluation_result")
    @patch(f"{SERVICE}.calculate_application_final_score")
    @patch(f"{SERVICE}.validate_ranking_completeness")
    @patch(f"{SERVICE}.get_evaluation_result_by_assignment")
    def test_result_failure_rolls_back_without_commit(
        self,
        mock_lookup,
        mock_validate,
        mock_score,
        mock_create,
    ):
        mock_lookup.return_value = None
        mock_score.return_value = Decimal("80.00")

        mock_create.side_effect = [
            SimpleNamespace(final_score=Decimal("80.00")),
            RuntimeError("Result creation failed"),
        ]

        with self.assertRaises(RuntimeError):
            generate_committee_ranking(
                db=self.db,
                committee_id=5,
            )

        self.db.commit.assert_not_called()
        self.db.rollback.assert_called_once()


if __name__ == "__main__":
    unittest.main()
