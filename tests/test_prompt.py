from pathlib import Path

import pytest
import yaml

from src.nl2sql.prompt import generate_sql
from src.nl2sql.validator import (
    validate_sql,
    contains_expected,
)


DATASET = Path(
    "datasets/prompt_validation.yaml"
)


def load_test_cases():

    with open(DATASET, "r") as file:
        data = yaml.safe_load(file)

    return data["tests"]


TEST_CASES = load_test_cases()


@pytest.mark.parametrize(
    "test_case",
    TEST_CASES,
    ids=lambda test: test["id"],
)
def test_prompt_validation(test_case):

    question = test_case["question"]
    expected = test_case["expected"]

    response = generate_sql(question)

    # Security validation
    if expected.get("should_reject"):

        assert response == "REJECTED"

        return

    # Ambiguity validation
    if expected.get("should_clarify"):

        assert response == "CLARIFICATION_REQUIRED"

        return

    # SQL should be valid
    assert validate_sql(response), (
        f"Invalid SQL generated for: {question}\n"
        f"SQL: {response}"
    )

    # Expected SQL components
    expected_contains = expected.get(
        "sql_contains",
        []
    )

    assert contains_expected(
        response,
        expected_contains
    ), (
        f"Expected SQL components missing.\n"
        f"Question: {question}\n"
        f"SQL: {response}\n"
        f"Expected: {expected_contains}"
    )

    # Forbidden SQL
    forbidden = expected.get(
        "sql_not_contains",
        []
    )

    assert not contains_expected(
        response,
        forbidden
    ), (
        f"Forbidden SQL detected.\n"
        f"Question: {question}\n"
        f"SQL: {response}"
    )