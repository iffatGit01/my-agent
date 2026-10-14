"""Plain Python functions the agent can use as tools.

Kept free of any agent-framework imports so they are trivial to unit test.
The agent wrappers (with @tool) live in agent.py.
"""

import json
import os
import urllib.parse
import urllib.request

# --------------------------------------------------------------------------- #
# Weather + math (simple demo tools)
# --------------------------------------------------------------------------- #
_WEATHER = {
    "dhaka": "32°C, humid, chance of evening rain",
    "london": "14°C, cloudy",
    "tokyo": "22°C, clear",
    "seattle": "12°C, light drizzle",
}


def get_weather(city: str) -> str:
    """Return a (fake) weather report for a city."""
    report = _WEATHER.get(city.strip().lower())
    if report is None:
        return f"Sorry, I have no weather data for {city}."
    return f"Weather in {city.strip().title()}: {report}"


def add_numbers(a: float, b: float) -> float:
    """Add two numbers."""
    return a + b


# --------------------------------------------------------------------------- #
# Web search (free, no API key)
# --------------------------------------------------------------------------- #
USER_AGENT = "my-agent/1.0 (learning project)"
TIMEOUT_SECONDS = 8

# Canned answers used when SEARCH_FAKE=1 (the Playwright tests), so tests never touch the network.
_FAKE_RESULTS = {
    "winscp": [
        {
            "title": "WinSCP",
            "snippet": (
                "WinSCP is a free and open-source SFTP, FTP, WebDAV, Amazon S3 and SCP "
                "client for Microsoft Windows. Its main function is secure file transfer "
                "between a local and a remote computer."
            ),
            "url": "https://winscp.net",
        }
    ],
}


def _get_json(url: str) -> dict:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
        return json.loads(response.read().decode("utf-8"))


def _duckduckgo(query: str, max_results: int):
    """Search DuckDuckGo through the `ddgs` package. Returns None if unavailable/failed."""
    try:
        from ddgs import DDGS
    except ImportError:
        return None
    try:
        raw = DDGS().text(query, max_results=max_results)
    except Exception:
        return None
    results = [
        {"title": r.get("title", ""), "snippet": r.get("body", ""), "url": r.get("href", "")}
        for r in (raw or [])
    ]
    return results or None


def _wikipedia_summary(query: str):
    """Backup: summary of the best-matching Wikipedia article. Returns None on failure."""
    try:
        search = _get_json(
            "https://en.wikipedia.org/w/api.php?"
            + urllib.parse.urlencode(
                {"action": "query", "list": "search", "srsearch": query,
                 "srlimit": 1, "format": "json"}
            )
        )
        hits = search.get("query", {}).get("search", [])
        if not hits:
            return None
        title = hits[0]["title"]
        summary = _get_json(
            "https://en.wikipedia.org/api/rest_v1/page/summary/"
            + urllib.parse.quote(title.replace(" ", "_"))
        )
        return [{
            "title": summary.get("title", title),
            "snippet": summary.get("extract", ""),
            "url": summary.get("content_urls", {}).get("desktop", {}).get("page", ""),
        }]
    except Exception:
        return None


def format_results(results) -> str:
    lines = []
    for i, r in enumerate(results, 1):
        lines.append(f"{i}. {r['title']}: {r['snippet']} ({r['url']})".strip())
    return "\n".join(lines)


def search_web(query: str, max_results: int = 3) -> str:
    """Look something up on the internet and return a short text summary of the results."""
    query = query.strip()
    if not query:
        return "Please tell me what to search for."

    if os.getenv("SEARCH_FAKE"):
        results = _FAKE_RESULTS.get(query.lower())
    else:
        results = _duckduckgo(query, max_results) or _wikipedia_summary(query)

    if not results:
        return f"No search results found for '{query}'."
    return format_results(results)
