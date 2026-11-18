
import unittest

from pydantic import ValidationError

from app.ai.schemas.extraction import (
    AcademicCVExtraction,
    EvidenceReference,
    ExtractedDegree,
    ExtractedPublication,
    ExtractedResearchProject,
    ExtractionIssue,
    IssueType,
)


class TestAcademicCVExtraction(unittest.TestCase):

    def test_valid_extraction(self):
        extraction = AcademicCVExtraction(
            specialization="Artificial Intelligence",
            research_areas="Machine Learning, Computer Vision",
            degrees=[
                ExtractedDegree(
                    degree_type="PhD",
                    title="PhD in Computer Science",
                    institution_name="Example University",
                    field_of_study="Computer Science",
                    end_year=2022,
                    evidence=[
                        EvidenceReference(
                            source_id="cv-test-001",
                            excerpt="PhD in Computer Science",
                        )
                    ],
                )
            ],
            publications=[
                ExtractedPublication(
                    title="Machine Learning Research",
                    publication_year=2023,
                )
            ],
        )

        self.assertEqual(len(extraction.degrees), 1)
        self.assertEqual(len(extraction.publications), 1)
        self.assertEqual(extraction.degrees[0].end_year, 2022)

    def test_missing_information(self):
        extraction = AcademicCVExtraction(
            issues=[
                ExtractionIssue(
                    field_path="teaching_experience",
                    issue_type=IssueType.MISSING,
                    explanation="No teaching experience was provided.",
                )
            ]
        )

        self.assertEqual(
            extraction.issues[0].issue_type,
            IssueType.MISSING,
        )

    def test_invalid_degree_years(self):
        with self.assertRaises(ValidationError):
            ExtractedDegree(
                degree_type="PhD",
                title="Computer Science",
                institution_name="Example University",
                start_year=2024,
                end_year=2022,
            )

    def test_invalid_project_dates(self):
        with self.assertRaises(ValidationError):
            ExtractedResearchProject(
                title="AI Research Project",
                start_date="2024-01-01",
                end_date="2023-01-01",
            )

    def test_invalid_evidence_offsets(self):
        with self.assertRaises(ValidationError):
            EvidenceReference(
                source_id="cv-test-001",
                excerpt="PhD",
                start_char=100,
                end_char=50,
            )


if __name__ == "__main__":
    unittest.main()
