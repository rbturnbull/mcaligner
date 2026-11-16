from __future__ import annotations

import pytest
from pydantic import ValidationError

from mcaligner.settings import RoleSettings, Settings, parse_thinking


def test_tiers_and_overrides(tmp_path):
    settings = Settings()
    assert settings.model_for("aligner") == "anthropic:claude-opus-5-5"
    assert settings.model_for("scorer") == "anthropic:claude-sonnet-5-5"
    assert Settings(light_roles=["scorer"]).model_for("scorer") == "anthropic:claude-haiku-5-5"
    assert Settings(model="x", roles={"scorer": RoleSettings(model="y")}).model_for("aligner") == "x"
    assert Settings(model="x", roles={"scorer": RoleSettings(model="y")}).model_for("scorer") == "y"
    assert Settings(strong_thinking="low").thinking_for("aligner") == "low"
    assert Settings(roles={"aligner": RoleSettings(thinking=False)}, strong_thinking="low").thinking_for("aligner") is False
    assert settings.enabled("scorer") and settings.thinking_for("scorer") is None
    updated = settings.with_overrides(model="m", role_models={"scorer": "s", "aligner": None}, scorer=False, rounds=4, threshold=None)
    assert (updated.model, updated.rounds, updated.threshold) == ("m", 4, 0.8)
    assert updated.model_for("scorer") == "s" and not updated.enabled("scorer")
    assert settings.with_overrides().model_dump() == settings.model_dump()
    path = tmp_path / "s.yaml"
    path.write_text(updated.to_yaml(), encoding="utf-8")
    assert Settings.from_file(path) == updated
    path.write_text("", encoding="utf-8")
    assert Settings.from_file(path) == Settings()


def test_unknown_roles():
    with pytest.raises(ValidationError, match="Unknown roles"):
        Settings(roles={"upos": RoleSettings()})
    with pytest.raises(ValidationError, match="Unknown roles"):
        Settings(efficient_roles=["x"])


def test_parse_thinking():
    assert parse_thinking("off") is False and parse_thinking("On") is True and parse_thinking("high") == "high"
    with pytest.raises(ValueError, match="Thinking must be"):
        parse_thinking("lots")


def test_guidelines(tmp_path):
    default = Settings()
    assert default.guidelines == "grc-lat" and "Do **not align punctuation**" in default.guidelines_text
    assert Settings(guidelines="none").guidelines is None and Settings(guidelines=None).guidelines_text is None
    assert Settings(guidelines="").guidelines_text is None
    own = tmp_path / "mine.md"
    own.write_text("Align everything.\n", encoding="utf-8")
    assert Settings(guidelines=str(own)).guidelines_text == "Align everything."
    with pytest.raises(ValidationError, match="No guidelines 'nowhere'"):
        Settings(guidelines="nowhere")
    assert default.with_overrides(guidelines="none").guidelines is None
    assert default.with_overrides().guidelines == "grc-lat"


def test_link_punctuation_override():
    assert Settings().rules.link_punctuation is False
    assert Settings().with_overrides(link_punctuation=True).rules.link_punctuation is True
    assert Settings().with_overrides(link_punctuation=None).rules.link_punctuation is False


def test_columns_and_tools_settings():
    default = Settings()
    assert default.columns == ["lemma", "upos", "head", "deprel"] and default.tools is None
    assert Settings(columns=["feats", "lemma"]).columns == ["lemma", "feats"]  # kept in the standard order
    assert Settings(columns=[]).columns == [] and Settings(tools=[]).tools == []
    with pytest.raises(ValidationError, match="Unknown columns"):
        Settings(columns=["gloss"])
    with pytest.raises(ValidationError, match="Unknown tools"):
        Settings(tools=["set_links"])
    assert default.with_overrides(columns=[], tools=[]).columns == []
