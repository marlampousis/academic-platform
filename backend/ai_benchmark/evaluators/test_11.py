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
    """Compare Greek scalar values by field path, ignoring list order.

    Multiset counts preserve duplicates. This measures value coverage only;
    complete-record metrics separately check which values belong together.
    """
    def greek_values(value: Any) -> Counter:
        result = Counter()

        def collect(item: Any, path: tuple) -> None:
            if isinstance(item, dict):
                for key, child in item.items():
                    collect(child, path + (key,))
            elif isinstance(item, list):
                for child in item:
                    collect(child, path + ("[]",))
            elif isinstance(item, str) and any(
                ("\u0370" <= char <= "\u03ff" or
                 "\u1f00" <= char <= "\u1fff") and char.isalpha()
                for char in item
            ):
                result[(path, item)] += 1

        collect(value, ())
        return result

    expected_values = greek_values(expected)
    actual_values = greek_values(actual)
    total = sum(expected_values.values())
    return (
        sum((actual_values & expected_values).values()) / total
        if total else 1.0
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
            "name_accuracy": False,
            "specialization_accuracy": False,
            "research_areas_exact_match": False,
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
        "name_accuracy": _same_type_and_value(
            parsed_response.get(keys[0]), reference[keys[0]],
        ),
        "specialization_accuracy": _same_type_and_value(
            parsed_response.get(keys[1]), reference[keys[1]],
        ),
        "research_areas_exact_match": (
            isinstance(parsed_response.get(keys[2]), list)
            and Counter(_fingerprint(x) for x in parsed_response[keys[2]])
            == Counter(_fingerprint(x) for x in reference[keys[2]])
        ),
        "publication_precision": pub_p,
        "publication_recall": pub_r,
        "publication_f1": pub_f1,
        "teaching_precision": teach_p,
        "teaching_recall": teach_r,
        "teaching_f1": teach_f1,
        "research_project_accuracy": projects_f1,
        "greek_value_consistency": greek_consistency,
    }
