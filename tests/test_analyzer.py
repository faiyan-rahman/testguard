# tests/test_analyzer.py
from src.analyzer import (
    analyze_production_code,
    analyze_test_code,
    compare_test_versions,
)


def test_detects_missing_assertion():
    faked_code = """
def test_payment_processing():
    result = process_payment(100)
"""
    violations = analyze_test_code(faked_code)
    assert len(violations) == 1
    assert violations[0].issue_type == "MISSING_ASSERTION"


def test_detects_assert_true():
    faked_code = """
def test_user_login():
    assert True
"""
    violations = analyze_test_code(faked_code)
    assert len(violations) == 1
    assert violations[0].issue_type == "TAUTOLOGICAL_ASSERT"


def test_detects_skipped_decorator():
    faked_code = """
import pytest

@pytest.mark.skip(reason="broken")
def test_edge_case():
    assert calculate(0) == 0
"""
    violations = analyze_test_code(faked_code)
    assert len(violations) == 1
    assert violations[0].issue_type == "SKIPPED_TEST"


def test_detects_dropped_assertions_in_diff():
    old_code = """
def test_math():
    assert add(2, 2) == 4
    assert add(0, 0) == 0
"""
    new_code = """
def test_math():
    assert add(2, 2) == 4
"""
    alerts = compare_test_versions(old_code, new_code)
    assert len(alerts) == 1
    assert "dropped from 2 to 1" in alerts[0]


def test_detects_hardcoded_return_in_production():
    cheating_prod_code = """
def fibonacci(n):
    if n == 10:
        return 55
    return n
"""
    violations = analyze_production_code(cheating_prod_code)
    assert len(violations) == 1
    assert violations[0].issue_type == "SUSPICIOUS_HARDCODED_RETURN"