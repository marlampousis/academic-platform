
import unittest
from unittest.mock import patch

import app.core.model_registry

from sqlalchemy import select

from app.ai.models import AIArtifact, AIReviewEvent

from test_ai_extraction_api import (
    CV_TEXT,
    FakeExtractionService,
    create_candidate,
    auth_headers,
)
from db_setup import isolated_api_client


class TestAIReviewAPI(unittest.TestCase):

    def create_draft(self, client, user):
        with patch(
            "app.ai.router.create_gemini_extraction_service",
            return_value=FakeExtractionService(),
        ):
            response = client.post(
                "/ai/extractions",
                headers=auth_headers(user),
                json={"cv_text": CV_TEXT},
            )

        self.assertEqual(
            response.status_code, 201, response.text
        )
        return response.json()["artifact_id"]

    def test_candidate_accepts_degree(self):
        with isolated_api_client() as (client, db):
            user = create_candidate(db)
            artifact_id = self.create_draft(client, user)

            response = client.patch(
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
                response.status_code, 200, response.text
            )
            self.assertEqual(
                response.json()["status"], "IN_REVIEW"
            )
            self.assertEqual(response.json()["version"], 2)
            self.assertEqual(
                response.json()["reviews"]["degrees:0"]["decision"],
                "ACCEPT",
            )

            events = db.execute(
                select(AIReviewEvent).where(
                    AIReviewEvent.artifact_id == artifact_id
                )
            ).scalars().all()

            self.assertEqual(len(events), 1)
            self.assertEqual(events[0].action, "RECORD_ACCEPT")

    def test_other_candidate_cannot_review(self):
        with isolated_api_client() as (client, db):
            owner = create_candidate(db)
            other = create_candidate(db)
            artifact_id = self.create_draft(client, owner)

            response = client.patch(
                f"/ai/extractions/{artifact_id}/review",
                headers=auth_headers(other),
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

            self.assertEqual(response.status_code, 404)

    def test_outdated_version_returns_409(self):
        with isolated_api_client() as (client, db):
            user = create_candidate(db)
            artifact_id = self.create_draft(client, user)

            response = client.patch(
                f"/ai/extractions/{artifact_id}/review",
                headers=auth_headers(user),
                json={
                    "expected_version": 99,
                    "reviews": [
                        {
                            "collection": "degrees",
                            "record_index": 0,
                            "decision": "ACCEPT",
                        }
                    ],
                },
            )

            self.assertEqual(response.status_code, 409)

    def test_invalid_record_returns_422(self):
        with isolated_api_client() as (client, db):
            user = create_candidate(db)
            artifact_id = self.create_draft(client, user)

            response = client.patch(
                f"/ai/extractions/{artifact_id}/review",
                headers=auth_headers(user),
                json={
                    "expected_version": 1,
                    "reviews": [
                        {
                            "collection": "degrees",
                            "record_index": 99,
                            "decision": "ACCEPT",
                        }
                    ],
                },
            )

            self.assertEqual(response.status_code, 422)

            artifact = db.get(AIArtifact, artifact_id)
            self.assertEqual(artifact.version, 1)
            self.assertEqual(
                artifact.status, "REVIEW_REQUIRED"
            )


    def test_candidate_can_change_review_decision(self):
        with isolated_api_client() as (client, db):
            user = create_candidate(db)
            artifact_id = self.create_draft(client, user)

            url = f"/ai/extractions/{artifact_id}/review"

            first = client.patch(
                url,
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

            self.assertEqual(first.status_code, 200, first.text)
            self.assertEqual(first.json()["version"], 2)

            second = client.patch(
                url,
                headers=auth_headers(user),
                json={
                    "expected_version": 2,
                    "reviews": [
                        {
                            "collection": "degrees",
                            "record_index": 0,
                            "decision": "REJECT",
                        }
                    ],
                },
            )

            self.assertEqual(second.status_code, 200, second.text)
            self.assertEqual(second.json()["version"], 3)
            self.assertEqual(
                second.json()["reviews"]["degrees:0"]["decision"],
                "REJECT",
            )

            events = db.execute(
                select(AIReviewEvent)
                .where(AIReviewEvent.artifact_id == artifact_id)
                .order_by(AIReviewEvent.id)
            ).scalars().all()

            self.assertEqual(len(events), 2)
            self.assertEqual(
                [event.action for event in events],
                ["RECORD_ACCEPT", "RECORD_REJECT"],
            )

            self.assertEqual(
                events[1].before_json["decision"],
                "ACCEPT",
            )

    def test_invalid_batch_rolls_back_all_decisions(self):
        with isolated_api_client() as (client, db):
            user = create_candidate(db)
            artifact_id = self.create_draft(client, user)

            response = client.patch(
                f"/ai/extractions/{artifact_id}/review",
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
                            "collection": "degrees",
                            "record_index": 999,
                            "decision": "REJECT",
                        },
                    ],
                },
            )

            self.assertEqual(response.status_code, 422, response.text)

            db.expire_all()
            artifact = db.get(AIArtifact, artifact_id)

            self.assertEqual(artifact.version, 1)
            self.assertEqual(artifact.status, "REVIEW_REQUIRED")
            self.assertNotIn(
                "_candidate_reviews",
                artifact.payload_json,
            )

            events = db.execute(
                select(AIReviewEvent).where(
                    AIReviewEvent.artifact_id == artifact_id
                )
            ).scalars().all()

            self.assertEqual(len(events), 0)


if __name__ == "__main__":
    unittest.main()
