import os
import subprocess
import sys
import time
import urllib.request

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _start_server(port: int, mode: str):
    env = {**os.environ, "AGENT_MODE": mode}
    if mode == "fake":
        env["SEARCH_FAKE"] = "1"  # canned search results: tests never touch the internet
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "agent_app.server:app", "--port", str(port)],
        cwd=ROOT,
        env=env,
    )
    url = f"http://127.0.0.1:{port}"
    for _ in range(100):
        try:
            urllib.request.urlopen(f"{url}/health", timeout=1)
            return proc, url
        except Exception:
            time.sleep(0.2)
    proc.terminate()
    raise RuntimeError(f"Server did not start on port {port}")


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
