"""Fail when CF-X1 provenance does not match the repository state."""

from __future__ import annotations

from pathlib import Path
from typing import Final

from cfx1.provenance import evaluate_project_provenance


REPOSITORY_ROOT: Final[Path] = Path(__file__).resolve().parents[1]


def main() -> int:
    """Evaluate project provenance and return a process-compatible status code."""
    result = evaluate_project_provenance(REPOSITORY_ROOT)

    if result.is_valid:
        print("[CF-X1] project provenance passed", flush=True)
        return 0

    print("[CF-X1] project provenance failed", flush=True)

    for issue in result.issues:
        print(
            f"- {issue.code}: {issue.path}: {issue.detail}",
            flush=True,
        )

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
