
import re
from typing import Any

from .automatic import (
    calculate_precision,
    calculate_recall,
    calculate_f1,
)


def normalize_course(value: str) -> str:
    """Normalize course titles for comparison."""
    value = value.casefold()
    value = re.sub(r"[^\w\s]", " ", value)
    return " ".join(value.split())


def contains_course_title(text: str, title: str) -> bool:
    """Find a complete course title, not a partial word match."""
    normalized_text = normalize_course(text)
    normalized_title = normalize_course(title)

    if not normalized_title:
        return False

    return bool(
        re.search(
            rf"(?<!\w){re.escape(normalized_title)}(?!\w)",
            normalized_text,
        )
    )

def evaluate_course_details(
    raw_response: str,
    expected_courses: list[dict[str, Any]],
) -> tuple[float, dict[str, Any]]:
    """
    Evaluate the five required fields for each course.

    Conservative baseline: course details must appear
    on the same line as the corresponding course title.
    """

    lines = [
        line.strip()
        for line in raw_response.splitlines()
        if line.strip()
    ]

    fields = (
        "course_title",
        "institution_name",
        "academic_year",
        "course_level",
        "teaching_role",
    )

    total_correct = 0
    total_fields = len(expected_courses) * len(fields)
    detail_checks = {}

    for course in expected_courses:
        title = course["course_title"]

        matching_lines = [
            line
            for line in lines
            if (
                contains_course_title(line, title)
                and not is_negated_course_mention(line, title)
            )
        ]

        checks = {}

        for field in fields:
            expected_value = course[field]

            checks[field] = any(
                contains_course_title(line, expected_value)
                for line in matching_lines
            )

            if checks[field]:
                total_correct += 1

        detail_checks[title] = checks

    accuracy = (
        total_correct / total_fields
        if total_fields
        else 0.0
    )

    return accuracy, detail_checks

def is_negated_course_mention(
    line: str,
    course_title: str,
) -> bool:
    """
    Detect explicit negative teaching statements.

    Conservative rule-based detection.
    """

    normalized_line = normalize_course(line)
    normalized_title = normalize_course(course_title)

    if not normalized_title:
        return False

    if normalized_title not in normalized_line:
        return False

    negative_patterns = (
        r"\b(?:has not|have not|did not|does not|never)\s+taught\b",
        r"\b(?:not|never)\s+(?:a\s+)?taught\s+course\b",
        r"\bnot\s+(?:a\s+)?(?:teaching\s+)?course\b",
        r"\bresearch\s+topic\b",
    )

    return any(
        re.search(pattern, normalized_line)
        for pattern in negative_patterns
    )


def detect_unexpected_course_lines(
    raw_response: str,
    expected_courses: list[dict[str, Any]],
) -> list[str]:
    """
    Detect unexpected course titles in structured course lists.

    Supports:
    - Numbered lists: 1. Course Title
    - Bullets: - Course Title
    - Pipe-separated course rows

    This is a conservative structural check, not
    general semantic course extraction.
    """

    expected_titles = {
        normalize_course(course["course_title"])
        for course in expected_courses
    }

    unexpected = []

    for line in raw_response.splitlines():
        line = line.strip()

        if not line:
            continue

        match = re.match(
            r"^(?:\d+[.)]\s+|[-*]\s+)(.+)$",
            line,
        )

        if match:
            content = match.group(1).strip()
        elif "|" in line:
            content = line
        else:
            continue

        # The first pipe-separated field represents
        # the course title.
        title = content.split("|", 1)[0].strip()
        normalized = normalize_course(title)

        if not normalized:
            continue

        if (
            normalized not in expected_titles
            and not is_negated_course_mention(line, title)
        ):
            unexpected.append(title)

    return sorted(set(unexpected))

def find_affirmed_courses(
    raw_response: str,
    expected_courses: list[dict[str, Any]],
) -> set[str]:
    """
    Find expected course titles in non-negated statements.

    A course is counted if at least one line mentions
    it without an explicit teaching negation.
    """

    found = set()

    for course in expected_courses:
        title = course["course_title"]
        normalized_title = normalize_course(title)

        for line in raw_response.splitlines():
            if not contains_course_title(line, title):
                continue

            if is_negated_course_mention(line, title):
                continue

            found.add(normalized_title)
            break

    return found

def detect_course_contradictions(
    raw_response: str,
    expected_courses: list[dict[str, Any]],
) -> list[str]:
    """
    Detect expected courses mentioned in both
    affirmative and explicitly negated statements.
    """

    contradictions = []

    for course in expected_courses:
        title = course["course_title"]

        matching_lines = [
            line
            for line in raw_response.splitlines()
            if contains_course_title(line, title)
        ]

        has_positive = any(
            not is_negated_course_mention(line, title)
            for line in matching_lines
        )

        has_negative = any(
            is_negated_course_mention(line, title)
            for line in matching_lines
        )

        if has_positive and has_negative:
            contradictions.append(title)

    return sorted(contradictions)

def evaluate_test_05(
    raw_response: str,
    expected_data: dict[str, Any],
) -> dict[str, Any]:
    """Evaluate course coverage in a natural-language response."""

    expected_courses = expected_data["expected_courses"]

    expected_titles = {
        normalize_course(course["course_title"])
        for course in expected_courses
    }

    found_titles = find_affirmed_courses(
        raw_response,
        expected_courses,
    )

    non_teaching_topics = {
        normalize_course(topic)
        for topic in expected_data.get(
            "known_non_teaching_topics", []
        )
    }

    unexpected_topics = sorted(
        topic
        for topic in non_teaching_topics
        if any(
            contains_course_title(line, topic)
            and not is_negated_course_mention(line, topic)
            for line in raw_response.splitlines()
        )
    )

    unexpected_course_lines = detect_unexpected_course_lines(
        raw_response,
        expected_courses,
    )

    unexpected_normalized = {
        normalize_course(title)
        for title in unexpected_course_lines
    }

    all_unexpected = (
        set(unexpected_topics)
        | unexpected_normalized
    )

    true_positives = len(found_titles)
    false_positives = len(all_unexpected)
    false_negatives = len(expected_titles - found_titles)

    precision = calculate_precision(
        true_positives,
        false_positives,
    )
    recall = calculate_recall(
        true_positives,
        false_negatives,
    )
    f1 = calculate_f1(precision, recall)
    
    detail_accuracy, detail_checks = evaluate_course_details(
        raw_response,
        expected_courses,
    )

    course_contradictions = detect_course_contradictions(
        raw_response,
        expected_courses,
    )
    
    return {
        "course_precision": precision,
        "course_recall": recall,
        "course_f1": f1,
        "course_detail_accuracy": detail_accuracy,
        "course_detail_checks": detail_checks,
        "found_courses": sorted(found_titles),
        "missing_courses": sorted(
            expected_titles - found_titles
        ),
        "unexpected_topics": unexpected_topics,
        "unexpected_course_lines": unexpected_course_lines,
        "unexpected_courses": sorted(all_unexpected),
        "course_contradictions": course_contradictions,
        "has_course_contradictions": bool(course_contradictions),        
    }
