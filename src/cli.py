# src/cli.py
import argparse
import sys
from pathlib import Path
from src.analyzer import analyze_production_code, analyze_test_code


def scan_path(target_path: Path) -> int:
    files = [target_path] if target_path.is_file() else list(target_path.rglob("*.py"))
    total_violations = 0

    for file_path in files:
        if "venv" in file_path.parts or ".git" in file_path.parts:
            continue

        source = file_path.read_text(encoding="utf-8")
        is_test_file = file_path.name.startswith("test_") or file_path.name.endswith("_test.py")

        violations = (
            analyze_test_code(source)
            if is_test_file
            else analyze_production_code(source)
        )

        for v in violations:
            total_violations += 1
            print(f"[FAIL] {file_path}:{v.line} ({v.target_name}) -> [{v.issue_type}] {v.description}")

    if total_violations == 0:
        print("[PASS] TestGuard: No reward-hacking patterns detected.")
        return 0

    print(f"\n[ALERT] TestGuard detected {total_violations} violation(s).")
    return 1


def main() -> None:
    parser = argparse.ArgumentParser(
        description="TestGuard: AST static analyzer to detect AI reward hacking and faked unit tests."
    )
    parser.add_argument("path", type=Path, help="Path to Python file or directory to scan")
    args = parser.parse_args()

    sys.exit(scan_path(args.path))


if __name__ == "__main__":
    main()