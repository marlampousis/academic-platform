
import unittest
from uuid import uuid4

import app.core.model_registry

from sqlalchemy import select

from app.users.models import User
from app.roles.models import Role
from app.ai.models import AIReviewEvent
from app.ai.schemas.extraction import (
    AcademicCVExtraction,
    ExtractedDegree,
    ExtractedPublication,
    EvidenceReference,
)
from app.ai.schemas.review import ExtractionReviewRequest
from app.ai.services.persistence_service import (
    create_ai_run,
    save_extraction_artifact,
)
from app.ai.services.review_service import (
    apply_extraction_review,
    ReviewNotFound,
    ReviewConflict,
    InvalidReview,
)

from db_setup import isolated_test_session


SOURCE_ID = "s03-test-cv"

CV_TEXT = (
    "Alex Morgan received a PhD in Computer Science "
    "from Example University in 2022. "
    "Published Machine Learning in Education in 2021."
)


def create_test_user(db):
    role_id = db.execute(
        select(Role.id).where(Role.code == "CANDIDATE")
    ).scalar_one()

    user = User(
        first_name="S03",
        last_name="Candidate",
        email=f"s03-{uuid4().hex}@example.test",
        hashed_password="test-only",
        role_id=role_id,
    )

    db.add(user)
    db.flush()
    return user


def create_test_artifact(db, user_id):
    extraction = AcademicCVExtraction(
        specialization="Artificial Intelligence",
        degrees=[
            ExtractedDegree(
                degree_type="PhD",
                title="PhD in Computer Science",
                institution_name="Example University",
                end_year=2022,
                evidence=[
                    EvidenceReference(
                        source_id=SOURCE_ID,
                        excerpt="PhD in Computer Science",
                    )
                ],
            )
        ],
        publications=[
            ExtractedPublication(
                title="Machine Learning in Education",
                publication_year=2021,
                evidence=[
                    EvidenceReference(
                        source_id=SOURCE_ID,
                        excerpt="Machine Learning in Education",
                    )
                ],
            )
        ],
    )

    run = create_ai_run(
        db,
        user_id=user_id,
        task_type="CV_EXTRACTION",
        provider="gemini",
        model_name="test-model",
    )

    run.status = "SUCCEEDED"

    artifact = save_extraction_artifact(
        db,
        run=run,
        owner_user_id=user_id,
        extraction=extraction,
        source_id=SOURCE_ID,
        cv_text=CV_TEXT,
    )

    return artifact


def make_request(
    collection,
    record_index,
    decision,
    corrected_data=None,
    expected_version=1,
):
    review = {
        "collection": collection,
        "record_index": record_index,
        "decision": decision,
    }

    if corrected_data is not None:
        review["corrected_data"] = corrected_data

    return ExtractionReviewRequest(
        expected_version=expected_version,
        reviews=[review],
    )


