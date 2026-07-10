import re

from sqlalchemy.orm import Session

from app.profiles.models import AcademicProfile

from app.degrees.schemas import DegreeCreate
from app.degrees.service import (
    create_degree,
    get_duplicate_degree,
)

from app.publications.schemas import PublicationCreate
from app.publications.service import (
    create_publication,
    get_publication_by_doi,
)

from app.research_projects.schemas import ResearchProjectCreate
from app.research_projects.service import (
    create_research_project,
    get_research_project_by_title,
)

from app.teaching_experience.schemas import TeachingExperienceCreate
from app.teaching_experience.service import (
    create_teaching_experience,
    get_duplicate_teaching_experience,
)

ORCID_PATTERN = r"\b\d{4}-\d{4}-\d{4}-\d{3}[\dX]\b"

DOI_PATTERN = r"\b10\.\d{4,9}/[-._;()/:A-Z0-9]+\b"


def extract_orcid_ids(text: str) -> list[str]:
    return list(set(re.findall(ORCID_PATTERN, text)))


def extract_dois(text: str) -> list[str]:
    matches = re.findall(DOI_PATTERN, text, flags=re.IGNORECASE)
    return list(set(match.rstrip(".,;") for match in matches))


def extract_section(text: str, section_keywords: list[str]) -> str | None:
    lines = text.splitlines()

    start_index = None

    for index, line in enumerate(lines):
        clean_line = line.strip().lower()

        for keyword in section_keywords:
            if keyword.lower() in clean_line:
                start_index = index
                break

        if start_index is not None:
            break

    if start_index is None:
        return None

    collected_lines = []

    for line in lines[start_index + 1:]:
        clean_line = line.strip()

        if not clean_line:
            continue

        lower_line = clean_line.lower()

        possible_new_section = [
            "education",
            "degrees",
            "publications",
            "research projects",
            "projects",
            "teaching",
            "teaching experience",
            "work experience",
            "professional experience",
            "skills",
            "languages"
        ]

        if any(section == lower_line for section in possible_new_section):
            break

        collected_lines.append(clean_line)

    return "\n".join(collected_lines) if collected_lines else None


def parse_cv_text(text: str):
    return {
        "orcid_ids": extract_orcid_ids(text),
        "dois": extract_dois(text),
        "education_section": extract_section(text, ["education", "degrees"]),
        "publications_section": extract_section(text, ["publications"]),
        "research_projects_section": extract_section(text, ["research projects", "projects"]),
        "teaching_section": extract_section(text, ["teaching experience", "teaching"]),
    }
    
def build_structured_preview(text: str):
    return {
        "orcid_ids": extract_orcid_ids(text),
        "dois": extract_dois(text),
        "degrees": parse_degrees(text),
        "publications": parse_publications(text),
        "research_projects": parse_research_projects(text),
        "teaching_experience": parse_teaching_experience(text)
    }

def clean_cv_line(line: str) -> str:
    bullet_characters = "•●▪◦‣⁃–—-*"

    cleaned_line = line.strip()
    cleaned_line = cleaned_line.lstrip(bullet_characters)
    cleaned_line = cleaned_line.strip()

    return cleaned_line


def parse_publications(text: str) -> list[dict]:
    publications_section = extract_section(
        text,
        ["publications"]
    )

    if not publications_section:
        return []

    raw_lines = [
        clean_cv_line(line)
        for line in publications_section.splitlines()
        if clean_cv_line(line)
    ]

    combined_entries: list[str] = []
    current_entry = ""

    for line in raw_lines:
        if current_entry:
            current_entry = f"{current_entry} {line}"
        else:
            current_entry = line

        line_dois = extract_dois(current_entry)

        if line_dois:
            combined_entries.append(current_entry.strip())
            current_entry = ""

    if current_entry:
        combined_entries.append(current_entry.strip())

    publications = []

    for entry in combined_entries:
        entry_dois = extract_dois(entry)

        cleaned_title = entry

        for doi in entry_dois:
            cleaned_title = cleaned_title.replace(doi, "")

        cleaned_title = re.sub(
            r"\bDOI\s*:\s*$",
            "",
            cleaned_title,
            flags=re.IGNORECASE
        )

        cleaned_title = re.sub(
            r"\s+",
            " ",
            cleaned_title
        )

        cleaned_title = cleaned_title.strip(" -–—.,;:")

        if not cleaned_title:
            continue

        publications.append(
            {
                "title": cleaned_title,
                "doi": entry_dois[0] if entry_dois else None
            }
        )

    return publications

