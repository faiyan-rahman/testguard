# src/analyzer.py
import ast
from dataclasses import dataclass
from typing import List


@dataclass
class Violation:
    target_name: str
    line: int
    issue_type: str
    description: str


class TestASTVisitor(ast.NodeVisitor):
    """Scans test_* functions for reward-hacking patterns."""

    def __init__(self) -> None:
        self.violations: List[Violation] = []

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        if not node.name.startswith("test_"):
            return

        # 1. Check for skip/xfail decorators
        for decorator in node.decorator_list:
            dec_str = ast.unparse(decorator)
            if "skip" in dec_str or "xfail" in dec_str:
                self.violations.append(
                    Violation(
                        target_name=node.name,
                        line=node.lineno,
                        issue_type="SKIPPED_TEST",
                        description=f"Test muted via decorator '@{dec_str}'.",
                    )
                )

        # 2. Check for missing assertions
        assert_nodes = [n for n in ast.walk(node) if isinstance(n, ast.Assert)]
        if not assert_nodes:
            self.violations.append(
                Violation(
                    target_name=node.name,
                    line=node.lineno,
                    issue_type="MISSING_ASSERTION",
                    description="Test contains no assert statements (silent pass).",
                )
            )

        # 3. Check for tautological assertions (e.g. 'assert True')
        for assert_node in assert_nodes:
            if isinstance(assert_node.test, ast.Constant) and bool(assert_node.test.value) is True:
                self.violations.append(
                    Violation(
                        target_name=node.name,
                        line=assert_node.lineno,
                        issue_type="TAUTOLOGICAL_ASSERT",
                        description=f"Trivial assertion 'assert {ast.unparse(assert_node.test)}' always passes.",
                    )
                )

        self.generic_visit(node)


class ProductionASTVisitor(ast.NodeVisitor):
    """Scans production functions for suspicious hardcoded test-case returns."""

    def __init__(self) -> None:
        self.violations: List[Violation] = []

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        if node.name.startswith("test_"):
            return

        for child in ast.walk(node):
            if isinstance(child, ast.If):
                # Check if condition compares a variable against a literal constant (e.g. if x == 42:)
                if isinstance(child.test, ast.Compare) and any(
                    isinstance(op, ast.Eq) for op in child.test.ops
                ):
                    has_literal_cmp = any(
                        isinstance(comp, ast.Constant)
                        and not isinstance(comp.value, (bool, type(None)))
                        for comp in child.test.comparators
                    )
                    # Check if the body immediately returns a constant literal
                    if has_literal_cmp and len(child.body) == 1 and isinstance(child.body[0], ast.Return):
                        ret_node = child.body[0]
                        if isinstance(ret_node.value, ast.Constant) and not isinstance(
                            ret_node.value.value, (bool, type(None))
                        ):
                            self.violations.append(
                                Violation(
                                    target_name=node.name,
                                    line=child.lineno,
                                    issue_type="SUSPICIOUS_HARDCODED_RETURN",
                                    description=(
                                        f"Suspicious hardcoded branch 'if {ast.unparse(child.test)}: "
                                        f"return {ast.unparse(ret_node.value)}' (potential test overfitting)."
                                    ),
                                )
                            )

        self.generic_visit(node)


def analyze_test_code(source_code: str) -> List[Violation]:
    tree = ast.parse(source_code)
    visitor = TestASTVisitor()
    visitor.visit(tree)
    return visitor.violations


def analyze_production_code(source_code: str) -> List[Violation]:
    tree = ast.parse(source_code)
    visitor = ProductionASTVisitor()
    visitor.visit(tree)
    return visitor.violations


def compare_test_versions(old_code: str, new_code: str) -> List[str]:
    old_tree = ast.parse(old_code)
    new_tree = ast.parse(new_code)

    old_asserts = sum(1 for n in ast.walk(old_tree) if isinstance(n, ast.Assert))
    new_asserts = sum(1 for n in ast.walk(new_tree) if isinstance(n, ast.Assert))

    alerts: List[str] = []
    if new_asserts < old_asserts:
        alerts.append(
            f"REGRESSION: Assertion count dropped from {old_asserts} to {new_asserts}."
        )
    return alerts