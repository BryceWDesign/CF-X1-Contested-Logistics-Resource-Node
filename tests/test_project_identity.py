"""Tests for canonical CF-X1 project identity."""

import pytest

from cfx1 import PROJECT_IDENTITY, ProjectIdentity


def test_project_identity_matches_locked_program() -> None:
    """The importable identity must preserve the locked program definition."""
    assert PROJECT_IDENTITY.repository_name == "CF-X1-Contested-Logistics-Resource-Node"
    assert PROJECT_IDENTITY.product_name == "CF-X1 Contested Logistics Resource Node"
    assert PROJECT_IDENTITY.platform_family == "IX ContinuumFoundry"
    assert PROJECT_IDENTITY.total_commits == 480
    assert PROJECT_IDENTITY.final_readme_commit == 480
    assert "mission-critical power" in PROJECT_IDENTITY.description
    assert "degraded, disrupted, or denied" in PROJECT_IDENTITY.description


def test_project_identity_rejects_empty_repository_name() -> None:
    """Repository identity cannot be created without a repository name."""
    with pytest.raises(ValueError, match="repository_name must not be empty"):
        ProjectIdentity(
            repository_name="",
            product_name="CF-X1",
            platform_family="IX ContinuumFoundry",
            description="Valid description.",
            total_commits=480,
            final_readme_commit=480,
        )


def test_project_identity_rejects_non_positive_commit_count() -> None:
    """The locked program must contain at least one commit."""
    with pytest.raises(ValueError, match="total_commits must be greater than zero"):
        ProjectIdentity(
            repository_name="CF-X1-Contested-Logistics-Resource-Node",
            product_name="CF-X1 Contested Logistics Resource Node",
            platform_family="IX ContinuumFoundry",
            description="Valid description.",
            total_commits=0,
            final_readme_commit=0,
        )


def test_project_identity_rejects_misaligned_readme_commit() -> None:
    """The README lock must remain aligned with the final program commit."""
    with pytest.raises(ValueError, match="final_readme_commit must equal total_commits"):
        ProjectIdentity(
            repository_name="CF-X1-Contested-Logistics-Resource-Node",
            product_name="CF-X1 Contested Logistics Resource Node",
            platform_family="IX ContinuumFoundry",
            description="Valid description.",
            total_commits=480,
            final_readme_commit=479,
        )
