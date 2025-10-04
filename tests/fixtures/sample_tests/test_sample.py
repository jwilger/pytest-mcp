"""Sample test fixtures for execute_tests integration testing.

These tests are executed by execute_tests() to avoid infinite recursion.
They do NOT call execute_tests() themselves.
"""


def test_passing() -> None:
    """A simple passing test."""
    assert True


def test_another_passing() -> None:
    """Another simple passing test."""
    assert 1 + 1 == 2


def test_failing() -> None:
    """A test that fails."""
    raise AssertionError("This test intentionally fails")