class TestAIReview(unittest.TestCase):

    def test_candidate_accepts_degree(self):
        with isolated_test_session() as db:
            user = create_test_user(db)
            artifact = create_test_artifact(db, user.id)

            result = apply_extraction_review(
                db,
                artifact_id=artifact.id,
                candidate_user_id=user.id,
                request=make_request(
                    "degrees", 0, "ACCEPT"
                ),
            )

            self.assertEqual(result.status, "IN_REVIEW")
            self.assertEqual(result.version, 2)

            review = result.payload_json[
                "_candidate_reviews"
            ]["degrees:0"]

            self.assertEqual(review["decision"], "ACCEPT")

            events = db.execute(
                select(AIReviewEvent).where(
                    AIReviewEvent.artifact_id == result.id
                )
            ).scalars().all()

            self.assertEqual(len(events), 1)
            self.assertEqual(
                events[0].action,
                "RECORD_ACCEPT",
            )
            self.assertEqual(events[0].reviewer_id, user.id)

    def test_candidate_edits_publication(self):
        with isolated_test_session() as db:
            user = create_test_user(db)
            artifact = create_test_artifact(db, user.id)

            result = apply_extraction_review(
                db,
                artifact_id=artifact.id,
                candidate_user_id=user.id,
                request=make_request(
                    "publications",
                    0,
                    "EDIT",
                    corrected_data={
                        "publication_year": 2023
                    },
                ),
            )

            review = result.payload_json[
                "_candidate_reviews"
            ]["publications:0"]

            self.assertEqual(review["decision"], "EDIT")
            self.assertEqual(
                review["corrected_data"]["publication_year"],
                2023,
            )

            # Original AI extraction remains unchanged.
            self.assertEqual(
                result.payload_json["publications"][0][
                    "publication_year"
                ],
                2021,
            )

    def test_other_candidate_cannot_review(self):
        with isolated_test_session() as db:
            owner = create_test_user(db)
            other = create_test_user(db)

            artifact = create_test_artifact(db, owner.id)

            with self.assertRaises(ReviewNotFound):
                apply_extraction_review(
                    db,
                    artifact_id=artifact.id,
                    candidate_user_id=other.id,
                    request=make_request(
                        "degrees", 0, "ACCEPT"
                    ),
                )

    def test_outdated_version_rejected(self):
        with isolated_test_session() as db:
            user = create_test_user(db)
            artifact = create_test_artifact(db, user.id)

            with self.assertRaises(ReviewConflict):
                apply_extraction_review(
                    db,
                    artifact_id=artifact.id,
                    candidate_user_id=user.id,
                    request=make_request(
                        "degrees",
                        0,
                        "ACCEPT",
                        expected_version=99,
                    ),
                )

    def test_invalid_record_index_rejected(self):
        with isolated_test_session() as db:
            user = create_test_user(db)
            artifact = create_test_artifact(db, user.id)

            with self.assertRaises(InvalidReview):
                apply_extraction_review(
                    db,
                    artifact_id=artifact.id,
                    candidate_user_id=user.id,
                    request=make_request(
                        "degrees", 99, "ACCEPT"
                    ),
                )

    def test_original_evidence_cannot_be_edited(self):
        with isolated_test_session() as db:
            user = create_test_user(db)
            artifact = create_test_artifact(db, user.id)

            with self.assertRaises(InvalidReview):
                apply_extraction_review(
                    db,
                    artifact_id=artifact.id,
                    candidate_user_id=user.id,
                    request=make_request(
                        "degrees",
                        0,
                        "EDIT",
                        corrected_data={
                            "evidence": []
                        },
                    ),
                )

    def test_approved_artifact_cannot_be_reviewed(self):
        with isolated_test_session() as db:
            user = create_test_user(db)
            artifact = create_test_artifact(db, user.id)

            artifact.status = "APPROVED"
            db.flush()

            with self.assertRaises(ReviewConflict):
                apply_extraction_review(
                    db,
                    artifact_id=artifact.id,
                    candidate_user_id=user.id,
                    request=make_request(
                        "degrees", 0, "ACCEPT"
                    ),
                )

    def test_unchanged_review_does_not_create_new_event(self):
        with isolated_test_session() as db:
            user = create_test_user(db)
            artifact = create_test_artifact(db, user.id)

            first = apply_extraction_review(
                db,
                artifact_id=artifact.id,
                candidate_user_id=user.id,
                request=make_request(
                    "degrees",
                    0,
                    "ACCEPT",
                    expected_version=1,
                ),
            )

            self.assertEqual(first.version, 2)

            second = apply_extraction_review(
                db,
                artifact_id=artifact.id,
                candidate_user_id=user.id,
                request=make_request(
                    "degrees",
                    0,
                    "ACCEPT",
                    expected_version=2,
                ),
            )

            self.assertEqual(second.version, 2)

            events = db.execute(
                select(AIReviewEvent).where(
                    AIReviewEvent.artifact_id == artifact.id
                )
            ).scalars().all()

            self.assertEqual(len(events), 1)
            self.assertEqual(events[0].action, "RECORD_ACCEPT")

if __name__ == "__main__":
    unittest.main()
