"""Machine-verifiable provenance for the standalone CF-X1 implementation."""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import StrEnum
from json import JSONDecodeError
from pathlib import Path
from typing import Final, TypeVar, cast

from cfx1.project import PROJECT_IDENTITY, ProjectIdentity


PROVENANCE_PATH: Final[Path] = Path("provenance/project-provenance.json")
EXPECTED_LICENSE_IDENTIFIER: Final[str] = "LicenseRef-CF-X1-Evaluation-Only-1.0"
EXPECTED_COPYRIGHT_HOLDER: Final[str] = "Bryce Lovell"
EXPECTED_COPYRIGHT_YEAR: Final[int] = 2026
THIRD_PARTY_NOTICE_PATH: Final[Path] = Path("THIRD_PARTY_NOTICES.md")
EnumType = TypeVar("EnumType", bound=StrEnum)


class ImplementationOrigin(StrEnum):
    """Permitted implementation-origin declarations."""

    STANDALONE = "standalone"


class SourceOfTruth(StrEnum):
    """Permitted source-of-truth declarations."""

    THIS_REPOSITORY = "this-repository"


class ThirdPartyMaterialPolicy(StrEnum):
    """Permitted handling policy for incorporated third-party materials."""

    SEGREGATE_AND_DOCUMENT = "segregate-and-document"


class ProvenanceFormatError(ValueError):
    """Raised when the provenance manifest has an invalid structure or value."""


@dataclass(frozen=True, slots=True)
class ProjectProvenance:
    """Validated provenance data for the CF-X1 repository."""

    schema_version: int
    repository_name: str
    product_name: str
    platform_family: str
    copyright_holder: str
    copyright_year: int
    license_file: str
    license_identifier: str
    implementation_origin: ImplementationOrigin
    source_of_truth: SourceOfTruth
    donor_repository_dependency: bool
    generated_from_donor_source: bool
    third_party_materials_present: bool
    third_party_material_policy: ThirdPartyMaterialPolicy


@dataclass(frozen=True, slots=True, order=True)
class ProvenanceIssue:
    """One deterministic provenance violation."""

    code: str
    path: str
    detail: str


@dataclass(frozen=True, slots=True)
class ProvenanceResult:
    """Complete provenance evaluation result."""

    provenance: ProjectProvenance | None
    issues: tuple[ProvenanceIssue, ...]

    @property
    def is_valid(self) -> bool:
        """Return whether the manifest and repository agree completely."""
        return self.provenance is not None and not self.issues


