"""Tests for machine-verifiable CF-X1 project provenance."""

from __future__ import annotations

import json
from pathlib import Path

from cfx1.provenance import PROVENANCE_PATH, evaluate_project_provenance


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def _manifest() -> dict[str, object]:
    return {
        "schema_version": 1,
        "project": {
            "repository_name": "CF-X1-Contested-Logistics-Resource-Node",
            "product_name": "CF-X1 Contested Logistics Resource Node",
            "platform_family": "IX ContinuumFoundry",
        },
        "ownership": {
            "copyright_holder": "Bryce Lovell",
            "copyright_year": 2026,
            "license_file": "LICENSE",
            "license_identifier": "LicenseRef-CF-X1-Evaluation-Only-1.0",
        },
        "implementation": {
            "origin": "standalone",
            "source_of_truth": "this-repository",
            "donor_repository_dependency": False,
            "generated_from_donor_source": False,
            "third_party_materials_present": False,
            "third_party_material_policy": "segregate-and-document",
        },
    }


def _write_repository(
    root: Path,
    manifest: dict[str, object],
) -> None:
    manifest_path = root / PROVENANCE_PATH
    manifest_path.parent.mkdir(parents=True)

    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    (root / "LICENSE").write_text(
        "Copyright © 2026 Bryce Lovell. All rights reserved.\n",
        encoding="utf-8",
    )


def test_repository_manifest_matches_canonical_identity() -> None:
    """The committed provenance manifest must match canonical project state."""
    result = evaluate_project_provenance(REPOSITORY_ROOT)

    assert result.is_valid
    assert result.provenance is not None
    assert result.provenance.repository_name == (
        "CF-X1-Contested-Logistics-Resource-Node"
    )
    assert not result.provenance.donor_repository_dependency
    assert not result.provenance.generated_from_donor_source


def test_missing_manifest_is_rejected(tmp_path: Path) -> None:
    """Provenance is mandatory and cannot be inferred from repository naming."""
    (tmp_path / "LICENSE").write_text(
        "Copyright © 2026 Bryce Lovell. All rights reserved.\n",
        encoding="utf-8",
    )

    result = evaluate_project_provenance(tmp_path)

    assert not result.is_valid
    assert result.provenance is None
    assert result.issues[0].code == "provenance-manifest-missing"


def test_identity_drift_is_rejected(tmp_path: Path) -> None:
    """The provenance manifest cannot rename the canonical repository."""
    manifest = _manifest()
    project = manifest["project"]

    assert isinstance(project, dict)

    project["repository_name"] = "Different-Repository"
    _write_repository(tmp_path, manifest)

    result = evaluate_project_provenance(tmp_path)

    assert any(
        issue.code == "identity-mismatch"
        for issue in result.issues
    )


def test_donor_dependency_is_rejected(tmp_path: Path) -> None:
    """CF-X1 must remain a standalone implementation without donor dependency."""
    manifest = _manifest()
    implementation = manifest["implementation"]

    assert isinstance(implementation, dict)

    implementation["donor_repository_dependency"] = True
    _write_repository(tmp_path, manifest)

    result = evaluate_project_provenance(tmp_path)

    assert any(
        issue.code == "donor-dependency-prohibited"
        for issue in result.issues
    )


def test_third_party_notice_must_match_declaration(
    tmp_path: Path,
) -> None:
    """Third-party material cannot appear without an explicit declaration."""
    manifest = _manifest()
    _write_repository(tmp_path, manifest)

    (tmp_path / "THIRD_PARTY_NOTICES.md").write_text(
        "Documented third-party material.\n",
        encoding="utf-8",
    )

    result = evaluate_project_provenance(tmp_path)

    assert any(
        issue.code == "third-party-declaration-mismatch"
        for issue in result.issues
    )


def test_malformed_manifest_is_rejected(tmp_path: Path) -> None:
    """Invalid JSON must fail as a provenance error rather than crash the gate."""
    manifest_path = tmp_path / PROVENANCE_PATH
    manifest_path.parent.mkdir(parents=True)

    manifest_path.write_text(
        "{invalid-json\n",
        encoding="utf-8",
    )

    (tmp_path / "LICENSE").write_text(
        "Copyright © 2026 Bryce Lovell. All rights reserved.\n",
        encoding="utf-8",
    )

    result = evaluate_project_provenance(tmp_path)

    assert not result.is_valid
    assert result.provenance is None
    assert result.issues[0].code == "provenance-manifest-invalid"
