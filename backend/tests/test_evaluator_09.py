
import json
import unittest
from pathlib import Path

from ai_benchmark.evaluators.test_09 import evaluate_test_09


BASE = Path(__file__).resolve().parents[1] / "ai_benchmark"

EXPECTED = json.loads(
    (BASE / "expected/test_09_expected.json").read_text(
        encoding="utf-8"
    )
)


def score(candidate, requirements):
    case = next(
        item for item in EXPECTED["cases"]
        if item["candidate"] == candidate
    )

    response = {
        "potential_gaps": [
            {
                "position_requirement": requirement,
                "candidate_evidence_status": "not_demonstrated",
                "explanation": "Evidence not demonstrated.",
            }
            for requirement in requirements
        ],
        "limitations": (
            "Absence of evidence does not prove "
            "absence of qualifications."
        ),
    }

    return evaluate_test_09(
        response,
        case,
        EXPECTED["expected_schema"],
    )


class TestEvaluator09(unittest.TestCase):

    def test_candidate_a_no_gaps(self):
        result = score("candidate_a", [])
        self.assertEqual(result["gap_f1"], 1.0)

    def test_candidate_b_descriptive_requirements(self):
        result = score("candidate_b", [
            "Research and teaching experience in Deep Learning",
            "Research and teaching experience in Computer Vision",
            "Research and teaching experience in "
            "Explainable Artificial Intelligence",
        ])
        self.assertEqual(result["gap_f1"], 1.0)

    def test_candidate_c_grouped_requirements(self):
        result = score("candidate_c", [
            "Artificial Intelligence and Machine Learning, "
            "including Deep Learning, Computer Vision and "
            "Explainable Artificial Intelligence"
        ])
        self.assertEqual(result["gap_recall"], 1.0)
        self.assertEqual(result["gap_precision"], 1.0)

    def test_unrelated_gap_is_not_credited(self):
        result = score("candidate_b", [
            "Renewable Energy Systems"
        ])
        self.assertEqual(result["gap_f1"], 0.0)

    def test_duplicate_requirement_is_penalized(self):
        result = score("candidate_b", [
            "Deep Learning",
            "Deep Learning",
        ])
        self.assertLess(result["gap_precision"], 1.0)

    def test_partial_word_is_not_matched(self):
        result = score("candidate_b", [
            "Computer Visionary Methods"
        ])
        self.assertEqual(result["gap_f1"], 0.0)


if __name__ == "__main__":
    unittest.main()
