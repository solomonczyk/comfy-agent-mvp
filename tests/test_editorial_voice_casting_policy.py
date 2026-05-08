"""Tests for editorial voice casting policy."""
import pytest
from app.editorial.voice_casting_policy import VoiceCastingContract


class TestVoiceCastingContractCreatedWithoutGeneration:
    def test_default_contract_has_no_generation(self):
        contract = VoiceCastingContract()
        assert contract.full_voiceover_generation_allowed is False
        assert contract.sample_required is True
        assert contract.operator_review_required is True

    def test_contract_validation_passes(self):
        contract = VoiceCastingContract()
        errs = contract.validate()
        assert errs == []

    def test_generation_allowed_rejected(self):
        contract = VoiceCastingContract(full_voiceover_generation_allowed=True)
        errs = contract.validate()
        assert any("full_voiceover_generation_allowed must be False" in e for e in errs)

    def test_empty_language(self):
        contract = VoiceCastingContract(language="")
        errs = contract.validate()
        assert any("language must be non-empty" in e for e in errs)

    def test_empty_tone(self):
        contract = VoiceCastingContract(tone=[])
        errs = contract.validate()
        assert any("tone must have at least one entry" in e for e in errs)

    def test_to_dict(self):
        contract = VoiceCastingContract()
        data = contract.to_dict()
        assert data["language"] == "ru"
        assert data["preferred_gender"] == "female"
        assert data["full_voiceover_generation_allowed"] is False

    def test_default_values(self):
        contract = VoiceCastingContract()
        assert contract.language == "ru"
        assert contract.preferred_gender == "female"
        assert contract.age_range == "30-45"
        assert contract.pace == "medium"
        assert contract.emotion == "confident_warm"
        assert "robotic" in contract.avoid
        assert "aggressive_sales_tone" in contract.avoid
