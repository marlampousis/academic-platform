
import unittest

from pydantic import ValidationError

from app.ai.schemas.matching import (
    AcademicRequirement,
    AcademicMatchingDraft,
    PositionRequirements,
)


class TestAIMatchingSchemas(unittest.TestCase):

    def test_valid_position_requirements(self):
        result = PositionRequirements.model_validate({
            "position_id": 1,
            "position_title": "Assistant Professor in AI",
            "requirements": [
                {
                    "requirement_id": "REQ-001",
                    "category": "DEGREE",
                    "priority": "REQUIRED",
                    "description": "PhD in a related field",
                    "source_excerpt": "PhD in a related field",
                }
            ],
        })

        self.assertEqual(len(result.requirements), 1)

    def test_invalid_priority_rejected(self):
        with self.assertRaises(ValidationError):
            AcademicRequirement.model_validate({
                "requirement_id": "REQ-001",
                "category": "DEGREE",
                "priority": "UNKNOWN",
                "description": "PhD required",
                "source_excerpt": "PhD required",
            })

    def test_invalid_evidence_id_rejected(self):
        with self.assertRaises(ValidationError):
            AcademicMatchingDraft.model_validate({
                "application_id": 1,
                "position_id": 2,
                "profile_id": 3,
                "summary": "Human review required",
                "matches": [
                    {
                        "requirement_id": "REQ-001",
                        "finding": "SUPPORTED",
                        "explanation": "Degree found",
                        "evidence": [
                            {
                                "collection": "degrees",
                                "record_id": -1,
                            }
                        ],
                    }
                ],
            })

    def test_unknown_evidence_collection_rejected(self):
        with self.assertRaises(ValidationError):
            AcademicMatchingDraft.model_validate({
                "application_id": 1,
                "position_id": 2,
                "profile_id": 3,
                "summary": "Human review required",
                "matches": [
                    {
                        "requirement_id": "REQ-001",
                        "finding": "SUPPORTED",
                        "explanation": "Evidence found",
                        "evidence": [
                            {
                                "collection": "unknown_table",
                                "record_id": 1,
                            }
                        ],
                    }
                ],
            })


if __name__ == "__main__":
    unittest.main()
