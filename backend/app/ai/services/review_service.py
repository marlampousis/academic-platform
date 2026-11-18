
from copy import deepcopy

from sqlalchemy.orm import Session

from app.ai.models import AIArtifact, AIReviewEvent
from app.ai.schemas.extraction import (
    ExtractedDegree,
    ExtractedPublication,
    ExtractedResearchProject,
    ExtractedTeachingExperience,
)
from app.ai.schemas.review import (
    ExtractionReviewRequest,
    ReviewDecision,
)


RECORD_MODELS = {
    "degrees": ExtractedDegree,
    "publications": ExtractedPublication,
    "research_projects": ExtractedResearchProject,
    "teaching_experience": ExtractedTeachingExperience,
}


class ReviewNotFound(Exception):
    """Artifact not found or not owned by the candidate."""


class ReviewConflict(Exception):
    """Artifact version or status prevents reviewing."""


class InvalidReview(ValueError):
    """The candidate's review contains invalid data."""


def apply_extraction_review(
    db: Session,
    *,
    artifact_id: int,
    candidate_user_id: int,
    request: ExtractionReviewRequest,
) -> AIArtifact:

    # Lock the artifact until the transaction finishes.
    artifact = (
        db.query(AIArtifact)
        .filter(
            AIArtifact.id == artifact_id,
            AIArtifact.owner_user_id == candidate_user_id,
            AIArtifact.artifact_type == "CV_EXTRACTION",
        )
        .with_for_update()
        .first()
    )

    if artifact is None:
        raise ReviewNotFound("Extraction not found")

    if artifact.status not in (
        "REVIEW_REQUIRED",
        "IN_REVIEW",
    ):
        raise ReviewConflict(
            "This extraction cannot be modified"
        )

    if artifact.version != request.expected_version:
        raise ReviewConflict(
            "The extraction has changed. Refresh before editing."
        )

    # Preserve the original AI extraction records.
    payload = deepcopy(artifact.payload_json)

    reviews = payload.get("_candidate_reviews", {})

    for decision in request.reviews:
        collection = decision.collection.value
        record_index = decision.record_index

        records = payload.get(collection, [])

        if record_index >= len(records):
            raise InvalidReview(
                f"Record index is invalid: {collection}[{record_index}]"
            )

        original_record = records[record_index]
        record_key = f"{collection}:{record_index}"

        previous_review = reviews.get(record_key)

        corrected_data = None

        if decision.decision == ReviewDecision.EDIT:
            model_class = RECORD_MODELS[collection]
            changes = decision.corrected_data

            allowed_fields = (
                set(model_class.model_fields) - {"evidence"}
            )

            unknown_fields = set(changes) - allowed_fields

            if unknown_fields:
                raise InvalidReview(
                    f"Unsupported editable fields: {unknown_fields}"
                )

            # Validate the complete proposed corrected record.
            corrected_record = {
                **original_record,
                **changes,
            }

            try:
                validated = model_class.model_validate(
                    corrected_record
                )
            except Exception as exc:
                raise InvalidReview(
                    "Corrected record failed validation"
                ) from exc

            # Store only candidate changes.
            # Original AI evidence remains unchanged.
            corrected_data = {
                field: validated.model_dump(mode="json")[field]
                for field in changes
            }

        new_review = {
            "decision": decision.decision.value,
            "corrected_data": corrected_data,
        }

        reviews[record_key] = new_review

        db.add(
            AIReviewEvent(
                artifact_id=artifact.id,
                reviewer_id=candidate_user_id,
                action=f"RECORD_{decision.decision.value}",
                comment=decision.comment,
                before_json=deepcopy(previous_review),
                after_json=deepcopy(new_review),
            )
        )

    payload["_candidate_reviews"] = reviews

    artifact.payload_json = payload
    artifact.status = "IN_REVIEW"
    artifact.version += 1

    db.flush()

    return artifact
