
from typing import Any


def validate_test_08_schema(
    parsed_response: Any,
    expected_data: dict[str, Any],
) -> bool:
    """Validate the exact required JSON structure."""

    if not isinstance(parsed_response, dict):
        return False

    schema = expected_data["expected_schema"]

    if set(parsed_response) != set(
        schema["required_top_level_fields"]
    ):
        return False

    publications = parsed_response.get(
        "relevant_publications"
    )

    if not isinstance(publications, list):
        return False

    required_fields = set(
        schema["publication_required_fields"]
    )

    for publication in publications:
        if not isinstance(publication, dict):
            return False

        if set(publication) != required_fields:
            return False

        if (
            not isinstance(publication["title"], str)
            or not publication["title"].strip()
        ):
            return False

        if type(publication["publication_year"]) is not int:
            return False

        areas = publication["relevant_position_areas"]

        if not isinstance(areas, list):
            return False

        if not areas:
            return False

        if not all(
            isinstance(area, str) and area.strip()
            for area in areas
        ):
            return False

        if (
            not isinstance(publication["evidence"], str)
            or not publication["evidence"].strip()
        ):
            return False

    return True


def evaluate_test_08(
    parsed_response: Any,
    expected_data: dict[str, Any],
) -> dict[str, Any]:
    """Evaluate Test 08: Evidence Retrieval."""

    schema_compliance = validate_test_08_schema(
        parsed_response,
        expected_data,
    )

    results = {
        "schema_compliance": schema_compliance,
        "publication_precision": None,
        "publication_year_accuracy": None,
        "position_area_accuracy": None,
        "maximum_item_compliance": None,
        "minimum_item_compliance": None,
        "duplicate_publication_titles": [],
        "duplicate_position_areas": {},
    }

    if not schema_compliance:
        return results

    publications = parsed_response[
        "relevant_publications"
    ]

    maximum = expected_data["max_publications"]

    results["maximum_item_compliance"] = (
        len(publications) <= maximum
    )

    minimum = expected_data["constraints"]["minimum_publications"]

    results["minimum_item_compliance"] = (
        len(publications) >= minimum
    )

    valid_publications = {
        publication["title"]: publication
        for publication in expected_data["valid_publications"]
    }

    if not publications:
        results["publication_precision"] = 0.0
        results["publication_year_accuracy"] = None
        results["position_area_accuracy"] = None
        return results

    correct_publications = 0
    correct_years = 0
    checked_years = 0
    correct_areas = 0
    checked_areas = 0

    seen_titles = set()
    duplicate_titles = set()
    duplicate_areas = {}

    for publication in publications:
        title = publication["title"]

        if title in seen_titles:
            duplicate_titles.add(title)

        area_names = publication["relevant_position_areas"]
        seen_areas = set()
        repeated_areas = set()

        for area in area_names:
            if area in seen_areas:
                repeated_areas.add(area)
            seen_areas.add(area)

        if repeated_areas:
            duplicate_areas[title] = sorted(repeated_areas)

        # Repeated publications do not count as new
        # correct retrievals.
        is_valid = (
            title in valid_publications
            and title not in seen_titles
        )

        seen_titles.add(title)

        if not is_valid:
            continue

        correct_publications += 1

        expected_publication = valid_publications[title]

        checked_years += 1

        if (
            publication["publication_year"]
            == expected_publication["publication_year"]
        ):
            correct_years += 1

        acceptable_areas = set(
            expected_publication[
                "acceptable_position_areas"
            ]
        )

        counted_areas = set()

        for area in publication["relevant_position_areas"]:
            checked_areas += 1

            if area in counted_areas:
                continue

            counted_areas.add(area)

            if area in acceptable_areas:
                correct_areas += 1

    results["publication_precision"] = (
        correct_publications / len(publications)
    )

    results["publication_year_accuracy"] = (
        correct_years / checked_years
        if checked_years
        else None
    )

    results["position_area_accuracy"] = (
        correct_areas / checked_areas
        if checked_areas
        else 0.0
    )

    results["duplicate_publication_titles"] = sorted(
        duplicate_titles
    )

    results["duplicate_position_areas"] = duplicate_areas

    return results
