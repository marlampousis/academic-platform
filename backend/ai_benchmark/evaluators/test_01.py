from typing import Any

from .automatic import (
    calculate_f1,
    calculate_precision,
    calculate_recall,
)


REQUIRED_FIELDS = {
    "name",
    "specialization",
    "research_areas",
    "degrees",
    "publication_titles",
    "research_project_titles",
    "teaching_course_titles",
}


SCALAR_FIELDS = [
    "name",
    "specialization",
]


LIST_FIELDS = [
    "research_areas",
    "degrees",
    "publication_titles",
    "research_project_titles",
    "teaching_course_titles",
]


def normalize_value(value: Any) -> str:
    """
    Normalize a scalar value for comparison.
    """

    if value is None:
        return ""

    return str(value).strip().casefold()



def schema_compliance(
    parsed_response: Any,
) -> bool:
    """
    Validate the required Test 01 JSON structure,
    including nested degree objects.
    """

    if not isinstance(parsed_response, dict):
        return False

    if set(parsed_response.keys()) != REQUIRED_FIELDS:
        return False

    for field in SCALAR_FIELDS:
        value = parsed_response[field]

        if value is not None and not isinstance(value, str):
            return False

    for field in LIST_FIELDS:
        if not isinstance(parsed_response[field], list):
            return False

    for field in [
        "research_areas",
        "publication_titles",
        "research_project_titles",
        "teaching_course_titles",
    ]:
        if not all(
            isinstance(item, str)
            for item in parsed_response[field]
        ):
            return False

    required_degree_fields = {
        "degree_type",
        "title",
        "field_of_study",
        "institution_name",
        "country",
        "start_year",
        "end_year",
    }

    for degree in parsed_response["degrees"]:

        if not isinstance(degree, dict):
            return False

        if set(degree.keys()) != required_degree_fields:
            return False

        for field in [
            "degree_type",
            "title",
            "field_of_study",
            "institution_name",
            "country",
        ]:
            value = degree[field]

            if value is not None and not isinstance(value, str):
                return False

        for field in ["start_year", "end_year"]:
            value = degree[field]

            if value is not None and (
                type(value) is not int
            ):
                return False

    return True


def scalar_field_accuracy(
    parsed_response: dict[str, Any],
    expected_data: dict[str, Any],
) -> float:
    """
    Calculate accuracy across scalar Test 01 fields.
    """

    correct = 0
    total = len(SCALAR_FIELDS)

    for field in SCALAR_FIELDS:

        actual = normalize_value(
            parsed_response.get(field)
        )

        expected = normalize_value(
            expected_data.get(field)
        )

        if actual == expected:
            correct += 1

    if total == 0:
        return 0.0

    return correct / total


def normalize_list_item(
    item: Any,
) -> str:
    """
    Normalize list items for comparison.
    """

    if isinstance(item, dict):
        normalized_pairs = []

        for key in sorted(item.keys()):
            value = normalize_value(
                item[key]
            )

            normalized_pairs.append(
                f"{key}:{value}"
            )

        return "|".join(
            normalized_pairs
        )

    return normalize_value(item)



def calculate_list_metrics(
    actual_list: list[Any],
    expected_list: list[Any],
) -> dict[str, float]:
    """
    Calculate precision, recall and F1
    for a single list field.
    """

    # Handle the case where both lists are empty.
    if not actual_list and not expected_list:
        return {
            "precision": 1.0,
            "recall": 1.0,
            "f1": 1.0,
        }

    actual_set = {
        normalize_list_item(item)
        for item in actual_list
    }

    expected_set = {
        normalize_list_item(item)
        for item in expected_list
    }

    true_positives = len(
        actual_set & expected_set
    )

    false_positives = len(
        actual_set - expected_set
    )

    false_negatives = len(
        expected_set - actual_set
    )

    precision = calculate_precision(
        true_positives,
        false_positives,
    )

    recall = calculate_recall(
        true_positives,
        false_negatives,
    )

    f1 = calculate_f1(
        precision,
        recall,
    )

    return {
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }


