
import json
import unittest
from pathlib import Path

from ai_benchmark.evaluators.test_04 import (
    evaluate_test_04,
    expand_position_area,
)


BASE = Path(__file__).resolve().parents[1] / "ai_benchmark"

EXPECTED = json.loads(
    (BASE / "expected/test_04_expected.json").read_text(
        encoding="utf-8"
    )
)


def case_for(candidate):
    return next(
        case for case in EXPECTED["cases"]
        if case["candidate"] == candidate
    )


class TestEvaluator04(unittest.TestCase):

    def test_exact_area(self):
        areas = {
            "artificial intelligence",
            "machine learning",
        }

        result = expand_position_area(
            "Artificial Intelligence",
            areas,
        )

        self.assertEqual(
            result,
            {"artificial intelligence"},
        )

    def test_grouped_ai_ml(self):
        areas = {
            "artificial intelligence",
            "machine learning",
        }

        result = expand_position_area(
            "Artificial Intelligence and Machine Learning",
            areas,
        )

        self.assertEqual(result, areas)

    def test_broad_description_not_accepted(self):
        areas = {"artificial intelligence"}

        result = expand_position_area(
            "Applying modern artificial intelligence "
            "methods to real-world problems",
            areas,
        )

        self.assertEqual(result, set())

    def test_missing_aligned_areas_are_penalized(self):
        response = {
            "aligned_areas": [],
            "areas_not_demonstrated": [
                {
                    "position_area": area,
                    "explanation": "No evidence found.",
                }
                for area in [
                    "Deep Learning",
                    "Computer Vision",
                    "Explainable Artificial Intelligence",
                ]
            ],
            "overall_explanation": "Evidence-based assessment.",
        }

        result = evaluate_test_04(
            response,
            case_for("candidate_b"),
        )

        self.assertEqual(
            result["alignment_area_recall"],
            0.0,
        )

        self.assertEqual(
            result["missing_evidence_accuracy"],
            1.0,
        )

    def test_grouped_missing_areas_partial_credit(self):
        response = {
            "aligned_areas": [],
            "areas_not_demonstrated": [
                {
                    "position_area":
                        "Artificial Intelligence and Machine Learning",
                    "explanation": "Not demonstrated.",
                }
            ],
            "overall_explanation": "Evidence-based assessment.",
        }

        result = evaluate_test_04(
            response,
            case_for("candidate_c"),
        )

        self.assertAlmostEqual(
            result["missing_evidence_accuracy"],
            0.4,
        )

    def test_grouped_alignment_contradiction(self):
        response = {
            "aligned_areas": [
                {
                    "position_area":
                        "Artificial Intelligence and Machine Learning",
                    "candidate_evidence": [
                        "Artificial Intelligence specialization",
                        "Machine Learning research area",
                    ],
                    "explanation": "Both areas demonstrated.",
                }
            ],
            "areas_not_demonstrated": [
                {
                    "position_area": "Machine Learning",
                    "explanation": "Not demonstrated.",
                }
            ],
            "overall_explanation": "Conflicting assessment.",
        }

        result = evaluate_test_04(
            response,
            case_for("candidate_a"),
        )

        self.assertFalse(result["logical_consistency"])
        self.assertIn(
            "machine learning",
            result["contradictory_areas"],
        )


    def test_duplicate_grouped_aligned_area(self):
        response = {
            "aligned_areas": [
                {
                    "position_area":
                        "Artificial Intelligence and Machine Learning",
                    "candidate_evidence": [
                        "Artificial Intelligence specialization",
                        "Machine Learning",
                    ],
                    "explanation": "Both areas demonstrated.",
                },
                {
                    "position_area": "Machine Learning",
                    "candidate_evidence": ["Machine Learning"],
                    "explanation": "Machine Learning demonstrated.",
                },
            ],
            "areas_not_demonstrated": [],
            "overall_explanation": "Assessment.",
        }

        result = evaluate_test_04(
            response,
            case_for("candidate_a"),
        )

        self.assertIn(
            "machine learning",
            result["duplicate_aligned_areas"],
        )
        self.assertFalse(result["logical_consistency"])
        self.assertAlmostEqual(
            result["alignment_area_precision"],
            2 / 3,
        )

    def test_duplicate_grouped_missing_area(self):
        response = {
            "aligned_areas": [],
            "areas_not_demonstrated": [
                {
                    "position_area":
                        "Artificial Intelligence and Machine Learning",
                    "explanation": "Not demonstrated.",
                },
                {
                    "position_area": "Machine Learning",
                    "explanation": "Not demonstrated.",
                },
            ],
            "overall_explanation": "Assessment.",
        }

        result = evaluate_test_04(
            response,
            case_for("candidate_c"),
        )

        self.assertIn(
            "machine learning",
            result["duplicate_missing_areas"],
        )
        self.assertFalse(result["logical_consistency"])

    def test_unacceptable_evidence_not_credited(self):
        response = {
            "aligned_areas": [
                {
                    "position_area": "Computer Vision",
                    "candidate_evidence": [
                        "Unrelated publication on renewable energy",
                    ],
                    "explanation": "Computer Vision demonstrated.",
                }
            ],
            "areas_not_demonstrated": [],
            "overall_explanation": "Assessment.",
        }

        result = evaluate_test_04(
            response,
            case_for("candidate_a"),
        )

        self.assertFalse(
            result["evidence_checks"]["computer vision"]
        )

if __name__ == "__main__":
    unittest.main()
