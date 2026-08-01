"""Fail when the repository violates an active CF-X1 integrity rule."""

from __future__ import annotations

from pathlib import Path
from typing import Final

from cfx1.repository_policy import evaluate_repository


REPOSITORY_ROOT: Final[Path] = Path(__file__).resolve().parents[1]


def main() -> int:
    """Evaluate repository policy and return a process-compatible status code."""
    result = evaluate_repository(REPOSITORY_ROOT)
    if result.is_compliant:
        print("[CF-X1] repository policy passed", flush=True)
        return 0

    print("[CF-X1] repository policy failed", flush=True)
    for issue in result.issues:
        print(
            f"- {issue.code}: {issue.path}: {issue.detail}",
            flush=True,
        )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
