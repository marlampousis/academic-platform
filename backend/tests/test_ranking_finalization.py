
import unittest
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from fastapi import HTTPException

from app.evaluation_results.service import (
    generate_committee_ranking,
    set_final_decision,
)


class TestRankingFinalization(unittest.TestCase):

    @patch(
        "app.evaluation_results.service."
        "get_evaluation_result_by_assignment"
    )
    def test_finalized_result_blocks_regeneration(
        self,
        mock_lookup,
    ):
        db = MagicMock()

        db.query.return_value.filter.return_value.all.return_value = [
            SimpleNamespace(id=25, committee_id=10)
        ]

        mock_lookup.return_value = SimpleNamespace(
            decision="APPROVED",
        )

        with self.assertRaises(HTTPException) as context:
            generate_committee_ranking(
                db=db,
                committee_id=10,
            )

        self.assertEqual(context.exception.status_code, 409)
        db.commit.assert_not_called()

    def test_final_decision_cannot_be_overwritten(self):
        db = MagicMock()

        result = SimpleNamespace(
            decision="APPROVED",
            final_score=Decimal("85.00"),
            final_comment="Original decision",
            decided_by=1,
        )

        with self.assertRaises(HTTPException) as context:
            set_final_decision(
                db=db,
                result=result,
                decision="REJECTED",
                final_comment="Changed decision",
                decided_by=2,
            )

        self.assertEqual(context.exception.status_code, 409)
        self.assertEqual(result.decision, "APPROVED")
        self.assertEqual(
            result.final_comment,
            "Original decision",
        )
        db.commit.assert_not_called()


if __name__ == "__main__":
    unittest.main()
