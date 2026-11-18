
import unittest

from langchain_core.runnables import RunnableLambda

from app.ai.schemas.extraction import (
    AcademicCVExtraction,
    EvidenceReference,
    ExtractedDegree,
)
from app.ai.services.extraction_service import (
    AcademicExtractionService,
    AIExtractionError,
)


CV_TEXT = (
    "Alex Morgan holds a PhD in Computer Science "
    "from Example University, completed in 2022."
)


def make_extraction(excerpt="PhD in Computer Science"):
    return AcademicCVExtraction(
        degrees=[
            ExtractedDegree(
                degree_type="PhD",
                title="PhD in Computer Science",
                institution_name="Example University",
                end_year=2022,
                evidence=[
                    EvidenceReference(
                        source_id="synthetic-cv-001",
                        excerpt=excerpt,
                    )
                ],
            )
        ]
    )


class TestAcademicExtractionService(unittest.TestCase):

    def test_successful_extraction(self):
        runnable = RunnableLambda(
            lambda prompt: make_extraction()
        )

        service = AcademicExtractionService(runnable)
        result = service.extract(CV_TEXT)

        self.assertIsInstance(result, AcademicCVExtraction)
        self.assertEqual(result.degrees[0].end_year, 2022)

    def test_empty_cv_rejected(self):
        runnable = RunnableLambda(
            lambda prompt: make_extraction()
        )

        service = AcademicExtractionService(runnable)

        with self.assertRaises(ValueError):
            service.extract("")

    def test_fabricated_evidence_rejected(self):
        runnable = RunnableLambda(
            lambda prompt: make_extraction(
                "PhD in Quantum Teleportation"
            )
        )

        service = AcademicExtractionService(runnable)

        with self.assertRaises(AIExtractionError):
            service.extract(CV_TEXT)

    def test_provider_failure_handled(self):
        def failing_model(prompt):
            raise RuntimeError("Simulated provider failure")

        service = AcademicExtractionService(
            RunnableLambda(failing_model)
        )

        with self.assertRaises(AIExtractionError):
            service.extract(CV_TEXT)

    def test_missing_evidence_rejected(self):
        extraction = make_extraction()
        extraction.degrees[0].evidence = []

        service = AcademicExtractionService(
            RunnableLambda(lambda prompt: extraction)
        )

        with self.assertRaises(AIExtractionError):
            service.extract(CV_TEXT)


if __name__ == "__main__":
    unittest.main()
