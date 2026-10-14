"""Tests for the search tool: unit tests (offline) + browser tests (fake agent)."""

import pytest
from playwright.sync_api import Page, expect

from agent_app import tools


# ----------------------------- unit tests ---------------------------------- #
def test_fake_search_returns_canned_result(monkeypatch):
    monkeypatch.setenv("SEARCH_FAKE", "1")
    assert "SFTP" in tools.search_web("WinSCP")


def test_fake_search_unknown_topic(monkeypatch):
    monkeypatch.setenv("SEARCH_FAKE", "1")
    assert "No search results" in tools.search_web("zzzz-unknown")


def test_empty_query():
    assert "what to search for" in tools.search_web("   ")


def test_falls_back_to_wikipedia_when_duckduckgo_fails(monkeypatch):
    monkeypatch.delenv("SEARCH_FAKE", raising=False)
    monkeypatch.setattr(tools, "_duckduckgo", lambda q, n: None)
    monkeypatch.setattr(
        tools,
        "_wikipedia_summary",
        lambda q: [{"title": "WinSCP", "snippet": "An SFTP client.", "url": "https://x"}],
    )
    assert "An SFTP client." in tools.search_web("WinSCP")


def test_duckduckgo_result_is_preferred(monkeypatch):
    monkeypatch.delenv("SEARCH_FAKE", raising=False)
    monkeypatch.setattr(
        tools, "_duckduckgo",
        lambda q, n: [{"title": "DDG", "snippet": "from ddg", "url": "https://d"}],
    )
    monkeypatch.setattr(tools, "_wikipedia_summary", lambda q: pytest.fail("should not be called"))
    assert "from ddg" in tools.search_web("anything")


# ----------------------------- browser tests ------------------------------- #
def test_what_is_winscp_via_typed_question(page: Page, base_url):
    page.goto(base_url)
    page.get_by_test_id("msg").fill("What is WinSCP?")
    page.get_by_role("button", name="Send").click()
    expect(page.get_by_test_id("reply")).to_contain_text("SFTP")


def test_winscp_suggestion_chip(page: Page, base_url):
    page.goto(base_url)
    page.get_by_role("button", name="What is WinSCP?").click()
    expect(page.get_by_test_id("reply")).to_contain_text("secure file transfer")
