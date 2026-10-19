# My Agent

A small AI agent with a modern chat interface, built with **Python** and the **Microsoft Agent Framework**, and tested end-to-end with **Playwright** and **pytest**.

It is modelled on the lessons in Microsoft's [AI Agents for Beginners](https://github.com/microsoft/ai-agents-for-beginners) course (lesson 14, Microsoft Agent Framework), but it can run completely **free**, without an Azure subscription.

## Features

- Chat web page with message bubbles, typing indicator, suggestion chips, copy button, retry on errors, clear chat, and light/dark theme.
- Agent tools:
  - `get_weather`: demo weather for a few cities
  - `add_numbers`: simple arithmetic
  - `search_web`: looks things up on the internet (DuckDuckGo, with a Wikipedia backup), no API key needed
  - `open_web_page`, `list_page_links`, `screenshot_web_page`: a **browsing agent**. It opens real pages in a Playwright-controlled browser, reads them, lists their links and shows screenshots in the chat
- Three interchangeable model backends: **GitHub Models** (free), **Ollama** (free, local), **Azure AI Foundry** (needs Azure).
- A `fake` agent mode so the browser tests are fast, deterministic and never touch the network.

## How it works

```
Browser (index.html)
      |  POST /chat {message}
      v
FastAPI server (agent_app/server.py)
      |
      v
Agent (agent_app/agent.py)  --->  Tools (agent_app/tools.py)
      |                              weather / add / web search
      v
Model backend:  GitHub Models | Ollama | Azure AI Foundry      (AGENT_MODE=real)
or the FakeAgent used by the tests                              (AGENT_MODE=fake)
```

## Project structure

```
my-agent/
├── agent_app/
│   ├── __init__.py
│   ├── agent.py          # builds the real agent or the fake test agent
│   ├── server.py         # FastAPI app: GET /, GET /health, POST /chat
│   ├── tools.py          # plain Python tool functions (weather, add, web search)
│   ├── browser_tool.py   # browsing tools (Playwright) + URL safety checks
│   └── static/
│       └── index.html    # chat UI
├── tests/
│   ├── conftest.py       # starts the server for the browser tests
│   ├── test_chat_ui.py   # Playwright: core chat behaviour
│   ├── test_ui_features.py  # Playwright: chips, history, theme, retry, clear
│   ├── test_search.py    # search tool unit tests + Playwright tests
│   ├── test_browser.py   # browsing tool: URL safety + full-stack Playwright tests
│   ├── site/             # tiny local demo website used by the browsing tests
│   ├── test_tools.py     # unit tests for the tools
│   ├── test_llm_settings.py # unit tests for provider settings
│   └── test_live.py      # opt-in tests against the real model
├── postman/              # Postman collection + environment for API tests
├── .env.example          # copy to .env and fill in
├── pytest.ini
├── requirements.txt
└── README.md
```

## Requirements

