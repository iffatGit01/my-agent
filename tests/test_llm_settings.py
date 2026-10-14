"""Unit tests for provider settings (no browser, no network)."""

import pytest

from agent_app.agent import resolve_llm_settings


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    for name in ("LLM_API_KEY", "LLM_BASE_URL", "LLM_MODEL", "GITHUB_TOKEN"):
        monkeypatch.delenv(name, raising=False)


def test_github_uses_token_and_endpoint(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "abc")
    cfg = resolve_llm_settings("github")
    assert cfg["api_key"] == "abc"
    assert cfg["base_url"] == "https://models.github.ai/inference"


def test_github_without_token_fails_clearly():
    with pytest.raises(RuntimeError, match="GITHUB_TOKEN"):
        resolve_llm_settings("github")


def test_ollama_needs_no_key():
    cfg = resolve_llm_settings("ollama")
    assert cfg["base_url"] == "http://localhost:11434/v1"
    assert cfg["api_key"]


def test_env_overrides(monkeypatch):
    monkeypatch.setenv("LLM_MODEL", "qwen2.5:7b")
    monkeypatch.setenv("LLM_BASE_URL", "http://example.test/v1")
    cfg = resolve_llm_settings("ollama")
    assert cfg["model"] == "qwen2.5:7b"
    assert cfg["base_url"] == "http://example.test/v1"


def test_unknown_provider():
    with pytest.raises(RuntimeError, match="Unknown LLM_PROVIDER"):
        resolve_llm_settings("nope")
