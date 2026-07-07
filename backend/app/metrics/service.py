from sqlalchemy.orm import Session

from app.publications.models import Publication


def calculate_h_index(citation_counts: list[int]) -> int:
    sorted_citations = sorted(citation_counts, reverse=True)

    h_index = 0

    for index, citations in enumerate(sorted_citations, start=1):
        if citations >= index:
            h_index = index
        else:
            break

    return h_index


def get_profile_metrics(db: Session, profile_id: int):
    publications = (
        db.query(Publication)
        .filter(Publication.profile_id == profile_id)
        .all()
    )

    total_publications = len(publications)

    citation_counts = [
        publication.citation_count or 0
        for publication in publications
    ]

    total_citations = sum(citation_counts)

    average_citations = (
        total_citations / total_publications
        if total_publications > 0
        else 0
    )

    h_index = calculate_h_index(citation_counts)

    return {
        "profile_id": profile_id,
        "total_publications": total_publications,
        "total_citations": total_citations,
        "average_citations": round(average_citations, 2),
        "h_index": h_index
    }