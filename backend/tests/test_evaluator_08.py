
import json
import unittest
from pathlib import Path

from ai_benchmark.evaluators.test_08 import (
    evaluate_test_08,
    validate_test_08_schema,
)


BASE = Path(__file__).resolve().parents[1] / "ai_benchmark"

EXPECTED = json.loads(
    (BASE / "expected/test_08_expected.json").read_text(
        encoding="utf-8"
    )
)

REFERENCE = EXPECTED["valid_publications"]


def publication(index=0, areas=None):
    reference = REFERENCE[index]

    if areas is None:
        areas = list(reference["acceptable_position_areas"][:2])

    return {
        "title": reference["title"],
        "publication_year": reference["publication_year"],
        "relevant_position_areas": areas,
        "evidence": "Evidence from the publication.",
    }


class TestEvaluator08(unittest.TestCase):

    def test_valid_publication(self):
        response = {
            "relevant_publications": [publication()]
        }

        result = evaluate_test_08(response, EXPECTED)

        self.assertTrue(result["schema_compliance"])
        self.assertEqual(result["publication_precision"], 1.0)
        self.assertEqual(result["publication_year_accuracy"], 1.0)
        self.assertEqual(result["position_area_accuracy"], 1.0)
        self.assertTrue(result["minimum_item_compliance"])
        self.assertTrue(result["maximum_item_compliance"])

    def test_empty_publications_fail_minimum(self):
        response = {"relevant_publications": []}

        result = evaluate_test_08(response, EXPECTED)

        self.assertTrue(result["schema_compliance"])
        self.assertFalse(result["minimum_item_compliance"])

    def test_blank_title_rejected(self):
        item = publication()
        item["title"] = "   "

        self.assertFalse(
            validate_test_08_schema(
                {"relevant_publications": [item]},
                EXPECTED,
            )
        )

    def test_empty_position_areas_rejected(self):
        item = publication(areas=[])

        self.assertFalse(
            validate_test_08_schema(
                {"relevant_publications": [item]},
                EXPECTED,
            )
        )

    def test_duplicate_publication_penalized(self):
        item = publication()
        response = {
            "relevant_publications": [item, item.copy()]
        }

        result = evaluate_test_08(response, EXPECTED)

        self.assertAlmostEqual(
            result["publication_precision"], 0.5
        )
        self.assertIn(
            item["title"],
            result["duplicate_publication_titles"],
        )

    def test_duplicate_area_penalized(self):
        item = publication(
            areas=[
                "Artificial Intelligence",
                "Artificial Intelligence",
            ]
        )

        result = evaluate_test_08(
            {"relevant_publications": [item]},
            EXPECTED,
        )

        self.assertAlmostEqual(
            result["position_area_accuracy"], 0.5
        )

        self.assertIn(
            "Artificial Intelligence",
            result["duplicate_position_areas"][item["title"]],
        )

    def test_unsupported_area_not_credited(self):
        item = publication(
            areas=["Quantum Computing"]
        )

        result = evaluate_test_08(
            {"relevant_publications": [item]},
            EXPECTED,
        )

        self.assertEqual(
            result["position_area_accuracy"], 0.0
        )

    def test_excess_publications_fail_maximum(self):
        response = {
            "relevant_publications": [
                publication(i) for i in range(4)
            ]
        }

        result = evaluate_test_08(response, EXPECTED)

        self.assertFalse(result["maximum_item_compliance"])


if __name__ == "__main__":
    unittest.main()
