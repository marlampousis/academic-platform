
import json
import unittest
from pathlib import Path

from ai_benchmark.evaluators.test_05 import evaluate_test_05


BASE = Path(__file__).resolve().parents[1] / "ai_benchmark"

EXPECTED = json.loads(
    (BASE / "expected/test_05_expected.json").read_text(
        encoding="utf-8"
    )
)


def course_block(course):
    return "\n".join([
        f"Course Title: {course['course_title']}",
        f"Institution: {course['institution_name']}",
        f"Academic Year: {course['academic_year']}",
        f"Course Level: {course['course_level']}",
        f"Teaching Role: {course['teaching_role']}",
    ])


class TestEvaluator05(unittest.TestCase):

    def test_complete_multiline_course_records(self):
        response = "\n\n".join(
            course_block(course)
            for course in EXPECTED["expected_courses"]
        )

        result = evaluate_test_05(response, EXPECTED)

        self.assertEqual(result["course_f1"], 1.0)
        self.assertEqual(
            result["course_detail_accuracy"], 1.0
        )

    def test_missing_field_is_penalized(self):
        course = EXPECTED["expected_courses"][0]

        response = (
            f"Course Title: {course['course_title']}\n"
            f"Institution: {course['institution_name']}\n"
            f"Academic Year: {course['academic_year']}\n"
            f"Teaching Role: {course['teaching_role']}"
        )

        result = evaluate_test_05(response, EXPECTED)

        checks = result["course_detail_checks"][
            course["course_title"]
        ]

        self.assertFalse(checks["course_level"])

    def test_details_do_not_leak_between_courses(self):
        first = EXPECTED["expected_courses"][0]
        third = EXPECTED["expected_courses"][2]

        response = (
            f"Course Title: {first['course_title']}\n"
            f"Institution: {first['institution_name']}\n"
            f"Academic Year: {third['academic_year']}\n"
            f"Course Level: {third['course_level']}\n"
            f"Teaching Role: {first['teaching_role']}"
        )

        result = evaluate_test_05(response, EXPECTED)
        checks = result["course_detail_checks"][
            first["course_title"]
        ]

        self.assertFalse(checks["academic_year"])
        self.assertFalse(checks["course_level"])

    def test_no_invented_course(self):
        response = "\n\n".join(
            course_block(course)
            for course in EXPECTED["expected_courses"]
        )

        response += (
            "\n\nCourse Title: Quantum Computing\n"
            "Institution: University of Edinburgh\n"
            "Academic Year: 2024-2025\n"
            "Course Level: Postgraduate\n"
            "Teaching Role: Lecturer"
        )

        result = evaluate_test_05(response, EXPECTED)

        self.assertIn(
            "quantum computing",
            result["unexpected_courses"],
        )

    def test_invented_course_reduces_precision(self):
        response = "\n\n".join(
            course_block(course)
            for course in EXPECTED["expected_courses"]
        )

        response += (
            "\n\nCourse Title: Quantum Computing\n"
            "Institution: University of Edinburgh\n"
            "Academic Year: 2024-2025\n"
            "Course Level: Postgraduate\n"
            "Teaching Role: Lecturer"
        )

        result = evaluate_test_05(response, EXPECTED)

        self.assertAlmostEqual(
            result["course_precision"],
            3 / 4,
        )

        self.assertLess(result["course_f1"], 1.0)

    def test_invented_course_reduces_precision(self):
        response = "\n\n".join(
            course_block(course)
            for course in EXPECTED["expected_courses"]
        )

        response += (
            "\n\nCourse Title: Quantum Computing\n"
            "Institution: University of Edinburgh\n"
            "Academic Year: 2024-2025\n"
            "Course Level: Postgraduate\n"
            "Teaching Role: Lecturer"
        )

        result = evaluate_test_05(response, EXPECTED)

        self.assertIn(
            "quantum computing",
            result["unexpected_courses"],
        )

        self.assertAlmostEqual(
            result["course_precision"],
            0.75,
        )

        self.assertLess(result["course_f1"], 1.0)


if __name__ == "__main__":
    unittest.main()