def calculate_degree_field_accuracy(
    actual_degrees: list[Any],
    expected_degrees: list[Any],
) -> float:
    """
    Calculate field-level accuracy for academic degrees.

    Degrees are matched by normalized title.
    Unmatched expected degrees count as incorrect.
    """

    degree_fields = [
        "degree_type",
        "title",
        "field_of_study",
        "institution_name",
        "country",
        "start_year",
        "end_year",
    ]

    if not expected_degrees:
        return 1.0 if not actual_degrees else 0.0

    actual_by_title = {}

    for degree in actual_degrees:
        if not isinstance(degree, dict):
            continue

        title = normalize_value(degree.get("title"))

        if title:
            actual_by_title[title] = degree

    correct_fields = 0
    total_fields = len(expected_degrees) * len(degree_fields)

    for expected_degree in expected_degrees:
        expected_title = normalize_value(
            expected_degree.get("title")
        )

        actual_degree = actual_by_title.get(expected_title)

        if actual_degree is None:
            continue

        for field in degree_fields:
            actual_value = actual_degree.get(field)
            expected_value = expected_degree.get(field)

            # Compare types as well as values.
            if (
                type(actual_value) is type(expected_value)
                and normalize_value(actual_value)
                == normalize_value(expected_value)
            ):
                correct_fields += 1

    return correct_fields / total_fields


def evaluate_test_01(
    parsed_response: Any,
    expected_data: dict[str, Any],
) -> dict[str, Any]:
    """
    Calculate Test 01 specific automatic metrics.
    """

    if not isinstance(parsed_response, dict):
        return {
            "schema_compliance": False,
            "field_accuracy": 0.0,
            "list_precision": 0.0,
            "list_recall": 0.0,
            "list_f1": 0.0,
            "degree_field_accuracy": 0.0,
        }

    schema_valid = schema_compliance(
        parsed_response
    )

    field_accuracy = scalar_field_accuracy(
        parsed_response,
        expected_data,
    )

    precision_values = []
    recall_values = []
    f1_values = []

    for field in LIST_FIELDS:

        actual_list = parsed_response.get(
            field,
            [],
        )

        expected_list = expected_data.get(
            field,
            [],
        )

        if not isinstance(actual_list, list):
            actual_list = []

        if not isinstance(expected_list, list):
            expected_list = []

        metrics = calculate_list_metrics(
            actual_list,
            expected_list,
        )

        precision_values.append(
            metrics["precision"]
        )

        recall_values.append(
            metrics["recall"]
        )

        f1_values.append(
            metrics["f1"]
        )

    number_of_lists = len(LIST_FIELDS)

    degree_field_accuracy = calculate_degree_field_accuracy(
        parsed_response.get("degrees", [])
        if isinstance(parsed_response.get("degrees"), list)
        else [],
        expected_data.get("degrees", []),
    )

    return {
        "schema_compliance": schema_valid,
        "field_accuracy": field_accuracy,
        "list_precision": (
            sum(precision_values)
            / number_of_lists
        ),
        "list_recall": (
            sum(recall_values)
            / number_of_lists
        ),
        "list_f1": (
            sum(f1_values)
            / number_of_lists
        ),
        "degree_field_accuracy": degree_field_accuracy,
    }
    
def validate_test_01_expected_data(
    expected_data: dict[str, Any],
) -> None:
    """
    Validate that Test 01 ground-truth data has the structure
    required by the evaluator.
    """

    missing_fields = (
        REQUIRED_FIELDS
        - set(expected_data.keys())
    )

    if missing_fields:
        raise ValueError(
            "Test 01 expected data is missing fields: "
            f"{sorted(missing_fields)}"
        )

    if not isinstance(
        expected_data["research_areas"],
        list,
    ):
        raise TypeError(
            "research_areas must be a list"
        )

    if not isinstance(
        expected_data["degrees"],
        list,
    ):
        raise TypeError(
            "degrees must be a list"
        )

    if not isinstance(
        expected_data["publication_titles"],
        list,
    ):
        raise TypeError(
            "publication_titles must be a list"
        )

    if not isinstance(
        expected_data["research_project_titles"],
        list,
    ):
        raise TypeError(
            "research_project_titles must be a list"
        )

    if not isinstance(
        expected_data["teaching_course_titles"],
        list,
    ):
        raise TypeError(
            "teaching_course_titles must be a list"
        )    