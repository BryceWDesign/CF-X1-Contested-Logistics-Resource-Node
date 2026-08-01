"""Tests for enforceable repository-integrity policy."""

from pathlib import Path

from cfx1.repository_policy import evaluate_repository


LICENSE_CONTENT = """\
CF-X1 EVALUATION-ONLY SOURCE AND HARDWARE DESIGN LICENSE
Commercial Use
Operational Deployment
END OF LICENSE
"""


def _write_compliant_repository(root: Path) -> None:
    (root / "LICENSE").write_text(
        LICENSE_CONTENT,
        encoding="utf-8",
    )
    (root / "pyproject.toml").write_text(
        "[project]\nname = 'example'\n",
        encoding="utf-8",
    )

    source_directory = root / "src" / "example"
    source_directory.mkdir(parents=True)
    (source_directory / "module.py").write_text(
        "VALUE = 1\n",
        encoding="utf-8",
    )


def test_compliant_repository_passes(tmp_path: Path) -> None:
    """A complete repository without unfinished-work markers must pass."""
    _write_compliant_repository(tmp_path)

    result = evaluate_repository(tmp_path)

    assert result.is_compliant
    assert result.issues == ()


def test_missing_license_fails(tmp_path: Path) -> None:
    """The root evaluation-only license is mandatory."""
    (tmp_path / "pyproject.toml").write_text(
        "[project]\nname = 'example'\n",
        encoding="utf-8",
    )

    result = evaluate_repository(tmp_path)

    assert not result.is_compliant
    assert any(
        issue.code == "required-root-file-missing"
        for issue in result.issues
    )


def test_missing_license_marker_fails(tmp_path: Path) -> None:
    """The root license must retain its defining protection markers."""
    _write_compliant_repository(tmp_path)
    (tmp_path / "LICENSE").write_text(
        "Incomplete license text.\n",
        encoding="utf-8",
    )

    result = evaluate_repository(tmp_path)

    assert any(
        issue.code == "license-marker-missing"
        for issue in result.issues
    )


def test_readme_is_locked_until_final_commit(tmp_path: Path) -> None:
    """A root README must not appear before overall commit 480."""
    _write_compliant_repository(tmp_path)
    (tmp_path / "README.md").write_text(
        "Premature release documentation.\n",
        encoding="utf-8",
    )

    result = evaluate_repository(tmp_path)

    assert any(
        issue.code == "readme-locked-until-final-commit"
        for issue in result.issues
    )


def test_unfinished_work_directive_fails(tmp_path: Path) -> None:
    """Committed source must not carry unfinished-work directives."""
    _write_compliant_repository(tmp_path)

    marker = "".join(
        chr(code)
        for code in (84, 79, 68, 79)
    )
    source_path = tmp_path / "src" / "example" / "module.py"
    source_path.write_text(
        f"# {marker}: replace later\n",
        encoding="utf-8",
    )

    result = evaluate_repository(tmp_path)

    assert any(
        issue.code == "placeholder-directive-detected"
        for issue in result.issues
    )


def test_not_implemented_sentinel_fails(tmp_path: Path) -> None:
    """Committed implementations must not defer behavior through sentinels."""
    _write_compliant_repository(tmp_path)

    sentinel = "".join(("NotImplemented", "Error"))
    source_path = tmp_path / "src" / "example" / "module.py"
    source_path.write_text(
        f"raise {sentinel}\n",
        encoding="utf-8",
    )

    result = evaluate_repository(tmp_path)

    assert any(
        issue.code == "not-implemented-sentinel-detected"
        for issue in result.issues
    )


def test_bare_pass_statement_fails(tmp_path: Path) -> None:
    """Empty committed implementations must be rejected."""
    _write_compliant_repository(tmp_path)

    source_path = tmp_path / "src" / "example" / "module.py"
    source_path.write_text(
        "def empty() -> None:\n    pass\n",
        encoding="utf-8",
    )

    result = evaluate_repository(tmp_path)

    assert any(
        issue.code == "bare-pass-detected"
        for issue in result.issues
    )


def test_generated_directories_are_ignored(tmp_path: Path) -> None:
    """Generated caches must not create false repository-policy failures."""
    _write_compliant_repository(tmp_path)

    marker = "".join(
        chr(code)
        for code in (84, 79, 68, 79)
    )
    cache_directory = tmp_path / ".pytest_cache"
    cache_directory.mkdir()
    (cache_directory / "generated.txt").write_text(
        marker,
        encoding="utf-8",
    )

    result = evaluate_repository(tmp_path)

    assert result.is_compliant
