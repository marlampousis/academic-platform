from copy import deepcopy
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.ai.models import AIArtifact, AIReviewEvent
from app.ai.schemas.approval import ExtractionApprovalRequest
from app.ai.services.review_service import RECORD_MODELS
from app.profiles.models import AcademicProfile
from app.degrees.models import Degree
from app.publications.models import Publication
from app.research_projects.models import ResearchProject
from app.teaching_experience.models import TeachingExperience


COLLECTION_MODELS = {
    "degrees": Degree,
    "publications": Publication,
    "research_projects": ResearchProject,
    "teaching_experience": TeachingExperience,
}


class ApprovalNotFound(Exception):
    """The artifact does not exist or belongs to another candidate."""


class ApprovalConflict(Exception):
    """Approval cannot proceed due to state, version or duplicates."""


class ApprovalValidationError(ValueError):
    """The extraction is incomplete or contains invalid review data."""


def approve_extraction(
    db: Session,
    *,
    artifact_id: int,
    candidate_user_id: int,
    request: ExtractionApprovalRequest,
) -> tuple[AIArtifact, dict[str, int]]:
    if request.confirm is not True:
        raise ApprovalValidationError(
            "Explicit approval confirmation is required"
        )

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
        raise ApprovalNotFound("Extraction not found")

    if artifact.status not in ("REVIEW_REQUIRED", "IN_REVIEW"):
        raise ApprovalConflict(
            "This extraction cannot be approved again"
        )

    if artifact.version != request.expected_version:
        raise ApprovalConflict(
            "The extraction has changed. Reload before approving."
        )

    # Lock the candidate's academic profile as well.
    profile = (
        db.query(AcademicProfile)
        .filter(AcademicProfile.user_id == candidate_user_id)
        .with_for_update()
        .first()
    )

    if profile is None:
        raise ApprovalConflict(
            "Create an academic profile before final approval"
        )

    payload = deepcopy(artifact.payload_json)
    reviews = payload.get("_candidate_reviews", {})

    counts = {
        collection: 0
        for collection in COLLECTION_MODELS
    }

    pending_records = []

    for collection, model_class in COLLECTION_MODELS.items():
        records = payload.get(collection, [])

        for index, original in enumerate(records):
            review_key = f"{collection}:{index}"
            review = reviews.get(review_key)

            if not review:
                raise ApprovalValidationError(
                    f"Missing review decision: {review_key}"
                )

            decision = review.get("decision")

            if decision not in ("ACCEPT", "EDIT", "REJECT"):
                raise ApprovalValidationError(
                    f"Invalid review decision: {review_key}"
                )

            if decision == "REJECT":
                continue

            # Original AI data and candidate corrections remain separate.
            effective_record = deepcopy(original)

            if decision == "EDIT":
                changes = review.get("corrected_data")

                if not isinstance(changes, dict) or not changes:
                    raise ApprovalValidationError(
                        f"Missing corrections for {review_key}"
                    )

                allowed_fields = (
                    set(RECORD_MODELS[collection].model_fields)
                    - {"evidence"}
                )

                if set(changes) - allowed_fields:
                    raise ApprovalValidationError(
                        f"Unsupported corrections for {review_key}"
                    )

                effective_record.update(changes)

            try:
                validated = RECORD_MODELS[
                    collection
                ].model_validate(effective_record)
            except Exception as exc:
                raise ApprovalValidationError(
                    f"Invalid credential: {review_key}"
                ) from exc

            data = validated.model_dump(
                mode="python",
                exclude={"evidence"},
            )

            # Never accept profile IDs from AI output or review changes.
            data.pop("profile_id", None)

            # Only mapped official model columns may be inserted.
            column_names = {
                column.name
                for column in model_class.__table__.columns
            } - {"id", "profile_id"}

            data = {
                key: value
                for key, value in data.items()
                if key in column_names
            }

            pending_records.append(
                (collection, model_class, data)
            )

    # Reject obvious duplicate records, including repeated suggestions
    # in the same extraction. More sophisticated identity matching
    # (DOI normalization, identifiers) can follow later.
    seen = set()

    for collection, model_class, data in pending_records:
        if collection == "degrees":
            identity = (
                data.get("degree_type"),
                data.get("title"),
                data.get("institution_name"),
                data.get("end_year"),
            )
        elif collection == "publications":
            identity = (
                data.get("doi").strip().lower()
                if data.get("doi")
                else (
                    str(data.get("title", "")).strip().lower(),
                    data.get("publication_year"),
                )
            )
        elif collection == "research_projects":
            identity = (
                data.get("title"),
                data.get("project_identifier"),
            )
        else:
            identity = (
                data.get("course_title"),
                data.get("institution_name"),
                data.get("academic_year"),
            )

        duplicate_key = (collection, identity)

        if duplicate_key in seen:
            raise ApprovalConflict(
                f"Duplicate record in extraction: {collection}"
            )

        seen.add(duplicate_key)

        # Check existing official records using their identity fields.
        existing_query = db.query(model_class).filter(
            model_class.profile_id == profile.id
        )

        if collection == "degrees":
            existing_query = existing_query.filter_by(
                degree_type=data.get("degree_type"),
                title=data.get("title"),
                institution_name=data.get("institution_name"),
                end_year=data.get("end_year"),
            )

        elif collection == "publications":
            if data.get("doi"):
                existing_query = existing_query.filter(
                    model_class.doi.ilike(data["doi"].strip())
                )
            else:
                normalized_title = (
                    data.get("title") or ""
                ).strip().casefold()

                existing_query = existing_query.filter(
                    func.lower(
                        func.trim(model_class.title)
                    ) == normalized_title,
                    model_class.publication_year
                    == data.get("publication_year"),
                )

        elif collection == "research_projects":
            existing_query = existing_query.filter_by(
                title=data.get("title"),
                project_identifier=data.get("project_identifier"),
            )

        else:
            existing_query = existing_query.filter_by(
                course_title=data.get("course_title"),
                institution_name=data.get("institution_name"),
                academic_year=data.get("academic_year"),
            )

        if existing_query.first() is not None:
            raise ApprovalConflict(
                f"Potential duplicate academic record: {collection}"
            )

    # All checks have passed. Stage official records.
    for collection, model_class, data in pending_records:
        db.add(
            model_class(
                profile_id=profile.id,
                **data,
            )
        )
        counts[collection] += 1

    # Approval and official records belong to one transaction.
    artifact.status = "APPROVED"
    artifact.version += 1

    db.add(
        AIReviewEvent(
            artifact_id=artifact.id,
            reviewer_id=candidate_user_id,
            action="FINAL_APPROVAL",
            comment="Candidate approved reviewed AI extraction",
            before_json={
                "status": "IN_REVIEW"
                if reviews
                else "REVIEW_REQUIRED",
            },
            after_json={
                "status": "APPROVED",
                "created_records": counts,
            },
        )
    )

    db.flush()

    return artifact, counts
