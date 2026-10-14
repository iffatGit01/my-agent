# My Agent

A small AI agent with a modern chat interface, built with **Python** and the **Microsoft Agent Framework**, and tested end-to-end with **Playwright** and **pytest**.

It is modelled on the lessons in Microsoft's [AI Agents for Beginners](https://github.com/microsoft/ai-agents-for-beginners) course (lesson 14, Microsoft Agent Framework), but it can run completely **free**, without an Azure subscription.

## Features

- Chat web page with message bubbles, typing indicator, suggestion chips, copy button, retry on errors, clear chat, and light/dark theme.
- Agent tools:
  - `get_weather`: demo weather for a few cities
  - `add_numbers`: simple arithmetic
  - `search_web`: looks things up on the internet (DuckDuckGo, with a Wikipedia backup), no API key needed
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
│   ├── tools.py          # plain Python tool functions
│   └── static/
│       └── index.html    # chat UI
├── tests/
│   ├── conftest.py       # starts the server for the browser tests
│   ├── test_chat_ui.py   # Playwright: core chat behaviour
│   ├── test_ui_features.py  # Playwright: chips, history, theme, retry, clear
│   ├── test_search.py    # search tool unit tests + Playwright tests
│   ├── test_tools.py     # unit tests for the tools
│   ├── test_llm_settings.py # unit tests for provider settings
│   └── test_live.py      # opt-in tests against the real model
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

## Security notes

- Never commit your `.env` file or share your tokens. `.gitignore` already excludes `.env`.
- The weather data is fake demo data.

## Credits

Based on the ideas in Microsoft's [AI Agents for Beginners](https://github.com/microsoft/ai-agents-for-beginners) course.
