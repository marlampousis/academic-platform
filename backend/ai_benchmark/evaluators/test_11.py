
from collections import Counter
from typing import Any
import json

from .automatic import (
    calculate_precision,
    calculate_recall,
    calculate_f1,
)


def _same_type_and_value(actual: Any, expected: Any) -> bool:
    if type(actual) is not type(expected):
        return False

    if isinstance(expected, dict):
        return (
            actual.keys() == expected.keys()
            and all(
                _same_type_and_value(actual[key], value)
                for key, value in expected.items()
            )
        )

    if isinstance(expected, list):
        return (
            len(actual) == len(expected)
            and all(
                _same_type_and_value(a, e)
                for a, e in zip(actual, expected)
            )
        )

    return actual == expected


def _fingerprint(item: Any) -> str:
    return json.dumps(
        item,
        ensure_ascii=False,
        sort_keys=True,
    )


def _record_scores(
    actual: Any,
    expected: Any,
    fields: list[str],
) -> tuple[float, float, float]:

    if not isinstance(actual, list):
        actual = []

    if not isinstance(expected, list):
        expected = []

    def normalized_record(item: Any) -> str:
        if not isinstance(item, dict):
            return _fingerprint(item)

        if set(item) != set(fields):
            return _fingerprint(item)

        return _fingerprint({
            field: item[field]
            for field in fields
        })

    actual_counts = Counter(
        normalized_record(item) for item in actual
    )
    expected_counts = Counter(
        normalized_record(item) for item in expected
    )

    true_positives = sum(
        (actual_counts & expected_counts).values()
    )

    false_positives = len(actual) - true_positives
    false_negatives = len(expected) - true_positives

    precision = calculate_precision(
        true_positives,
        false_positives,
    )
    recall = calculate_recall(
        true_positives,
        false_negatives,
    )

    return (
        precision,
        recall,
        calculate_f1(precision, recall),
    )


def _valid_structure(
    actual: Any,
    expected: Any,
) -> bool:

    if type(actual) is not type(expected):
        return False

    if isinstance(expected, dict):
        return (
            set(actual) == set(expected)
            and all(
                _valid_structure(actual[key], value)
                for key, value in expected.items()
            )
        )

    if isinstance(expected, list):
        if not expected:
            return True

        template = expected[0]

        return all(
            _valid_structure(item, template)
            for item in actual
        )

    return True


def _greek_value_consistency(
    actual: Any,
    expected: Any,
) -> float:
    """
    Compare all Greek-language scalar values.

    English titles and proper names are not included.
    """

    pairs = []

    def collect(actual_value, expected_value):
        if isinstance(expected_value, dict):
            if not isinstance(actual_value, dict):
                actual_value = {}

            for key, value in expected_value.items():
                collect(actual_value.get(key), value)

        elif isinstance(expected_value, list):
            if not isinstance(actual_value, list):
                actual_value = []

            for index, value in enumerate(expected_value):
                item = (
                    actual_value[index]
                    if index < len(actual_value)
                    else None
                )
                collect(item, value)

        elif isinstance(expected_value, str):
            if any(
                "\u0370" <= char <= "\u03ff"
                or "\u1f00" <= char <= "\u1fff"
                for char in expected_value
            ):
                pairs.append(
                    actual_value == expected_value
                )

    collect(actual, expected)

    return (
        sum(pairs) / len(pairs)
        if pairs
        else 1.0
    )


def evaluate_test_11(
    parsed_response: Any,
    expected_data: dict[str, Any],
) -> dict[str, Any]:

    keys = expected_data["expected_schema"][
        "required_top_level_fields"
    ]
    reference = expected_data["expected"]
    nested = expected_data["nested_schema"]

    if not isinstance(parsed_response, dict):
        return {
            "schema_compliance": False,
            "exact_keys": False,
            "highest_degree_selection": False,
            "publication_precision": 0.0,
            "publication_recall": 0.0,
            "publication_f1": 0.0,
            "teaching_precision": 0.0,
            "teaching_recall": 0.0,
            "teaching_f1": 0.0,
            "research_project_accuracy": 0.0,
            "greek_value_consistency": 0.0,
        }

    degree_key = keys[3]
    publications_key = keys[4]
    projects_key = keys[5]
    teaching_key = keys[6]

    exact_keys = set(parsed_response) == set(keys)

    schema_compliance = (
        exact_keys
        and _valid_structure(
            parsed_response,
            reference,
        )
    )

    highest_degree_selection = _same_type_and_value(
        parsed_response.get(degree_key),
        reference[degree_key],
    )

    pub_p, pub_r, pub_f1 = _record_scores(
        parsed_response.get(publications_key),
        reference[publications_key],
        nested["δημοσίευση"],
    )

    teach_p, teach_r, teach_f1 = _record_scores(
        parsed_response.get(teaching_key),
        reference[teaching_key],
        nested["διδακτική_εμπειρία"],
    )

    _, _, projects_f1 = _record_scores(
        parsed_response.get(projects_key),
        reference[projects_key],
        nested["ερευνητικό_έργο"],
    )

    greek_consistency = _greek_value_consistency(
        parsed_response,
        reference,
    )

    return {
        "schema_compliance": schema_compliance,
        "exact_keys": exact_keys,
        "highest_degree_selection": highest_degree_selection,
        "publication_precision": pub_p,
        "publication_recall": pub_r,
        "publication_f1": pub_f1,
        "teaching_precision": teach_p,
        "teaching_recall": teach_r,
        "teaching_f1": teach_f1,
        "research_project_accuracy": projects_f1,
        "greek_value_consistency": greek_consistency,
    }
