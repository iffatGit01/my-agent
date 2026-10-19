import os
import subprocess
import sys
import time
import urllib.request

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE_DIR = os.path.join(ROOT, "tests", "site")


def _wait_for(url: str, proc, what: str):
    for _ in range(100):
        try:
            urllib.request.urlopen(url, timeout=1)
            return
        except Exception:
            time.sleep(0.2)
    proc.terminate()
    raise RuntimeError(f"{what} did not start")


def _start_server(port: int, mode: str):
    env = {**os.environ, "AGENT_MODE": mode}
    if mode == "fake":
        env["SEARCH_FAKE"] = "1"         # canned search results: no internet
        env["BROWSER_ALLOW_LOCAL"] = "1"  # lets the agent open the local demo site (loopback only)
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "agent_app.server:app", "--port", str(port)],
        cwd=ROOT,
        env=env,
    )
    url = f"http://127.0.0.1:{port}"
    _wait_for(f"{url}/health", proc, f"Server on port {port}")
    return proc, url


@pytest.fixture(scope="session")
def base_url():
    """Server running the FAKE agent. Used by the normal (fast, offline) tests."""
    proc, url = _start_server(8765, "fake")
    yield url
    proc.terminate()
    proc.wait(timeout=10)


@pytest.fixture(scope="session")
def live_base_url():
    """Server running the REAL agent. Only used by tests marked `live`."""
    proc, url = _start_server(8766, "real")
    yield url
    proc.terminate()
    proc.wait(timeout=10)


@pytest.fixture(scope="session")
def site_url():
    """A tiny local website (tests/site) that the browsing agent is pointed at."""
    port = 8770
    proc = subprocess.Popen(
        [sys.executable, "-m", "http.server", str(port), "--bind", "127.0.0.1",
         "--directory", SITE_DIR],
    )
    url = f"http://127.0.0.1:{port}"
    _wait_for(f"{url}/index.html", proc, "Demo site")
    yield url
    proc.terminate()
    proc.wait(timeout=10)
