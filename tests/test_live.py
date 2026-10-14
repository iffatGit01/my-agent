"""Opt-in tests against the REAL agent (needs Azure login + .env).

Run with:  pytest -m live
"""

import pytest
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.live


def test_real_agent_answers_weather(page: Page, live_base_url):
    page.goto(live_base_url)
    page.get_by_test_id("msg").fill("What's the weather in Tokyo?")
    page.get_by_role("button", name="Send").click()
    # The LLM's wording varies, so assert on facts coming from the tool, with a long timeout.
    expect(page.get_by_test_id("reply")).to_contain_text("22", timeout=60_000)