def _require_mapping(value: object, field: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ProvenanceFormatError(f"{field} must be an object")
    return cast(dict[str, object], value)


def _require_string(mapping: dict[str, object], field: str) -> str:
    value = mapping.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ProvenanceFormatError(f"{field} must be a non-empty string")
    return value


def _require_integer(mapping: dict[str, object], field: str) -> int:
    value = mapping.get(field)
    if not isinstance(value, int) or isinstance(value, bool):
        raise ProvenanceFormatError(f"{field} must be an integer")
    return value


def _require_boolean(mapping: dict[str, object], field: str) -> bool:
    value = mapping.get(field)
    if not isinstance(value, bool):
        raise ProvenanceFormatError(f"{field} must be a boolean")
    return value


def _require_enum(
    mapping: dict[str, object],
    field: str,
    enum_type: type[EnumType],
) -> EnumType:
    value = _require_string(mapping, field)
    try:
        return enum_type(value)
    except ValueError as error:
        allowed = ", ".join(member.value for member in enum_type)
        raise ProvenanceFormatError(
            f"{field} must be one of: {allowed}"
        ) from error


def load_project_provenance(path: Path) -> ProjectProvenance:
    """Load and structurally validate a provenance manifest."""
    raw: object = json.loads(path.read_text(encoding="utf-8"))
    root = _require_mapping(raw, "manifest")
    project = _require_mapping(root.get("project"), "project")
    ownership = _require_mapping(root.get("ownership"), "ownership")
    implementation = _require_mapping(root.get("implementation"), "implementation")

    return ProjectProvenance(
        schema_version=_require_integer(root, "schema_version"),
        repository_name=_require_string(project, "repository_name"),
        product_name=_require_string(project, "product_name"),
        platform_family=_require_string(project, "platform_family"),
        copyright_holder=_require_string(ownership, "copyright_holder"),
        copyright_year=_require_integer(ownership, "copyright_year"),
        license_file=_require_string(ownership, "license_file"),
        license_identifier=_require_string(ownership, "license_identifier"),
        implementation_origin=_require_enum(
            implementation,
            "origin",
            ImplementationOrigin,
        ),
        source_of_truth=_require_enum(
            implementation,
            "source_of_truth",
            SourceOfTruth,
        ),
        donor_repository_dependency=_require_boolean(
            implementation,
            "donor_repository_dependency",
        ),
        generated_from_donor_source=_require_boolean(
            implementation,
            "generated_from_donor_source",
        ),
        third_party_materials_present=_require_boolean(
            implementation,
            "third_party_materials_present",
        ),
        third_party_material_policy=_require_enum(
            implementation,
            "third_party_material_policy",
            ThirdPartyMaterialPolicy,
        ),
    )


def _identity_issues(
    provenance: ProjectProvenance,
    identity: ProjectIdentity,
) -> list[ProvenanceIssue]:
    comparisons = (
        ("repository_name", provenance.repository_name, identity.repository_name),
        ("product_name", provenance.product_name, identity.product_name),
        ("platform_family", provenance.platform_family, identity.platform_family),
    )
    return [
        ProvenanceIssue(
            code="identity-mismatch",
            path=PROVENANCE_PATH.as_posix(),
            detail=f"{field} does not match the canonical project identity",
        )
        for field, actual, expected in comparisons
        if actual != expected
    ]


def _ownership_issues(
    provenance: ProjectProvenance,
    root: Path,
) -> list[ProvenanceIssue]:
    issues: list[ProvenanceIssue] = []

    if provenance.copyright_holder != EXPECTED_COPYRIGHT_HOLDER:
        issues.append(
            ProvenanceIssue(
                code="copyright-holder-mismatch",
                path=PROVENANCE_PATH.as_posix(),
                detail="copyright_holder does not match the project owner",
            )
        )

    if provenance.copyright_year != EXPECTED_COPYRIGHT_YEAR:
        issues.append(
            ProvenanceIssue(
                code="copyright-year-mismatch",
                path=PROVENANCE_PATH.as_posix(),
                detail=f"copyright_year must be {EXPECTED_COPYRIGHT_YEAR}",
            )
        )

    if provenance.license_file != "LICENSE":
        issues.append(
            ProvenanceIssue(
                code="license-path-invalid",
                path=PROVENANCE_PATH.as_posix(),
                detail="license_file must identify the root LICENSE file",
            )
        )

    if provenance.license_identifier != EXPECTED_LICENSE_IDENTIFIER:
        issues.append(
            ProvenanceIssue(
                code="license-identifier-mismatch",
                path=PROVENANCE_PATH.as_posix(),
                detail="license_identifier does not match the CF-X1 license",
            )
        )

    license_path = root / "LICENSE"
    if not license_path.is_file():
        issues.append(
            ProvenanceIssue(
                code="license-file-missing",
                path=provenance.license_file,
                detail="the declared root license file does not exist",
            )
        )
        return issues

    license_content = license_path.read_text(encoding="utf-8")

    if provenance.copyright_holder not in license_content:
        issues.append(
            ProvenanceIssue(
                code="license-owner-mismatch",
                path=provenance.license_file,
                detail="the declared copyright holder is absent from LICENSE",
            )
        )

    if str(provenance.copyright_year) not in license_content:
        issues.append(
            ProvenanceIssue(
                code="license-year-mismatch",
                path=provenance.license_file,
                detail="the declared copyright year is absent from LICENSE",
            )
        )

    return issues


def _implementation_issues(
    provenance: ProjectProvenance,
    root: Path,
) -> list[ProvenanceIssue]:
    issues: list[ProvenanceIssue] = []

    if provenance.schema_version != 1:
        issues.append(
            ProvenanceIssue(
                code="unsupported-schema-version",
                path=PROVENANCE_PATH.as_posix(),
                detail="schema_version must be 1",
            )
        )

    if provenance.donor_repository_dependency:
        issues.append(
            ProvenanceIssue(
                code="donor-dependency-prohibited",
                path=PROVENANCE_PATH.as_posix(),
                detail="the completed CF-X1 implementation must remain standalone",
            )
        )

    if provenance.generated_from_donor_source:
        issues.append(
            ProvenanceIssue(
                code="donor-source-generation-prohibited",
                path=PROVENANCE_PATH.as_posix(),
                detail="CF-X1 source must not be generated from donor source code",
            )
        )

    notice_exists = (root / THIRD_PARTY_NOTICE_PATH).is_file()
    if provenance.third_party_materials_present != notice_exists:
        issues.append(
            ProvenanceIssue(
                code="third-party-declaration-mismatch",
                path=PROVENANCE_PATH.as_posix(),
                detail=(
                    "third_party_materials_present must match the presence of "
                    f"{THIRD_PARTY_NOTICE_PATH.as_posix()}"
                ),
            )
        )

    return issues


def evaluate_project_provenance(
    root: Path,
    identity: ProjectIdentity = PROJECT_IDENTITY,
) -> ProvenanceResult:
    """Validate the repository provenance manifest against canonical state."""
    resolved_root = root.resolve()
    manifest_path = resolved_root / PROVENANCE_PATH

    if not manifest_path.is_file():
        return ProvenanceResult(
            provenance=None,
            issues=(
                ProvenanceIssue(
                    code="provenance-manifest-missing",
                    path=PROVENANCE_PATH.as_posix(),
                    detail="the machine-verifiable provenance manifest is required",
                ),
            ),
        )

    try:
        provenance = load_project_provenance(manifest_path)
    except (OSError, UnicodeError, JSONDecodeError, ProvenanceFormatError) as error:
        return ProvenanceResult(
            provenance=None,
            issues=(
                ProvenanceIssue(
                    code="provenance-manifest-invalid",
                    path=PROVENANCE_PATH.as_posix(),
                    detail=str(error),
                ),
            ),
        )

    issues = [
        *_identity_issues(provenance, identity),
        *_ownership_issues(provenance, resolved_root),
        *_implementation_issues(provenance, resolved_root),
    ]

    return ProvenanceResult(
        provenance=provenance,
        issues=tuple(sorted(set(issues))),
    )
