"""Run the complete local quality gate in the same order as continuous integration."""

from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Final


REPOSITORY_ROOT: Final[Path] = Path(__file__).resolve().parents[1]


@dataclass(frozen=True, slots=True)
class Check:
    """One deterministic repository quality check."""

    name: str
    command: tuple[str, ...]


CHECKS: Final[tuple[Check, ...]] = (
    Check(
        "repository-policy",
        (
            sys.executable,
            "scripts/check_repository_policy.py",
        ),
    ),
    Check(
        "project-provenance",
        (
            sys.executable,
            "scripts/check_provenance.py",
        ),
    ),
    Check(
        "ruff-format",
        (
            sys.executable,
            "-m",
            "ruff",
            "format",
            "--check",
            ".",
        ),
    ),
    Check(
        "ruff-lint",
        (
            sys.executable,
            "-m",
            "ruff",
            "check",
            ".",
        ),
    ),
    Check(
        "mypy",
        (
            sys.executable,
            "-m",
            "mypy",
            "src",
            "tests",
            "scripts",
        ),
    ),
    Check(
        "pytest",
        (
            sys.executable,
            "-m",
            "pytest",
        ),
    ),
)


def run_check(check: Check) -> None:
    """Run one check and stop immediately when it fails."""
    print(
        f"[CF-X1] running {check.name}: {' '.join(check.command)}",
        flush=True,
    )

    subprocess.run(
        check.command,
        cwd=REPOSITORY_ROOT,
        check=True,
    )


def main() -> int:
    """Execute all repository checks and return a process-compatible status code."""
    try:
        for check in CHECKS:
            run_check(check)
    except subprocess.CalledProcessError as error:
        print(
            f"[CF-X1] quality gate failed with exit code {error.returncode}",
            flush=True,
        )
        return error.returncode

    print("[CF-X1] all quality gates passed", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
