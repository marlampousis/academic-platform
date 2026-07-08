import httpx

from app.orcid.schemas import (
    OrcidProfilePreview,
    OrcidWorkPreview,
    OrcidEducationPreview,
)

ORCID_BASE_URL = "https://pub.orcid.org/v3.0"


def _headers():
    return {
        "Accept": "application/json"
    }


async def get_orcid_profile(orcid_id: str) -> OrcidProfilePreview:
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.get(
            f"{ORCID_BASE_URL}/{orcid_id}/record",
            headers=_headers()
        )

        response.raise_for_status()
        data = response.json()

    person = data.get("person", {})
    name = person.get("name", {}) or {}
    biography_obj = person.get("biography", {}) or {}

    given_names = (name.get("given-names") or {}).get("value")
    family_name = (name.get("family-name") or {}).get("value")
    credit_name = (name.get("credit-name") or {}).get("value")
    biography = biography_obj.get("content")

    return OrcidProfilePreview(
        orcid_id=orcid_id,
        given_names=given_names,
        family_name=family_name,
        credit_name=credit_name,
        biography=biography
    )


def _extract_external_id(work_summary: dict, external_id_type: str):
    external_ids = work_summary.get("external-ids") or {}
    external_id_list = external_ids.get("external-id") or []

    for external_id in external_id_list:
        if external_id.get("external-id-type") == external_id_type:
            return external_id.get("external-id-value")

    return None


def _extract_year(work_summary: dict):
    publication_date = work_summary.get("publication-date") or {}
    year = publication_date.get("year") or {}

    value = year.get("value")

    if value:
        try:
            return int(value)
        except ValueError:
            return None

    return None


async def get_orcid_works(orcid_id: str) -> list[OrcidWorkPreview]:
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.get(
            f"{ORCID_BASE_URL}/{orcid_id}/works",
            headers=_headers()
        )

        response.raise_for_status()
        data = response.json()

    groups = data.get("group") or []
    works: list[OrcidWorkPreview] = []

    for group in groups:
        summaries = group.get("work-summary") or []

        for summary in summaries:
            title_obj = summary.get("title") or {}
            title = (title_obj.get("title") or {}).get("value")

            journal_title_obj = summary.get("journal-title") or {}
            journal_title = journal_title_obj.get("value")

            doi = _extract_external_id(summary, "doi")

            works.append(
                OrcidWorkPreview(
                    title=title,
                    publication_year=_extract_year(summary),
                    doi=doi,
                    work_type=summary.get("type"),
                    journal_title=journal_title,
                    orcid_work_id=str(summary.get("put-code"))
                    if summary.get("put-code") is not None
                    else None
                )
            )

    return works

def _extract_year_from_date(date_obj: dict | None):
    if not date_obj:
        return None

    year = date_obj.get("year") or {}
    value = year.get("value")

    if value:
        try:
            return int(value)
        except ValueError:
            return None

    return None


async def get_orcid_education(orcid_id: str) -> list[OrcidEducationPreview]:
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.get(
            f"{ORCID_BASE_URL}/{orcid_id}/educations",
            headers=_headers()
        )

        response.raise_for_status()
        data = response.json()

    summaries = data.get("affiliation-group") or []
    education_entries: list[OrcidEducationPreview] = []

    for group in summaries:
        education_summaries = group.get("summaries") or []

        for item in education_summaries:
            summary = item.get("education-summary") or {}

            organization = summary.get("organization") or {}
            department_name = summary.get("department-name")
            role_title = summary.get("role-title")

            education_entries.append(
                OrcidEducationPreview(
                    organization_name=organization.get("name"),
                    department_name=department_name,
                    role_title=role_title,
                    start_year=_extract_year_from_date(summary.get("start-date")),
                    end_year=_extract_year_from_date(summary.get("end-date")),
                    orcid_education_id=str(summary.get("put-code"))
                    if summary.get("put-code") is not None
                    else None
                )
            )

    return education_entries