
import unittest
from unittest.mock import patch

import app.core.model_registry

from sqlalchemy import select

from app.ai.models import AIArtifact, AIReviewEvent
from app.ai.services.approval_service import approve_extraction
from app.profiles.models import AcademicProfile
from app.degrees.models import Degree
from app.publications.models import Publication

from db_setup import isolated_api_client
from test_ai_extraction_api import (
    create_candidate,
    auth_headers,
)
from test_ai_review import create_test_artifact


class TestAIApprovalAPI(unittest.TestCase):

    def prepare(self, db, create_profile=True):
        user = create_candidate(db)

        profile = None
        if create_profile:
            profile = AcademicProfile(user_id=user.id)
            db.add(profile)
            db.flush()

        artifact = create_test_artifact(db, user.id)
        return user, profile, artifact

    def review_all(self, client, user, artifact):
        response = client.patch(
            f"/ai/extractions/{artifact.id}/review",
            headers=auth_headers(user),
            json={
                "expected_version": 1,
                "reviews": [
                    {
                        "collection": "degrees",
                        "record_index": 0,
                        "decision": "ACCEPT",
                    },
                    {
                        "collection": "publications",
                        "record_index": 0,
                        "decision": "EDIT",
                        "corrected_data": {
                            "publication_year": 2024
                        },
                    },
                ],
            },
        )

        self.assertEqual(
            response.status_code, 200, response.text
        )
        self.assertEqual(response.json()["version"], 2)

    def approve(self, client, user, artifact, version=2):
        return client.post(
            f"/ai/extractions/{artifact.id}/approve",
            headers=auth_headers(user),
            json={
                "expected_version": version,
                "confirm": True,
            },
        )

    def test_successful_approval_creates_official_records(self):
        with isolated_api_client() as (client, db):
            user, profile, artifact = self.prepare(db)
            self.review_all(client, user, artifact)

            response = self.approve(client, user, artifact)

            self.assertEqual(
                response.status_code, 200, response.text
            )
            self.assertEqual(response.json()["status"], "APPROVED")
            self.assertEqual(response.json()["version"], 3)

            counts = response.json()["created_records"]
            self.assertEqual(counts["degrees"], 1)
            self.assertEqual(counts["publications"], 1)

            db.expire_all()

            publication = db.execute(
                select(Publication).where(
                    Publication.profile_id == profile.id
                )
            ).scalar_one()

            self.assertEqual(
                publication.publication_year, 2024
            )

            saved_artifact = db.get(AIArtifact, artifact.id)
            self.assertEqual(saved_artifact.status, "APPROVED")
            self.assertEqual(
                saved_artifact.payload_json["publications"][0][
                    "publication_year"
                ],
                2021,
            )

            events = db.execute(
                select(AIReviewEvent).where(
                    AIReviewEvent.artifact_id == artifact.id,
                    AIReviewEvent.action == "FINAL_APPROVAL",
                )
            ).scalars().all()

            self.assertEqual(len(events), 1)
            self.assertEqual(events[0].reviewer_id, user.id)

    def test_incomplete_review_returns_422(self):
        with isolated_api_client() as (client, db):
            user, profile, artifact = self.prepare(db)
            artifact_id = artifact.id

            # Review only the degree.
            # The publication remains NOT_REVIEWED.
            review_response = client.patch(
                f"/ai/extractions/{artifact_id}/review",
                headers=auth_headers(user),
                json={
                    "expected_version": 1,
                    "reviews": [
                        {
                            "collection": "degrees",
                            "record_index": 0,
                            "decision": "ACCEPT",
                        }
                    ],
                },
            )

            self.assertEqual(
                review_response.status_code,
                200,
                review_response.text,
            )
            self.assertEqual(
                review_response.json()["version"],
                2,
            )

            # Final approval must reject incomplete reviews.
            response = client.post(
                f"/ai/extractions/{artifact_id}/approve",
                headers=auth_headers(user),
                json={
                    "expected_version": 2,
                    "confirm": True,
                },
            )

            self.assertEqual(
                response.status_code,
                422,
                response.text,
            )

            # The rejected approval must not change
            # the previously saved review.
            db.expire_all()

            saved_artifact = db.get(
                AIArtifact,
                artifact_id,
            )

            self.assertIsNotNone(saved_artifact)
            self.assertEqual(
                saved_artifact.status,
                "IN_REVIEW",
            )
            self.assertEqual(
                saved_artifact.version,
                2,
            )

            # No official credentials should be created.
            degrees = db.execute(
                select(Degree).where(
                    Degree.profile_id == profile.id
                )
            ).scalars().all()

            publications = db.execute(
                select(Publication).where(
                    Publication.profile_id == profile.id
                )
            ).scalars().all()

            self.assertEqual(len(degrees), 0)
            self.assertEqual(len(publications), 0)

    def test_other_candidate_cannot_approve(self):
        with isolated_api_client() as (client, db):
            owner, profile, artifact = self.prepare(db)
            other = create_candidate(db)

            self.review_all(client, owner, artifact)

            response = self.approve(
                client, other, artifact
            )

            self.assertEqual(response.status_code, 404)

    def test_stale_version_returns_409(self):
        with isolated_api_client() as (client, db):
            user, profile, artifact = self.prepare(db)
            self.review_all(client, user, artifact)

            response = self.approve(
                client, user, artifact, version=1
            )

            self.assertEqual(response.status_code, 409)

    def test_confirmation_false_returns_422(self):
        with isolated_api_client() as (client, db):
            user, profile, artifact = self.prepare(db)
            self.review_all(client, user, artifact)

            response = client.post(
                f"/ai/extractions/{artifact.id}/approve",
                headers=auth_headers(user),
                json={
                    "expected_version": 2,
                    "confirm": False,
                },
            )

            self.assertEqual(response.status_code, 422)

    def test_second_approval_returns_409(self):
        with isolated_api_client() as (client, db):
            user, profile, artifact = self.prepare(db)
            self.review_all(client, user, artifact)

            first = self.approve(client, user, artifact)
            self.assertEqual(
                first.status_code, 200, first.text
            )

            second = self.approve(
                client, user, artifact, version=3
            )
            self.assertEqual(second.status_code, 409)

            db.expire_all()
            publications = db.execute(
                select(Publication).where(
                    Publication.profile_id == profile.id
                )
            ).scalars().all()

            self.assertEqual(len(publications), 1)

    def test_unauthenticated_approval_returns_401(self):
        with isolated_api_client() as (client, db):
            user, profile, artifact = self.prepare(db)

            response = client.post(
                f"/ai/extractions/{artifact.id}/approve",
                json={
                    "expected_version": 1,
                    "confirm": True,
                },
            )

            self.assertEqual(response.status_code, 401)

    def test_approval_failure_rolls_back_everything(self):
        with isolated_api_client() as (client, db):
            user, profile, artifact = self.prepare(db)
            self.review_all(client, user, artifact)

            def fail_after_staging(*args, **kwargs):
                approve_extraction(*args, **kwargs)
                raise RuntimeError("Simulated approval failure")

            with patch(
                "app.ai.router.approve_extraction",
                side_effect=fail_after_staging,
            ):
                response = self.approve(
                    client, user, artifact
                )

            self.assertEqual(response.status_code, 500)

            db.expire_all()

            saved_artifact = db.get(AIArtifact, artifact.id)
            self.assertEqual(saved_artifact.status, "IN_REVIEW")
            self.assertEqual(saved_artifact.version, 2)

            degrees = db.execute(
                select(Degree).where(
                    Degree.profile_id == profile.id
                )
            ).scalars().all()

            publications = db.execute(
                select(Publication).where(
                    Publication.profile_id == profile.id
                )
            ).scalars().all()

            self.assertEqual(len(degrees), 0)
            self.assertEqual(len(publications), 0)

            approvals = db.execute(
                select(AIReviewEvent).where(
                    AIReviewEvent.artifact_id == artifact.id,
                    AIReviewEvent.action == "FINAL_APPROVAL",
                )
            ).scalars().all()

            self.assertEqual(len(approvals), 0)


if __name__ == "__main__":
    unittest.main()
