"""Playwright tests for the interactive parts of the UI (fake agent)."""

from playwright.sync_api import Page, expect


def test_welcome_is_shown_first(page: Page, base_url):
    page.goto(base_url)
    expect(page.get_by_test_id("welcome")).to_be_visible()
    expect(page.get_by_role("button", name="Weather in Dhaka")).to_be_visible()


def test_suggestion_chip_sends_a_message(page: Page, base_url):
    page.goto(base_url)
    page.get_by_role("button", name="Add 2 and 40").click()
    expect(page.get_by_test_id("reply")).to_have_text("The sum is 42")
    # welcome card disappears once the chat starts
    expect(page.get_by_test_id("welcome")).to_have_count(0)


def test_conversation_keeps_history(page: Page, base_url):
    page.goto(base_url)
    for question in ["weather in Tokyo", "add 1 and 2"]:
        page.get_by_test_id("msg").fill(question)
        page.get_by_role("button", name="Send").click()
        expect(page.get_by_test_id("typing")).to_have_count(0)

    expect(page.locator(".row.user")).to_have_count(2)
    expect(page.locator(".row.agent")).to_have_count(2)
    expect(page.locator(".row.agent .bubble").first).to_contain_text("Tokyo")
    expect(page.locator(".row.agent .bubble").last).to_contain_text("The sum is 3")


def test_enter_key_sends(page: Page, base_url):
    page.goto(base_url)
    page.get_by_test_id("msg").fill("hello")
    page.get_by_test_id("msg").press("Enter")
    expect(page.get_by_test_id("reply")).to_contain_text("Hello!")


def test_error_bubble_has_retry(page: Page, base_url):
    page.goto(base_url)
    page.get_by_test_id("msg").fill("boom")
    page.get_by_role("button", name="Send").click()
    expect(page.locator(".row.agent.error")).to_have_count(1)
    expect(page.get_by_role("button", name="Try again")).to_be_visible()


def test_clear_chat_restores_welcome(page: Page, base_url):
    page.goto(base_url)
    page.get_by_role("button", name="Weather in Dhaka").click()
    expect(page.locator(".row.agent")).to_have_count(1)
    page.get_by_role("button", name="Clear chat").click()
    expect(page.locator(".row")).to_have_count(0)
    expect(page.get_by_test_id("welcome")).to_be_visible()


def test_theme_toggle_switches_and_persists(page: Page, base_url):
    page.goto(base_url)
    html = page.locator("html")
    before = html.get_attribute("data-theme")
    page.get_by_role("button", name="Switch theme").click()
    after = html.get_attribute("data-theme")
    assert before != after

    page.reload()
    expect(html).to_have_attribute("data-theme", after)