- Python 3.12 or newer
- One of the following for the real agent (not needed for the tests):
  - a GitHub account (free), or
  - [Ollama](https://ollama.com) installed on your computer (free), or
  - an Azure subscription with an Azure AI Foundry project

## Setup

Windows PowerShell:

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
playwright install
```

macOS / Linux:

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install --with-deps
```

## Run the tests

The tests use the fake agent, so they need no account, no model and no internet.

```powershell
pytest                              # run everything (headless)
pytest --headed --slowmo 400        # watch the browser while tests run
pytest --tracing=retain-on-failure  # save a trace for failing tests
pytest tests/test_search.py         # run one file
```

Tests marked `live` call the real model and are skipped by default:

```powershell
pytest -m live
```

## Run the real agent

1. Copy the example settings file:

   ```powershell
   Copy-Item .env.example .env
   ```

2. Edit `.env` and choose **one** backend.

   **Option 1: GitHub Models (free)**

   Create a GitHub personal access token with the **Models: read** permission, then:

   ```
   LLM_PROVIDER=github
   GITHUB_TOKEN=your-token-here
   # LLM_MODEL=openai/gpt-4.1-mini
   ```

   Other models are listed in the [GitHub Models catalog](https://github.com/marketplace/models).

   **Option 2: Ollama (free, runs on your computer)**

   ```powershell
   ollama pull llama3.1
   ```

   ```
   LLM_PROVIDER=ollama
   LLM_MODEL=llama3.1
   ```

   Small local models sometimes ignore tools. If the agent does not call the search tool, try a larger model such as `qwen2.5:7b`.

   **Option 3: Azure AI Foundry (needs an Azure subscription)**

   ```powershell
   az login
   ```

   ```
   LLM_PROVIDER=azure
   AZURE_AI_PROJECT_ENDPOINT=https://<your-resource>.services.ai.azure.com/api/projects/<your-project>
   AZURE_AI_MODEL_DEPLOYMENT_NAME=gpt-4o-mini
   ```

3. Start the server (stop and restart it after editing `.env`):

   ```powershell
   $env:AGENT_MODE="real"
   uvicorn agent_app.server:app --reload
   ```

4. Open <http://127.0.0.1:8000> and try:
   - "What's the weather in Dhaka?"
   - "add 2 and 40"
   - "What is WinSCP?"

## Configuration reference

| Variable | Meaning | Default |
| --- | --- | --- |
| `AGENT_MODE` | `real` or `fake` | `real` |
| `LLM_PROVIDER` | `github`, `ollama` or `azure` | `github` |
| `LLM_MODEL` | Model name for GitHub Models / Ollama | provider preset |
| `LLM_BASE_URL` | Override the endpoint URL | provider preset |
| `LLM_API_KEY` | Override the API key | provider preset |
| `GITHUB_TOKEN` | Token for GitHub Models | none |
| `SEARCH_FAKE` | `1` returns canned search results (used by tests) | unset |
| `BROWSER_HEADLESS` | `0` shows the browser window while the agent browses | `1` |
| `BROWSER_TIMEOUT` | Seconds to wait for a page | `20` |
| `BROWSER_ALLOW_LOCAL` | `1` allows `127.0.0.1` / `localhost` only (used by tests) | unset |

## Browsing agent

The agent can use a real browser. Try these in the chat:

- "Open https://example.com and tell me what it says"
- "List the links on https://example.com"
- "Take a screenshot of https://example.com"

To watch it work, start the server with the browser window visible:

```powershell
$env:BROWSER_HEADLESS="0"
$env:AGENT_MODE="real"
uvicorn agent_app.server:app --reload
```

How it is built and kept safe:

- Playwright runs in its own worker thread, so it works on Windows even with `--reload`.
- Each visit uses a fresh browser context, so no cookies or logins are shared between visits.
- Only `http` and `https` addresses are allowed. Addresses that point to private networks, your own computer or cloud metadata services are blocked, including redirects to them.
- Page text is passed to the model labelled as untrusted, and the agent's instructions tell it never to follow instructions written inside a page. This reduces, but does not remove, the risk of prompt injection, so do not give the agent tools that can change or delete things without asking you first.
- Screenshots are saved in `agent_app/static/shots/`. Delete old ones from time to time.

The tests use a small local website in `tests/site/`, so they never need the internet.

## API testing with Postman

The server exposes a small HTTP API, and `postman/` contains a ready-made collection with automatic checks.

| Endpoint | Purpose |
| --- | --- |
| `GET /health` | Returns `{"status": "ok"}` |
| `GET /` | The chat page |
| `POST /chat` | Body `{"message": "..."}`. Returns `{"reply": "..."}` or, on failure, status 500 with `{"error": "..."}` |
| `GET /docs` | Interactive Swagger page generated by FastAPI |
| `GET /openapi.json` | Machine-readable API description |

Start the server in **fake mode** so the answers are repeatable:

```powershell
$env:AGENT_MODE="fake"; $env:SEARCH_FAKE="1"; $env:BROWSER_ALLOW_LOCAL="1"
uvicorn agent_app.server:app --port 8000
```

In Postman: **Import** `postman/my-agent.postman_collection.json` and `postman/my-agent-local.postman_environment.json`, pick the environment **My Agent - local** (top right), then right-click the collection and choose **Run collection**. Folders 1 to 3 run in fake mode. Folder 4 needs the real agent (`AGENT_MODE=real`) and is slower.

Optional command-line run (for CI):

```powershell
npm install -g newman
newman run postman/my-agent.postman_collection.json -e postman/my-agent-local.postman_environment.json --folder "1. Basics" --folder "2. Chat - fake agent (deterministic)" --folder "3. Chat - error handling"
```

## Adding your own tool

1. Add a plain function to `agent_app/tools.py` and a unit test in `tests/`.
2. Wrap it with `@tool` inside `_make_tools()` in `agent_app/agent.py` and add it to the returned list.
3. Mention it in `INSTRUCTIONS` in `agent.py` so the model knows when to use it.
4. Teach `FakeAgent` how to route a matching question, then add a Playwright test.

## Troubleshooting

| Problem | Fix |
| --- | --- |
| `No module named 'agent_app'` when running pytest | `pytest.ini` must contain `pythonpath = .` |
| `No API key found for provider 'github'` | Your `.env` is missing, misnamed (for example `.env.txt`), or has no `GITHUB_TOKEN`. If you use Ollama, set `LLM_PROVIDER=ollama`. |
| Changes to `.env` are ignored | Stop the server with Ctrl+C and start it again. |
| 401 error from GitHub Models | The token is invalid or lacks the Models permission. |
| Connection refused with Ollama | The Ollama app is not running. |
| Model not found | `LLM_MODEL` does not match a model you pulled or can access. |
| Import error from `agent_framework` | The framework changes quickly. Compare the imports in `agent_app/agent.py` with lesson 14 of the course. |
| Playwright cannot find a browser | Run `playwright install`. |
| Agent says "The browser is not installed" | Run `playwright install chromium` in the same virtual environment the server uses. |
| Agent says "Blocked: ... private or local network" | The page is on your own network or computer. This is on purpose. |

## Security notes

- Never commit your `.env` file or share your tokens. `.gitignore` already excludes `.env`.
- The weather data is fake demo data.

## Credits

Based on the ideas in Microsoft's [AI Agents for Beginners](https://github.com/microsoft/ai-agents-for-beginners) course.
