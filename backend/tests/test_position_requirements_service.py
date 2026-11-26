
import unittest

from app.ai.services.position_requirements_service import (
    PositionRequirementsService,
    PositionRequirementsError,
)

from types import SimpleNamespace
from unittest.mock import Mock

from app.ai.services.position_requirements_service import (
    extract_requirements_for_position,
)

from app.ai.services.position_context_service import (
    PositionNotFound,
)

POSITION_TEXT = (
    "Applicants must hold a PhD in Computer Science "
    "and demonstrate research experience in machine learning. "
    "University teaching experience is desirable."
)


def valid_result():
    return {
        "position_id": 999,
        "position_title": "Incorrect AI title",
        "requirements": [
            {
                "requirement_id": "AI-001",
                "category": "DEGREE",
                "priority": "REQUIRED",
                "description": "PhD in Computer Science",
                "source_excerpt":
                    "Applicants must hold a PhD in Computer Science",
            },
            {
                "requirement_id": "AI-002",
                "category": "TEACHING",
                "priority": "DESIRABLE",
                "description": "University teaching experience",
                "source_excerpt":
                    "University teaching experience is desirable.",
            },
        ],
    }


class FakeRunnable:
    def __init__(self, result):
        self.result = result

    def invoke(self, prompt):
        return self.result


class TestPositionRequirementsService(unittest.TestCase):

    def extract(self, result, description=POSITION_TEXT):
        service = PositionRequirementsService(
            FakeRunnable(result)
        )

        return service.extract(
            position_id=10,
            position_title="Assistant Professor in AI",
            position_description=description,
        )

    def test_valid_requirements_extracted(self):
        output = self.extract(valid_result())

        self.assertEqual(len(output.requirements), 2)
        self.assertEqual(
            output.requirements[0].priority.value,
            "REQUIRED",
        )
        self.assertEqual(
            output.requirements[1].priority.value,
            "DESIRABLE",
        )

    def test_backend_controls_position_identity(self):
        output = self.extract(valid_result())

        self.assertEqual(output.position_id, 10)
        self.assertEqual(
            output.position_title,
            "Assistant Professor in AI",
        )

    def test_backend_generates_requirement_ids(self):
        output = self.extract(valid_result())

        self.assertEqual(
            output.requirements[0].requirement_id,
            "REQ-001",
        )
        self.assertEqual(
            output.requirements[1].requirement_id,
            "REQ-002",
        )

    def test_fabricated_evidence_rejected(self):
        result = valid_result()

        result["requirements"][0]["source_excerpt"] = (
            "Applicants must have ten years of experience"
        )

        with self.assertRaises(PositionRequirementsError):
            self.extract(result)

    def test_duplicate_evidence_rejected(self):
        result = valid_result()
        result["requirements"].append(
            result["requirements"][0].copy()
        )

        with self.assertRaises(PositionRequirementsError):
            self.extract(result)

    def test_empty_description_rejected(self):
        with self.assertRaises(ValueError):
            self.extract(valid_result(), description="")

    def test_empty_requirements_allowed(self):
        output = self.extract({
            "position_id": 10,
            "position_title": "Assistant Professor in AI",
            "requirements": [],
        })

        self.assertEqual(output.requirements, [])

    def test_position_database_to_requirements_workflow(self):
        position = SimpleNamespace(
            id=10,
            title="Assistant Professor in AI",
            field_of_study="Artificial Intelligence",
            description=POSITION_TEXT,
        )

        db = Mock()
        db.get.return_value = position

        service = PositionRequirementsService(
            FakeRunnable(valid_result())
        )

        result = extract_requirements_for_position(
            db,
            position_id=10,
            extraction_service=service,
        )

        self.assertEqual(result.position_id, 10)
        self.assertEqual(
            result.position_title,
            "Assistant Professor in AI",
        )

        self.assertEqual(len(result.requirements), 2)

        self.assertEqual(
            result.requirements[0].requirement_id,
            "REQ-001",
        )

        self.assertEqual(
            result.requirements[1].priority.value,
            "DESIRABLE",
        )

    def test_missing_database_position_stops_ai_extraction(self):
        db = Mock()
        db.get.return_value = None

        runnable = Mock()
        service = PositionRequirementsService(runnable)

        with self.assertRaises(PositionNotFound):
            extract_requirements_for_position(
                db,
                position_id=999,
                extraction_service=service,
            )

        runnable.invoke.assert_not_called()

if __name__ == "__main__":
    unittest.main()