def parse_degrees(text: str) -> list[dict]:
    education_section = extract_section(
        text,
        ["education", "degrees"]
    )

    if not education_section:
        return []

    lines = [
        clean_cv_line(line)
        for line in education_section.splitlines()
        if clean_cv_line(line)
    ]

    degrees = []

    for line in lines:
        year_match = re.search(
            r"\b(19|20)\d{2}\b",
            line
        )

        year = int(year_match.group()) if year_match else None

        cleaned_line = line

        if year_match:
            cleaned_line = cleaned_line.replace(
                year_match.group(),
                ""
            )

        cleaned_line = re.sub(
            r"\s+",
            " ",
            cleaned_line
        ).strip(" -–—,.;")

        if not cleaned_line:
            continue

        parts = [
            part.strip()
            for part in cleaned_line.split(",")
            if part.strip()
        ]

        title = parts[0] if parts else cleaned_line
        institution = parts[1] if len(parts) > 1 else None

        degrees.append(
            {
                "title": title,
                "institution": institution,
                "year": year
            }
        )

    return degrees

def parse_teaching_experience(text: str) -> list[dict]:
    teaching_section = extract_section(
        text,
        ["teaching experience", "teaching"]
    )

    if not teaching_section:
        return []

    lines = [
        clean_cv_line(line)
        for line in teaching_section.splitlines()
        if clean_cv_line(line)
    ]

    teaching_entries = []

    for line in lines:
        cleaned_line = re.sub(r"\s+", " ", line).strip(" -–—,.;")

        if not cleaned_line:
            continue

        teaching_entries.append(
            {
                "course": cleaned_line
            }
        )

    return teaching_entries

def parse_research_projects(text: str) -> list[dict]:
    projects_section = extract_section(
        text,
        ["research projects", "projects"]
    )

    if not projects_section:
        return []

    lines = [
        clean_cv_line(line)
        for line in projects_section.splitlines()
        if clean_cv_line(line)
    ]

    projects = []
    current_entry = ""

    role_keywords = [
        "principal investigator",
        "co-principal investigator",
        "researcher",
        "postdoctoral researcher",
        "doctoral researcher",
        "phd researcher",
        "technical lead",
        "work package leader",
        "project coordinator",
        "scientific coordinator"
    ]

    for line in lines:
        lower_line = line.lower()

        is_role_line = any(
            role in lower_line
            for role in role_keywords
        )

        has_date_range = bool(
            re.search(r"\b(19|20)\d{2}\s*[-–—]\s*(19|20)\d{2}\b", line)
        )

        has_funding = "funding" in lower_line

        if current_entry and (
            is_role_line
            or has_date_range
            or has_funding
        ):
            current_entry = f"{current_entry} {line}".strip()

            projects.append(
                {
                    "title": re.sub(
                        r"\s+",
                        " ",
                        current_entry
                    ).strip(" -–—,.;")
                }
            )

            current_entry = ""

        else:
            if current_entry:
                projects.append(
                    {
                        "title": re.sub(
                            r"\s+",
                            " ",
                            current_entry
                        ).strip(" -–—,.;")
                    }
                )

            current_entry = line

    if current_entry:
        projects.append(
            {
                "title": re.sub(
                    r"\s+",
                    " ",
                    current_entry
                ).strip(" -–—,.;")
            }
        )

    return projects

