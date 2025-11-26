"""Validation script for TASK_001 Database Foundation.

Runs all quality checks:
- Black formatting
- Flake8 linting
- Mypy type checking
- Pytest with coverage

Usage:
    python validate.py
"""

import subprocess
import sys


def run_command(name: str, command: list[str]) -> bool:
    """Run a validation command and report results."""
    print(f"\n{'=' * 60}")
    print(f"Running {name}...")
    print(f"{'=' * 60}\n")

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
        )

        print(result.stdout)
        if result.stderr:
            print(result.stderr)

        if result.returncode == 0:
            print(f"\n✓ {name} PASSED\n")
            return True
        else:
            print(f"\n✗ {name} FAILED\n")
            return False

    except FileNotFoundError:
        print(f"\n✗ {name} FAILED - Command not found\n")
        return False
    except Exception as e:
        print(f"\n✗ {name} FAILED - {e}\n")
        return False


def main() -> int:
    """Run all validation checks."""
    print("\n" + "=" * 60)
    print("TASK_001 Database Foundation - Validation")
    print("=" * 60)

    results = {}

    # 1. Black formatting check
    results["Black"] = run_command(
        "Black Formatting",
        ["black", "app/", "--check", "--diff"],
    )

    # 2. Flake8 linting
    results["Flake8"] = run_command(
        "Flake8 Linting",
        ["flake8", "app/"],
    )

    # 3. Mypy type checking
    results["Mypy"] = run_command(
        "Mypy Type Checking",
        ["mypy", "app/"],
    )

    # 4. Pytest with coverage
    results["Pytest"] = run_command(
        "Pytest with Coverage",
        [
            "pytest",
            "-v",
            "--cov=app",
            "--cov-report=term-missing",
            "--cov-report=html",
        ],
    )

    # Summary
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60 + "\n")

    passed = sum(1 for result in results.values() if result)
    total = len(results)

    for name, result in results.items():
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{name:<20} {status}")

    print(f"\nTotal: {passed}/{total} checks passed")

    if passed == total:
        print("\n🎉 ALL VALIDATION CHECKS PASSED! 🎉\n")
        print("TASK_001 Database Foundation is ready for deployment.\n")
        return 0
    else:
        print("\n❌ SOME VALIDATION CHECKS FAILED ❌\n")
        print("Please fix the issues above before proceeding.\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
