
import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from app.ai.services.candidate_context_service import (
    CandidateProfileAccessDenied,
    CandidateProfileNotFound,
    get_candidate_academic_context,
)


class TestCandidateContextService(unittest.TestCase):

    def make_db(self, profile_user_id=1):
        db = Mock()

        db.get.return_value = SimpleNamespace(
            id=10,
            user_id=profile_user_id,
            specialization="Artificial Intelligence",
            research_areas="Machine Learning",
        )

        records = [
            [
                SimpleNamespace(
                    id=5,
                    degree_type="PhD",
                    title="PhD in Computer Science",
                    field_of_study="Computer Science",
                    institution_name="Example University",
                    start_year=2018,
                    end_year=2022,
                ),
            ],
            [
                SimpleNamespace(
                    id=8,
                    title="Research in Machine Learning",
                    publication_year=2023,
                    publication_type="Journal",
                    doi="10.1234/example",
                    journal_name="Example Journal",
                ),
            ],
            [
                SimpleNamespace(
                    id=12,
                    title="Explainable AI",
                    role="Researcher",
                    status="Completed",
                    start_date=None,
                    end_date=None,
                    description="Research project on explainability",
                ),
            ],
            [
                SimpleNamespace(
                    id=20,
                    course_title="Machine Learning",
                    institution_name="Example University",
                    academic_year="2022-2023",
                    teaching_role="Lecturer",
                    hours_per_week=4,
                ),
            ],
        ]

        db.scalars.side_effect = [
            SimpleNamespace(all=lambda rows=rows: rows)
            for rows in records
        ]

        return db

    def test_aggregates_all_academic_collections(self):
        db = self.make_db()

        result = get_candidate_academic_context(
            db,
            profile_id=10,
            expected_user_id=1,
        )

        self.assertEqual(result.profile_id, 10)
        self.assertEqual(result.user_id, 1)
        self.assertEqual(len(result.degrees), 1)
        self.assertEqual(len(result.publications), 1)
        self.assertEqual(len(result.research_projects), 1)
        self.assertEqual(len(result.teaching_experience), 1)

        self.assertEqual(result.degrees[0].id, 5)
        self.assertEqual(result.publications[0].id, 8)
        self.assertEqual(result.research_projects[0].id, 12)
        self.assertEqual(result.teaching_experience[0].id, 20)

        self.assertEqual(db.scalars.call_count, 4)

    def test_profile_ownership_is_enforced(self):
        db = self.make_db(profile_user_id=2)

        with self.assertRaises(CandidateProfileAccessDenied):
            get_candidate_academic_context(
                db,
                profile_id=10,
                expected_user_id=1,
            )

        db.scalars.assert_not_called()

    def test_missing_profile_is_rejected(self):
        db = self.make_db()
        db.get.return_value = None

        with self.assertRaises(CandidateProfileNotFound):
            get_candidate_academic_context(
                db,
                profile_id=999,
                expected_user_id=1,
            )

        db.scalars.assert_not_called()

    def test_invalid_identifiers_are_rejected(self):
        db = self.make_db()

        with self.assertRaises(ValueError):
            get_candidate_academic_context(
                db,
                profile_id=0,
                expected_user_id=1,
            )

        with self.assertRaises(ValueError):
            get_candidate_academic_context(
                db,
                profile_id=10,
                expected_user_id=0,
            )

        db.get.assert_not_called()

    def test_empty_academic_collections_are_allowed(self):
        db = self.make_db()
        db.scalars.side_effect = [
            SimpleNamespace(all=lambda: [])
            for _ in range(4)
        ]

        result = get_candidate_academic_context(
            db,
            profile_id=10,
            expected_user_id=1,
        )

        self.assertEqual(result.degrees, [])
        self.assertEqual(result.publications, [])
        self.assertEqual(result.research_projects, [])
        self.assertEqual(result.teaching_experience, [])


if __name__ == "__main__":
    unittest.main()