def import_parsed_cv_data(
    db: Session,
    profile: AcademicProfile,
    parsed_data: dict
):
    profile_updated = False

    degrees_imported = 0
    degrees_skipped = 0

    publications_imported = 0
    publications_skipped = 0

    research_projects_imported = 0
    research_projects_skipped = 0

    teaching_imported = 0
    teaching_skipped = 0

    # -------------------------------------------------
    # Academic Profile / ORCID
    # -------------------------------------------------

    orcid_ids = parsed_data.get("orcid_ids", [])

    if orcid_ids:
        detected_orcid = orcid_ids[0]

        if profile.orcid_id != detected_orcid:
            profile.orcid_id = detected_orcid
            profile_updated = True

    # -------------------------------------------------
    # Degrees
    # -------------------------------------------------

    for degree in parsed_data.get("degrees", []):
        title = degree.get("title")
        institution_name = degree.get("institution") or "Unknown Institution"
        end_year = degree.get("year")

        if not title:
            degrees_skipped += 1
            continue

        degree_type = "Education"

        existing_degree = get_duplicate_degree(
            db=db,
            profile_id=profile.id,
            degree_type=degree_type,
            title=title,
            institution_name=institution_name,
            end_year=end_year
        )

        if existing_degree:
            degrees_skipped += 1
            continue

        degree_data = DegreeCreate(
            degree_type=degree_type,
            title=title,
            field_of_study=None,
            institution_name=institution_name,
            country=None,
            start_year=None,
            end_year=end_year
        )

        create_degree(
            db=db,
            profile_id=profile.id,
            degree_data=degree_data
        )

        degrees_imported += 1

    # -------------------------------------------------
    # Publications
    # -------------------------------------------------

    for publication in parsed_data.get("publications", []):
        title = publication.get("title")
        doi = publication.get("doi")

        if not title:
            publications_skipped += 1
            continue

        if doi:
            existing_publication = get_publication_by_doi(
                db=db,
                profile_id=profile.id,
                doi=doi
            )

            if existing_publication:
                publications_skipped += 1
                continue

        publication_data = PublicationCreate(
            title=title,
            abstract=None,
            publication_type=None,
            publication_year=None,
            doi=doi,
            journal_name=None,
            conference_name=None,
            publisher=None,
            citation_count=0,
            openalex_id=None,
            orcid_work_id=None
        )

        create_publication(
            db=db,
            profile_id=profile.id,
            publication_data=publication_data
        )

        publications_imported += 1

    # -------------------------------------------------
    # Research Projects
    # -------------------------------------------------

    for project in parsed_data.get("research_projects", []):
        title = project.get("title")

        if not title:
            research_projects_skipped += 1
            continue

        existing_project = get_research_project_by_title(
            db=db,
            profile_id=profile.id,
            title=title
        )

        if existing_project:
            research_projects_skipped += 1
            continue

        project_data = ResearchProjectCreate(
            title=title,
            acronym=None,
            funding_program=None,
            funding_organization=None,
            role=None,
            status=None,
            funding_amount=None,
            currency="EUR",
            start_date=None,
            end_date=None,
            project_identifier=None,
            website_url=None,
            keywords=None,
            description=None
        )

        create_research_project(
            db=db,
            profile_id=profile.id,
            project_data=project_data
        )

        research_projects_imported += 1

    # -------------------------------------------------
    # Teaching Experience
    # -------------------------------------------------

    for teaching in parsed_data.get("teaching_experience", []):
        course_title = teaching.get("course")

        if not course_title:
            teaching_skipped += 1
            continue

        existing_teaching = get_duplicate_teaching_experience(
            db=db,
            profile_id=profile.id,
            course_title=course_title
        )

        if existing_teaching:
            teaching_skipped += 1
            continue

        teaching_data = TeachingExperienceCreate(
            course_title=course_title,
            institution_name=None,
            department_name=None,
            academic_year=None,
            semester=None,
            course_level=None,
            teaching_role=None,
            hours_per_week=None,
            description=None
        )

        create_teaching_experience(
            db=db,
            profile_id=profile.id,
            teaching_data=teaching_data
        )

        teaching_imported += 1

    if profile_updated:
        db.commit()
        db.refresh(profile)

    return {
        "profile_updated": profile_updated,
        "degrees_imported": degrees_imported,
        "degrees_skipped": degrees_skipped,
        "publications_imported": publications_imported,
        "publications_skipped": publications_skipped,
        "research_projects_imported": research_projects_imported,
        "research_projects_skipped": research_projects_skipped,
        "teaching_imported": teaching_imported,
        "teaching_skipped": teaching_skipped,
    }