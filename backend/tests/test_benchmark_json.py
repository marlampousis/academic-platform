import unittest
import sys
from pathlib import Path
from unittest.mock import patch

from ai_benchmark.providers.base import ModelResponse

from ai_benchmark.evaluators.test_11 import evaluate_test_11, _valid_structure

BENCHMARK_DIR = (
    Path(__file__).resolve().parents[1]
    / "ai_benchmark"
)

sys.path.insert(0, str(BENCHMARK_DIR))

from ai_benchmark import benchmark

parse_model_response = benchmark.parse_model_response
execute_run = benchmark.execute_run

class TestBenchmarkJSON(unittest.TestCase):

    def test_invalid_json_is_detected(self):
        raw_response = '{"name": "Mario"'

        result = parse_model_response(
            test_id="test_11_greek_json",
            raw_response=raw_response,
        )

        self.assertIsNone(result["parsed_response"])
        self.assertFalse(result["json_validity"])
        self.assertIsNotNone(result["parse_error"])

    def test_valid_json_is_accepted(self):
        raw_response = '{"name": "Mario"}'

        result = parse_model_response(
            test_id="test_11_greek_json",
            raw_response=raw_response,
        )

        self.assertEqual(
            result["parsed_response"],
            {"name": "Mario"},
        )
        self.assertTrue(result["json_validity"])
        self.assertIsNone(result["parse_error"])

    def test_raw_text_does_not_require_json(self):
        result = parse_model_response(
            test_id="test_02_summary",
            raw_response="Academic summary",
        )

        self.assertEqual(
            result["parsed_response"],
            "Academic summary",
        )
        self.assertIsNone(result["json_validity"])

    def test_invalid_json_through_execute_run(self):
        from tempfile import TemporaryDirectory
        from pathlib import Path
        from unittest.mock import Mock

        invalid_json = '{"name": "Mario"'

        provider = Mock()
        provider.provider_name = "fake-gemini"
        provider.model_name = "fake-model"

        provider.generate.return_value = ModelResponse(
            text=invalid_json,
            latency_ms=10.0,
            error=False,
            error_message=None,
        )

        with TemporaryDirectory() as temp_dir:
            expected_file = Path(temp_dir) / "expected.json"
            expected_file.write_text(
                '{"expected": {}}',
                encoding="utf-8",
            )

            run_specification = {
                "test_id": "test_11_greek_json",
                "case_id": "test_case",
                "run_number": 1,
                "rendered_prompt": "Return structured JSON",
                "expected_file": expected_file,
                "automatic_metrics": [],
                "qualitative_metrics": [],
                "safety_metrics": [],
            }

            with patch.object(
                benchmark,
                "resolve_expected_data",
                return_value={},
            ), patch.object(
                benchmark,
                "evaluate_automatic_metrics",
                return_value={
                    "schema_compliance": False,
                    "publication_f1": 0.0,
                },
            ) as evaluate_mock:

                result = execute_run(
                    run_specification,
                    provider,
                )

        self.assertFalse(result["error"])
        self.assertEqual(result["raw_response"], invalid_json)
        self.assertIsNone(result["parsed_response"])
        self.assertFalse(result["json_validity"])
        self.assertIsNotNone(result["parse_error"])

        evaluate_mock.assert_called_once()

        self.assertIsNone(
            evaluate_mock.call_args.kwargs["parsed_response"]
        )
        self.assertFalse(
            evaluate_mock.call_args.kwargs["json_validity"]
        )

    def test_invalid_json_receives_zero_test_11_scores(self):
        invalid_json = '{"name": "Mario"'

        parsing_result = parse_model_response(
            test_id="test_11_greek_json",
            raw_response=invalid_json,
        )

        expected_data = {
            "expected_schema": {
                "required_top_level_fields": [
                    "name",
                    "institution",
                    "department",
                    "highest_degree",
                    "publications",
                    "research_projects",
                    "teaching_experience",
                ]
            },
            "expected": {},
            "nested_schema": {},
        }

        metrics = evaluate_test_11(
            parsed_response=parsing_result["parsed_response"],
            expected_data=expected_data,
        )

        self.assertFalse(parsing_result["json_validity"])
        self.assertFalse(metrics["schema_compliance"])
        self.assertFalse(metrics["exact_keys"])
        self.assertFalse(metrics["highest_degree_selection"])
        self.assertEqual(metrics["publication_f1"], 0.0)
        self.assertEqual(metrics["teaching_f1"], 0.0)
        self.assertEqual(metrics["research_project_accuracy"], 0.0)
        self.assertEqual(metrics["greek_value_consistency"], 0.0)

    def test_test11_rejects_wrong_scalar_types(self):
        expected = {
            "year": 2023,
            "title": "Academic publication",
            "verified": True,
        }

        actual = {
            "year": "2023",
            "title": 123,
            "verified": 1,
        }

        self.assertFalse(_valid_structure(actual, expected))


    def test_test11_accepts_correct_scalar_types(self):
        expected = {
            "year": 2023,
            "title": "Academic publication",
            "verified": True,
        }

        actual = {
            "year": 2024,
            "title": "Another publication",
            "verified": False,
        }

        self.assertTrue(_valid_structure(actual, expected))


    def test_test11_rejects_wrong_nested_types(self):
        expected = {
            "publications": [
                {"title": "Paper", "year": 2023}
            ]
        }

        actual = {
            "publications": [
                {"title": "Paper", "year": "2023"}
            ]
        }

        self.assertFalse(_valid_structure(actual, expected))

    def test_invalid_json_with_real_test11_evaluator(self):
        from pathlib import Path
        from unittest.mock import Mock

        provider = Mock()
        provider.provider_name = "fake-gemini"
        provider.model_name = "fake-model"
        provider.generate.return_value = ModelResponse(
            text='{"incomplete": ',
            latency_ms=10.0,
            error=False,
            error_message=None,
        )

        expected_file = (
            Path(__file__).resolve().parents[1]
            / "ai_benchmark"
            / "expected"
            / "test_11_expected.json"
        )

        run_specification = {
            "test_id": "test_11_greek_json",
            "case_id": "candidate_a_gr",
            "run_number": 1,
            "rendered_prompt": "Return structured academic JSON",
            "expected_file": expected_file,
            "automatic_metrics": [],
            "qualitative_metrics": [],
            "safety_metrics": [],
        }

        result = execute_run(
            run_specification=run_specification,
            provider=provider,
        )

        self.assertFalse(result["error"])
        self.assertFalse(result["json_validity"])
        self.assertIsNone(result["parsed_response"])

        metrics = result["automatic_metrics"]

        self.assertFalse(metrics["schema_compliance"])
        self.assertFalse(metrics["exact_keys"])
        self.assertEqual(metrics["publication_f1"], 0.0)
        self.assertEqual(metrics["teaching_f1"], 0.0)
        self.assertEqual(
            metrics["research_project_accuracy"], 0.0
        )
if __name__ == "__main__":
    unittest.main()