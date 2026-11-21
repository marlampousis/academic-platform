
import unittest

import app.core.model_registry

from sqlalchemy import select

from app.ai.models import AIReviewEvent
from app.ai.schemas.approval import ExtractionApprovalRequest
from app.ai.services.approval_service import (
    approve_extraction,
    ApprovalConflict,
    ApprovalValidationError,
)
from app.ai.services.review_service import apply_extraction_review

from app.profiles.models import AcademicProfile
from app.degrees.models import Degree
from app.publications.models import Publication

from db_setup import isolated_test_session
from test_ai_review import (
    create_test_user,
    create_test_artifact,
    make_request,
)


def prepare_candidate(db, create_profile=True):
    user = create_test_user(db)

    profile = None

    if create_profile:
        profile = AcademicProfile(user_id=user.id)
        db.add(profile)
        db.flush()

    artifact = create_test_artifact(db, user.id)
    return user, profile, artifact


def review_degree_and_publication(
    db,
    user,
    artifact,
    publication_decision="EDIT",
):
    apply_extraction_review(
        db,
        artifact_id=artifact.id,
        candidate_user_id=user.id,
        request=make_request(
            "degrees", 0, "ACCEPT",
            expected_version=1,
        ),
    )

    changes = (
        {"publication_year": 2024}
        if publication_decision == "EDIT"
        else None
    )

    apply_extraction_review(
        db,
        artifact_id=artifact.id,
        candidate_user_id=user.id,
        request=make_request(
            "publications",
            0,
            publication_decision,
            corrected_data=changes,
            expected_version=2,
        ),
    )


def approve(db, user, artifact, version=3, confirm=True):
    return approve_extraction(
        db,
        artifact_id=artifact.id,
        candidate_user_id=user.id,
        request=ExtractionApprovalRequest(
            expected_version=version,
            confirm=confirm,
        ),
    )


class TestAIApproval(unittest.TestCase):

    def test_corrected_publication_is_persisted(self):
        with isolated_test_session() as db:
            user, profile, artifact = prepare_candidate(db)

            review_degree_and_publication(db, user, artifact)

            result, counts = approve(db, user, artifact)

            self.assertEqual(result.status, "APPROVED")
            self.assertEqual(result.version, 4)
            self.assertEqual(counts["degrees"], 1)
            self.assertEqual(counts["publications"], 1)

            publication = db.execute(
                select(Publication).where(
                    Publication.profile_id == profile.id
                )
            ).scalar_one()

            self.assertEqual(publication.publication_year, 2024)
            self.assertEqual(
                publication.title,
                "Machine Learning in Education",
            )

            # The original Gemini result remains preserved.
            self.assertEqual(
                result.payload_json["publications"][0][
                    "publication_year"
                ],
                2021,
            )

            event = db.execute(
                select(AIReviewEvent).where(
                    AIReviewEvent.artifact_id == result.id,
                    AIReviewEvent.action == "FINAL_APPROVAL",
                )
            ).scalar_one()

            self.assertEqual(event.reviewer_id, user.id)

    def test_rejected_publication_is_not_saved(self):
        with isolated_test_session() as db:
            user, profile, artifact = prepare_candidate(db)

            review_degree_and_publication(
                db, user, artifact,
                publication_decision="REJECT",
            )

            result, counts = approve(db, user, artifact)

            self.assertEqual(result.status, "APPROVED")
            self.assertEqual(counts["degrees"], 1)
            self.assertEqual(counts["publications"], 0)

            publications = db.execute(
                select(Publication).where(
                    Publication.profile_id == profile.id
                )
            ).scalars().all()

            self.assertEqual(len(publications), 0)

    def test_incomplete_review_is_rejected(self):
        with isolated_test_session() as db:
            user, profile, artifact = prepare_candidate(db)

            apply_extraction_review(
                db,
                artifact_id=artifact.id,
                candidate_user_id=user.id,
                request=make_request(
                    "degrees", 0, "ACCEPT",
                ),
            )

            with self.assertRaises(ApprovalValidationError):
                approve(db, user, artifact, version=2)

            degrees = db.execute(
                select(Degree).where(
                    Degree.profile_id == profile.id
                )
            ).scalars().all()

            self.assertEqual(len(degrees), 0)
            self.assertEqual(artifact.status, "IN_REVIEW")

    def test_second_approval_is_rejected(self):
        with isolated_test_session() as db:
            user, profile, artifact = prepare_candidate(db)

            review_degree_and_publication(db, user, artifact)

            approve(db, user, artifact)

            with self.assertRaises(ApprovalConflict):
                approve(db, user, artifact, version=4)

            publications = db.execute(
                select(Publication).where(
                    Publication.profile_id == profile.id
                )
            ).scalars().all()

            self.assertEqual(len(publications), 1)

    def test_missing_profile_is_rejected(self):
        with isolated_test_session() as db:
            user, _, artifact = prepare_candidate(
                db, create_profile=False
            )

            review_degree_and_publication(db, user, artifact)

            with self.assertRaises(ApprovalConflict):
                approve(db, user, artifact)

            self.assertEqual(artifact.status, "IN_REVIEW")

    def test_explicit_confirmation_is_required(self):
        with isolated_test_session() as db:
            user, profile, artifact = prepare_candidate(db)

            review_degree_and_publication(db, user, artifact)

            with self.assertRaises(ApprovalValidationError):
                approve(
                    db, user, artifact,
                    confirm=False,
                )

            self.assertEqual(artifact.status, "IN_REVIEW")

    def test_existing_duplicate_is_rejected(self):
        with isolated_test_session() as db:
            user, profile, artifact = prepare_candidate(db)

            existing = Publication(
                profile_id=profile.id,
                title="Machine Learning in Education",
                publication_year=2024,
            )
            db.add(existing)
            db.flush()

            review_degree_and_publication(db, user, artifact)

            with self.assertRaises(ApprovalConflict):
                approve(db, user, artifact)

            degrees = db.execute(
                select(Degree).where(
                    Degree.profile_id == profile.id
                )
            ).scalars().all()

            self.assertEqual(len(degrees), 0)
            self.assertEqual(artifact.status, "IN_REVIEW")

    def test_publication_duplicate_ignores_case_and_spaces(self):
        with isolated_test_session() as db:
            user, profile, artifact = prepare_candidate(db)

            existing = Publication(
                profile_id=profile.id,
                title=" machine learning in education ",
                publication_year=2024,
            )
            db.add(existing)
            db.flush()

            review_degree_and_publication(
                db, user, artifact
            )

            with self.assertRaises(ApprovalConflict):
                approve(db, user, artifact)

if __name__ == "__main__":
    unittest.main()