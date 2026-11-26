
from sqlalchemy.orm import Session

from app.ai.services.candidate_context_service import (
    CandidateProfileAccessDenied,
    CandidateProfileNotFound,
    get_candidate_academic_context,
)
from app.ai.services.matching_retrieval_service import (
    MatchingArtifactInvalid,
    get_saved_matching_report,
)


COLLECTIONS = (
    "degrees",
    "publications",
    "research_projects",
    "teaching_experience",
)

TITLE_FIELDS = {
    "degrees": "title",
    "publications": "title",
    "research_projects": "title",
    "teaching_experience": "course_title",
}


def get_matching_evidence_details(
    db: Session,
    *,
    artifact_id: int,
    owner_user_id: int,
) -> dict:
    """
    Retrieve the current academic records cited by a saved
    AI matching report.

    Security:
    - Verify ownership of the saved matching artifact.
    - Verify ownership of the candidate academic profile.
    - Return only records cited in the matching report.

    Important:
    The saved AI matching report is historical.
    The evidence details reflect the current database state.
    """

    # Step 1: Validate identifiers.
    if artifact_id <= 0 or owner_user_id <= 0:
        raise ValueError(
            "Artifact ID and owner user ID must be positive"
        )

    # Step 2: Retrieve the saved matching report.
    # This service validates artifact and AI-run ownership.
    report = get_saved_matching_report(
        db,
        artifact_id=artifact_id,
        owner_user_id=owner_user_id,
    )

    draft = report.matching_draft

    # Step 3: Retrieve the candidate's academic records.
    # Profile ownership is checked by the existing service.
    try:
        context = get_candidate_academic_context(
            db,
            profile_id=draft.profile_id,
            expected_user_id=owner_user_id,
        )

    except (
        CandidateProfileAccessDenied,
        CandidateProfileNotFound,
    ) as exc:
        raise MatchingArtifactInvalid(
            "Matching profile is unavailable or inaccessible"
        ) from exc

    # Step 4: Verify candidate identity consistency.
    if (
        context.user_id != owner_user_id
        or context.profile_id != draft.profile_id
    ):
        raise MatchingArtifactInvalid(
            "Candidate context identity mismatch"
        )

    # Step 5: Index the candidate's current academic records.
    # Keys are (collection_name, record_id).
    evidence_index = {}

    for collection in COLLECTIONS:
        records = getattr(context, collection)

        for record in records:
            evidence_index[
                (collection, record.id)
            ] = record

    # Step 6: Resolve evidence references.
    resolved_matches = []

    for match in draft.matches:
        resolved_evidence = []

        for reference in match.evidence:
            collection = reference.collection

            # Support both string and Enum values.
            if hasattr(collection, "value"):
                collection = collection.value

            record_id = reference.record_id

            if collection not in COLLECTIONS:
                raise MatchingArtifactInvalid(
                    "Unknown evidence collection"
                )

            record = evidence_index.get(
                (collection, record_id)
            )

            # The record may have been deleted or changed
            # after the original AI matching report.
            if record is None:
                resolved_evidence.append({
                    "collection": collection,
                    "record_id": record_id,
                    "available": False,
                    "title": None,
                    "details": None,
                })

                continue

            # Convert validated Pydantic records into
            # JSON-compatible dictionaries.
            details = record.model_dump(mode="json")

            title = details.get(
                TITLE_FIELDS[collection]
            )

            resolved_evidence.append({
                "collection": collection,
                "record_id": record_id,
                "available": True,
                "title": title,
                "details": details,
            })

        resolved_matches.append({
            "requirement_id": match.requirement_id,
            "evidence": resolved_evidence,
        })

    # Step 7: Return only evidence cited by the report.
    return {
        "artifact_id": report.artifact_id,
        "application_id": draft.application_id,
        "profile_id": draft.profile_id,
        "evidence_source": "CURRENT_DATABASE_RECORDS",
        "matches": resolved_matches,
    }
