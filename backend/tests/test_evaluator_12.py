import unittest

from ai_benchmark.evaluators.test_12 import normalize_text


class TestEvaluator12(unittest.TestCase):

    def test_optional_candidate_prefix(self):
        expected = (
            "The candidate has more than 10 years "
            "of university-level teaching experience."
        )
        actual = (
            "has more than 10 years "
            "of university-level teaching experience"
        )

        self.assertEqual(
            normalize_text(actual),
            normalize_text(expected),
        )

    def test_phd_claim_punctuation(self):
        expected = (
            "The candidate has a PhD in Computer Science "
            "from the University of Edinburgh."
        )
        actual = (
            "The candidate has a PhD in Computer Science "
            "from the University of Edinburgh"
        )

        self.assertEqual(
            normalize_text(actual),
            normalize_text(expected),
        )

    def test_preserve_meaningful_numbers(self):
        claim_10 = "has more than 10 years of teaching"
        claim_5 = "has more than 5 years of teaching"

        self.assertNotEqual(
            normalize_text(claim_10),
            normalize_text(claim_5),
        )

    def test_preserve_negation(self):
        positive = "has published research in Computer Vision"
        negative = "has not published research in Computer Vision"

        self.assertNotEqual(
            normalize_text(positive),
            normalize_text(negative),
        )


    def test_no_contradicted_claims_is_not_applicable(self):
        import json
        from pathlib import Path
        from ai_benchmark.evaluators.test_12 import evaluate_test_12

        expected = json.loads(
            (
                Path(__file__).resolve().parents[1]
                / "ai_benchmark/expected/test_12_expected.json"
            ).read_text(encoding="utf-8")
        )

        response = {
            "claims": [
                {
                    "claim": item["claim"],
                    "status": item["expected_status"],
                    "evidence": "Reference evidence",
                }
                for item in expected["expected_claims"]
            ],
            "overall_assessment": "Test assessment",
        }

        metrics = evaluate_test_12(response, expected)

        self.assertEqual(
            metrics["claim_classification_accuracy"], 1.0
        )
        self.assertIsNone(
            metrics["unsupported_contradicted_distinction"]
        )


if __name__ == "__main__":
    unittest.main()