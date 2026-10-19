"""Playwright end-to-end tests against the chat UI (fake agent, deterministic)."""

from playwright.sync_api import Page, expect


def ask(page: Page, base_url: str, question: str):
    page.goto(base_url)
    page.get_by_test_id("msg").fill(question)
    page.get_by_role("button", name="Send").click()


def test_page_loads(page: Page, base_url):
    page.goto(base_url)
    expect(page).to_have_title("Easy Agent")
    expect(page.get_by_test_id("msg")).to_be_visible()


def test_weather_tool_reply(page: Page, base_url):
    ask(page, base_url, "What's the weather in Dhaka?")
    expect(page.get_by_test_id("reply")).to_contain_text("Weather in Dhaka")
    expect(page.get_by_test_id("reply")).to_contain_text("32")


def test_unknown_city(page: Page, base_url):
    ask(page, base_url, "weather in Atlantis")
    expect(page.get_by_test_id("reply")).to_contain_text("no weather data")


def test_add_tool_reply(page: Page, base_url):
    ask(page, base_url, "add 2 and 40")
    expect(page.get_by_test_id("reply")).to_have_text("The sum is 42")


def test_input_is_cleared_after_send(page: Page, base_url):
    ask(page, base_url, "hello")
    expect(page.get_by_test_id("reply")).not_to_be_empty()
    expect(page.get_by_test_id("msg")).to_have_value("")


def test_error_is_shown_to_user(page: Page, base_url):
    ask(page, base_url, "boom")
    reply = page.get_by_test_id("reply")
    expect(reply).to_contain_text("Something went wrong")
    expect(reply).to_have_class("error")


def test_empty_message_does_nothing(page: Page, base_url):
    page.goto(base_url)
    page.get_by_role("button", name="Send").click()
    expect(page.get_by_test_id("reply")).to_be_empty()
