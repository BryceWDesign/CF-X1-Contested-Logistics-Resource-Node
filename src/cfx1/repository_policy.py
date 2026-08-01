"""Repository-integrity rules enforced by the CF-X1 quality gate."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Final


REQUIRED_ROOT_FILES: Final[tuple[str, ...]] = ("LICENSE", "pyproject.toml")
REQUIRED_LICENSE_MARKERS: Final[tuple[str, ...]] = (
    "CF-X1 EVALUATION-ONLY SOURCE AND HARDWARE DESIGN LICENSE",
    "Commercial Use",
    "Operational Deployment",
    "END OF LICENSE",
)
FORBIDDEN_ROOT_README_NAMES: Final[frozenset[str]] = frozenset(
    {"readme", "readme.md", "readme.rst", "readme.txt"}
)
SCANNED_SUFFIXES: Final[frozenset[str]] = frozenset(
    {".json", ".md", ".py", ".toml", ".txt", ".yaml", ".yml"}
)
IGNORED_DIRECTORY_NAMES: Final[frozenset[str]] = frozenset(
    {
        ".git",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".venv",
        "__pycache__",
        "artifacts",
        "build",
        "dist",
        "runs",
        "venv",
    }
)

_DIRECTIVE_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"(?im)^\s*(?:(?:#|//|/\*|\*|<!--)\s*)?(?:TODO|FIXME|TBD|PLACEHOLDER)\b"
)
_NOT_IMPLEMENTED_SENTINEL_NAME: Final[str] = "".join(("NotImplemented", "Error"))
_NOT_IMPLEMENTED_PATTERN: Final[re.Pattern[str]] = re.compile(
    _NOT_IMPLEMENTED_SENTINEL_NAME
)
_BARE_PASS_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"(?m)^\s*pass\s*(?:#.*)?$"
)


@dataclass(frozen=True, slots=True, order=True)
class RepositoryPolicyIssue:
    """One deterministic repository-policy violation."""

    code: str
    path: str
    detail: str


@dataclass(frozen=True, slots=True)
class RepositoryPolicyResult:
    """Complete repository-policy evaluation result."""

    issues: tuple[RepositoryPolicyIssue, ...]

    @property
    def is_compliant(self) -> bool:
        """Return whether the repository satisfies every active policy rule."""
        return not self.issues


def _is_ignored(path: Path, root: Path) -> bool:
    relative_parts = path.relative_to(root).parts
    return any(part in IGNORED_DIRECTORY_NAMES for part in relative_parts)


def _iter_scanned_files(root: Path) -> tuple[Path, ...]:
    files = (
        path
        for path in root.rglob("*")
        if path.is_file()
        and path.suffix.casefold() in SCANNED_SUFFIXES
        and not _is_ignored(path, root)
    )
    return tuple(sorted(files, key=lambda path: path.as_posix().casefold()))


def _relative_path(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def _check_required_root_files(root: Path) -> list[RepositoryPolicyIssue]:
    issues: list[RepositoryPolicyIssue] = []
    for filename in REQUIRED_ROOT_FILES:
        if not (root / filename).is_file():
            issues.append(
                RepositoryPolicyIssue(
                    code="required-root-file-missing",
                    path=filename,
                    detail=f"required root file is missing: {filename}",
                )
            )
    return issues


def _check_license(root: Path) -> list[RepositoryPolicyIssue]:
    license_path = root / "LICENSE"
    if not license_path.is_file():
        return []

    content = license_path.read_text(encoding="utf-8")
    return [
        RepositoryPolicyIssue(
            code="license-marker-missing",
            path="LICENSE",
            detail=f"required license marker is missing: {marker}",
        )
        for marker in REQUIRED_LICENSE_MARKERS
        if marker not in content
    ]


def _check_readme_lock(root: Path) -> list[RepositoryPolicyIssue]:
    return [
        RepositoryPolicyIssue(
            code="readme-locked-until-final-commit",
            path=path.name,
            detail="the README is locked until overall commit 480",
        )
        for path in sorted(root.iterdir(), key=lambda item: item.name.casefold())
        if path.is_file() and path.name.casefold() in FORBIDDEN_ROOT_README_NAMES
    ]


def _check_file_content(
    path: Path,
    root: Path,
) -> list[RepositoryPolicyIssue]:
    try:
        content = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return [
            RepositoryPolicyIssue(
                code="text-file-not-utf8",
                path=_relative_path(path, root),
                detail="repository-owned text files must use UTF-8 encoding",
            )
        ]

    checks: tuple[tuple[str, str, re.Pattern[str]], ...] = (
        (
            "placeholder-directive-detected",
            "placeholder or unfinished-work directive detected",
            _DIRECTIVE_PATTERN,
        ),
        (
            "not-implemented-sentinel-detected",
            (
                f"{_NOT_IMPLEMENTED_SENTINEL_NAME} is not permitted "
                "in committed implementation code"
            ),
            _NOT_IMPLEMENTED_PATTERN,
        ),
        (
            "bare-pass-detected",
            "a bare pass statement is not permitted as committed implementation",
            _BARE_PASS_PATTERN,
        ),
    )
    relative_path = _relative_path(path, root)
    return [
        RepositoryPolicyIssue(
            code=code,
            path=relative_path,
            detail=detail,
        )
        for code, detail, pattern in checks
        if pattern.search(content)
    ]


def evaluate_repository(root: Path) -> RepositoryPolicyResult:
    """Evaluate the active repository-integrity rules for ``root``."""
    resolved_root = root.resolve()
    if not resolved_root.is_dir():
        raise ValueError(
            f"repository root does not exist: {resolved_root}"
        )

    issues = [
        *_check_required_root_files(resolved_root),
        *_check_license(resolved_root),
        *_check_readme_lock(resolved_root),
    ]
    for path in _iter_scanned_files(resolved_root):
        issues.extend(_check_file_content(path, resolved_root))

    return RepositoryPolicyResult(
        issues=tuple(sorted(set(issues)))
    )
