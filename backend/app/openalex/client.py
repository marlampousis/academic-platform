import httpx

from app.openalex.schemas import OpenAlexWorkPreview


OPENALEX_BASE_URL = "https://api.openalex.org"


def normalize_openalex_work(work: dict) -> OpenAlexWorkPreview:
    authorships = work.get("authorships") or []

    authors = []
    for authorship in authorships:
        author = authorship.get("author") or {}
        display_name = author.get("display_name")

        if display_name:
            authors.append(display_name)

    primary_location = work.get("primary_location") or {}
    source = primary_location.get("source") or {}

    return OpenAlexWorkPreview(
        openalex_id=work.get("id"),
        title=work.get("title") or work.get("display_name"),
        publication_year=work.get("publication_year"),
        doi=work.get("doi"),
        publication_type=work.get("type"),
        journal_name=source.get("display_name"),
        citation_count=work.get("cited_by_count") or 0,
        authors=authors
    )


async def search_works(query: str, per_page: int = 10):
    params = {
        "search": query,
        "per-page": per_page
    }

    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.get(
            f"{OPENALEX_BASE_URL}/works",
            params=params
        )

        response.raise_for_status()
        data = response.json()

    results = data.get("results", [])

    return [
        normalize_openalex_work(work)
        for work in results
    ]


async def get_work_by_doi(doi: str):
    normalized_doi = doi.strip()

    if not normalized_doi.startswith("https://doi.org/"):
        normalized_doi = f"https://doi.org/{normalized_doi}"

    params = {
        "filter": f"doi:{normalized_doi}",
        "per-page": 1
    }

    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.get(
            f"{OPENALEX_BASE_URL}/works",
            params=params
        )

        response.raise_for_status()
        data = response.json()

    results = data.get("results", [])

    if not results:
        return None

    return normalize_openalex_work(results[0])

async def get_work_by_openalex_id(openalex_id: str):
    normalized_id = openalex_id.strip()

    if normalized_id.startswith("https://openalex.org/"):
        work_id = normalized_id.split("/")[-1]
        api_url = f"{OPENALEX_BASE_URL}/works/{work_id}"
    elif normalized_id.startswith("W"):
        api_url = f"{OPENALEX_BASE_URL}/works/{normalized_id}"
    else:
        api_url = normalized_id

    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.get(api_url)

        response.raise_for_status()
        data = response.json()

    return normalize_openalex_work(data)