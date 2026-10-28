
import json
import unittest
from pathlib import Path

from ai_benchmark.evaluators.test_02 import (
    calculate_category_presence,
    evaluate_test_02,
)


BASE = Path(__file__).resolve().parents[1] / "ai_benchmark"

EXPECTED = json.loads(
    (BASE / "expected/test_02_expected.json").read_text(
        encoding="utf-8"
    )
)

CASE_A = EXPECTED["cases"][0]


class TestEvaluator02(unittest.TestCase):

    def test_publication_and_project_mentions(self):
        response = (
            "The candidate has authored journal articles "
            "and conference papers and participated as "
            "a researcher in a completed project."
        )

        result = calculate_category_presence(
            response,
            CASE_A["required_facts"],
        )

        self.assertTrue(
            result["category_presence_checks"]["publications"]
        )
        self.assertTrue(
            result["category_presence_checks"]["research_projects"]
        )

    def test_negative_mentions_not_credited(self):
        response = (
            "The candidate has no publications "
            "and no research projects."
        )

        result = calculate_category_presence(
            response,
            CASE_A["required_facts"],
        )

        self.assertFalse(
            result["category_presence_checks"]["publications"]
        )
        self.assertFalse(
            result["category_presence_checks"]["research_projects"]
        )

    def test_exact_title_score_preserved(self):
        response = (
            "The candidate authored journal articles "
            "and participated in a completed research project."
        )

        result = evaluate_test_02(response, CASE_A)

        self.assertFalse(
            result["required_facts_checks"]["publications"]
        )
        self.assertTrue(
            result["category_presence_checks"]["publications"]
        )

    def test_unrelated_text_not_credited(self):
        response = (
            "The candidate specializes in Artificial Intelligence."
        )

        result = calculate_category_presence(
            response,
            CASE_A["required_facts"],
        )

        self.assertFalse(
            result["category_presence_checks"]["publications"]
        )
        self.assertFalse(
            result["category_presence_checks"]["research_projects"]
        )


if __name__ == "__main__":
    unittest.main()
