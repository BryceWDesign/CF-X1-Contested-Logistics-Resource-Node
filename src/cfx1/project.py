"""Canonical project identity and repository-level invariants."""

from dataclasses import dataclass
from typing import Final


@dataclass(frozen=True, slots=True)
class ProjectIdentity:
    """Immutable public identity for the CF-X1 program."""

    repository_name: str
    product_name: str
    platform_family: str
    description: str
    total_commits: int
    final_readme_commit: int

    def __post_init__(self) -> None:
        """Reject internally inconsistent project metadata."""
        if not self.repository_name:
            raise ValueError("repository_name must not be empty")
        if not self.product_name:
            raise ValueError("product_name must not be empty")
        if not self.platform_family:
            raise ValueError("platform_family must not be empty")
        if not self.description:
            raise ValueError("description must not be empty")
        if self.total_commits <= 0:
            raise ValueError("total_commits must be greater than zero")
        if self.final_readme_commit != self.total_commits:
            raise ValueError("final_readme_commit must equal total_commits")


PROJECT_IDENTITY: Final[ProjectIdentity] = ProjectIdentity(
    repository_name="CF-X1-Contested-Logistics-Resource-Node",
    product_name="CF-X1 Contested Logistics Resource Node",
    platform_family="IX ContinuumFoundry",
    description=(
        "A distributed, battery-free, supercapacitor-buffered sustainment system that "
        "produces mission-critical power, purified water, cooling, hydrogen, and oxygen "
        "at the point of need when conventional logistics are degraded, disrupted, or denied."
    ),
    total_commits=480,
    final_readme_commit=480,
)
