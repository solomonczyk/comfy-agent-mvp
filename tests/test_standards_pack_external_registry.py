"""Tests for standards pack external registry.

RC-COMBINE-V2-MACHINE-READABLE-STANDARDS-PACK-001
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest


def get_standards_pack_dir() -> Path:
    """Return the standards pack directory for testing."""
    return Path("data/rc2_multishot1_ep01/output/control/standards_pack")


class TestExternalStandardsSources:
    """Test external standards sources registry."""

    def test_external_standards_sources_is_valid_json(self):
        """external_standards_sources.json must be valid JSON."""
        path = get_standards_pack_dir() / "external_registry" / "external_standards_sources.json"
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert isinstance(data, dict)

    def test_registry_has_sources_array(self):
        """Registry must have sources array."""
        path = get_standards_pack_dir() / "external_registry" / "external_standards_sources.json"
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert "sources" in data
        assert isinstance(data["sources"], list)

    def test_owasp_asvs_registered(self):
        """OWASP ASVS must be registered."""
        path = get_standards_pack_dir() / "external_registry" / "external_standards_sources.json"
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        sources = data.get("sources", [])
        owasp = [s for s in sources if s.get("standard_id") == "owasp_asvs"]
        assert len(owasp) == 1, "OWASP ASVS not found in registry"

    def test_mitre_cwe_registered(self):
        """MITRE CWE must be registered."""
        path = get_standards_pack_dir() / "external_registry" / "external_standards_sources.json"
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        sources = data.get("sources", [])
        cwe = [s for s in sources if s.get("standard_id") == "mitre_cwe"]
        assert len(cwe) == 1, "MITRE CWE not found in registry"

    def test_mitre_capec_registered(self):
        """MITRE CAPEC must be registered."""
        path = get_standards_pack_dir() / "external_registry" / "external_standards_sources.json"
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        sources = data.get("sources", [])
        capec = [s for s in sources if s.get("standard_id") == "mitre_capec"]
        assert len(capec) == 1, "MITRE CAPEC not found in registry"

    def test_nist_oscal_registered(self):
        """NIST OSCAL must be registered."""
        path = get_standards_pack_dir() / "external_registry" / "external_standards_sources.json"
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        sources = data.get("sources", [])
        oscal = [s for s in sources if s.get("standard_id") == "nist_oscal"]
        assert len(oscal) == 1, "NIST OSCAL not found in registry"

    def test_cyclonedx_registered(self):
        """CycloneDX must be registered."""
        path = get_standards_pack_dir() / "external_registry" / "external_standards_sources.json"
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        sources = data.get("sources", [])
        cdx = [s for s in sources if s.get("standard_id") == "cyclonedx"]
        assert len(cdx) == 1, "CycloneDX not found in registry"

    def test_spdx_registered(self):
        """SPDX must be registered."""
        path = get_standards_pack_dir() / "external_registry" / "external_standards_sources.json"
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        sources = data.get("sources", [])
        spdx = [s for s in sources if s.get("standard_id") == "spdx"]
        assert len(spdx) == 1, "SPDX not found in registry"

    def test_openssf_scorecard_registered(self):
        """OpenSSF Scorecard must be registered."""
        path = get_standards_pack_dir() / "external_registry" / "external_standards_sources.json"
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        sources = data.get("sources", [])
        scorecard = [s for s in sources if s.get("standard_id") == "openssf_scorecard"]
        assert len(scorecard) == 1, "OpenSSF Scorecard not found in registry"


class TestExternalStandardsNotDownloaded:
    """Test that external standards are not downloaded."""

    def test_no_download_performed_for_any_standard(self):
        """All external standards must have download_performed=false."""
        path = get_standards_pack_dir() / "external_registry" / "external_standards_sources.json"
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        sources = data.get("sources", [])
        for source in sources:
            assert source.get("download_performed") is False, \
                f"{source.get('standard_id')} has download_performed=true"

    def test_no_local_copy_available(self):
        """All external standards must have local_copy_available=false."""
        path = get_standards_pack_dir() / "external_registry" / "external_standards_sources.json"
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        sources = data.get("sources", [])
        for source in sources:
            assert source.get("local_copy_available") is False, \
                f"{source.get('standard_id')} has local_copy_available=true"

    def test_status_is_pending_controlled_acquisition(self):
        """All standards should indicate pending controlled acquisition."""
        path = get_standards_pack_dir() / "external_registry" / "external_standards_sources.json"
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        sources = data.get("sources", [])
        for source in sources:
            status = source.get("status", "").lower()
            assert "pending" in status or "controlled" in status or "future" in status, \
                f"{source.get('standard_id')} status does not indicate pending acquisition"


class TestExternalStandardsAcquisitionPlan:
    """Test external standards acquisition plan."""

    def test_acquisition_plan_exists(self):
        """external_standards_acquisition_plan.json must exist."""
        path = get_standards_pack_dir() / "external_registry" / "external_standards_acquisition_plan.json"
        assert path.exists()

    def test_acquisition_plan_is_valid_json(self):
        """Acquisition plan must be valid JSON."""
        path = get_standards_pack_dir() / "external_registry" / "external_standards_acquisition_plan.json"
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert isinstance(data, dict)


class TestExternalStandardsAcquisitionStatus:
    """Test external standards acquisition status."""

    def test_acquisition_status_exists(self):
        """external_standards_acquisition_status.json must exist."""
        path = get_standards_pack_dir() / "external_registry" / "external_standards_acquisition_status.json"
        assert path.exists()

    def test_acquisition_status_is_valid_json(self):
        """Acquisition status must be valid JSON."""
        path = get_standards_pack_dir() / "external_registry" / "external_standards_acquisition_status.json"
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert isinstance(data, dict)
