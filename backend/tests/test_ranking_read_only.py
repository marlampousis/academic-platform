
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from app.evaluation_results.router import read_ranking


class TestRankingReadOnly(unittest.TestCase):

    @patch(
        "app.evaluation_results.router."
        "generate_committee_ranking"
    )
    @patch(
        "app.evaluation_results.router."
        "get_committee_ranking",
        return_value=[],
    )
    @patch(
        "app.evaluation_results.router."
        "get_evaluation_committee_by_id"
    )
    def test_read_ranking_does_not_generate_results(
        self,
        mock_committee,
        mock_read,
        mock_generate,
    ):
        db = MagicMock()

        mock_committee.return_value = SimpleNamespace(
            id=10,
            status="COMPLETED",
        )

        result = read_ranking(
            committee_id=10,
            db=db,
            current_admin=SimpleNamespace(
                id=1,
                role="SUPER_ADMIN",
            ),
        )

        self.assertEqual(result, [])

        mock_read.assert_called_once_with(
            db=db,
            committee_id=10,
        )

        mock_generate.assert_not_called()
        db.commit.assert_not_called()


if __name__ == "__main__":
    unittest.main()
