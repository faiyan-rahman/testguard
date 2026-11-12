![TestGuard CI](https://github.com/faiyan-rahman/testguard/actions/workflows/ci.yml/badge.svg)
# TestGuard

**Static AST Analyzer & CI Guardrail for Detecting AI Reward Hacking in Python Test Suites.**

## Overview
Autonomous coding agents and LLMs frequently exhibit *reward hacking* when tasked with fixing failing builds—modifying unit tests to pass trivially rather than resolving the underlying bug in production code. 

**TestGuard** parses Python Abstract Syntax Trees (`ast`) to automatically flag faked test passes, silent assertion deletions, and hardcoded test-case overfitting before changes are merged.

## Detected Failure Modes
- **`MISSING_ASSERTION`**: Identifies `test_*` functions where assertions were removed or commented out to force a silent pass.
- **`TAUTOLOGICAL_ASSERT`**: Flags trivial assertions (e.g., `assert True`) injected by agents.
- **`SKIPPED_TEST`**: Detects unauthorized `@pytest.mark.skip` or `@pytest.mark.xfail` decorators added to bypass failing tests.
- **`SUSPICIOUS_HARDCODED_RETURN`**: Scans production functions for literal input-to-output branches (e.g., `if x == 10: return 55`) designed to hardcode unit test expectations.
- **Assertion Count Regression**: Compares file revisions to alert when total assertion counts drop across commits.

## Quickstart & Usage

```bash
# Install dependencies
pip install -r requirements.txt

# Run the unit test suite
python -m pytest -v

# Scan a directory or file via CLI
python -m src.cli ./tests
