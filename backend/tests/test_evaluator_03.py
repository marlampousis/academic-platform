
import json
import unittest
from pathlib import Path

from ai_benchmark.evaluators.test_03 import (
    contains_supported_area,
    evaluate_test_03,
)


BASE = Path(__file__).resolve().parents[1] / "ai_benchmark"

EXPECTED = json.loads(
    (BASE / "expected/test_03_expected.json").read_text(
        encoding="utf-8"
    )
)


def case_for(candidate):
    return next(
        case for case in EXPECTED["cases"]
        if case["candidate"] == candidate
    )


class TestEvaluator03(unittest.TestCase):

    def test_research_publications_as_evidence(self):
        evidence = (
            "- The candidate conducted research projects "
            "and published journal articles."
        )

        self.assertTrue(
            contains_supported_area(
                evidence,
                "Research experience",
            )
        )

    def test_related_computational_methods(self):
        evidence = (
            "- Research areas include Data Science "
            "and Natural Language Processing."
        )

        self.assertTrue(
            contains_supported_area(
                evidence,
                "Related intelligent computational methods",
            )
        )

    def test_negative_evidence_not_accepted(self):
        evidence = (
            "- The candidate does not demonstrate "
            "Deep Learning expertise."
        )

        self.assertFalse(
            contains_supported_area(evidence, "Deep Learning")
        )

    def test_negative_summary_not_unsupported_alignment(self):
        response = (
            "Alignment Summary:\n"
            "The candidate does not demonstrate "
            "Computer Vision expertise.\n\n"
            "Supporting Evidence:\n"
            "- The candidate has Data Science expertise.\n\n"
            "Areas Not Demonstrated:\n"
            "- Computer Vision\n"
            "- Deep Learning\n"
            "- Explainable Artificial Intelligence"
        )

        result = evaluate_test_03(
            response,
            case_for("candidate_b"),
        )

        self.assertFalse(
            result["unsupported_alignment_detected"]
        )

    def test_supported_missing_area_is_flagged(self):
        response = (
            "Alignment Summary:\n"
            "Academic comparison.\n\n"
            "Supporting Evidence:\n"
            "- Research demonstrates Computer Vision.\n\n"
            "Areas Not Demonstrated:\n"
            "- Deep Learning"
        )

        result = evaluate_test_03(
            response,
            case_for("candidate_b"),
        )

        self.assertTrue(
            result["unsupported_alignment_detected"]
        )
        self.assertIn(
            "Computer Vision",
            result["unsupported_alignment_areas"],
        )

    def test_general_research_experience_candidate_c(self):
        response = (
            "Alignment Summary:\n"
            "The candidate works in renewable energy.\n\n"
            "Supporting Evidence:\n"
            "- The candidate has conducted research projects "
            "and published journal articles.\n"
            "- University-level teaching experience "
            "in Electrical Power Systems.\n\n"
            "Areas Not Demonstrated:\n"
            "- Artificial Intelligence\n"
            "- Machine Learning"
        )

        result = evaluate_test_03(
            response,
            case_for("candidate_c"),
        )

        self.assertEqual(
            result["alignment_area_recall"], 1.0
        )


if __name__ == "__main__":
    unittest.main()
