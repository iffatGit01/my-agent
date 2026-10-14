"""Agent construction.

AGENT_MODE selects how the agent is built:

  fake  -> deterministic stand-in used by the Playwright tests (no network)
  real  -> a real LLM-backed agent built with the Microsoft Agent Framework

For AGENT_MODE=real, LLM_PROVIDER selects the model backend:

  github  -> GitHub Models   (FREE tier, needs a GitHub token)      <- default
  ollama  -> Ollama on your own PC (FREE, offline, no account)
  azure   -> Azure AI Foundry (needs an Azure subscription)

Every option exposes the same interface:  `await agent.run("text")` -> object with `.text`
"""

import os
import re
from contextlib import AsyncExitStack
from dataclasses import dataclass
from typing import Annotated

from pydantic import Field

from .tools import add_numbers, get_weather, search_web

INSTRUCTIONS = (
    "You are a friendly assistant. Use the get_weather tool for weather questions, "
    "the add tool for arithmetic, and the search_web tool whenever the user asks what "
    "something is or wants facts about software, people, places or other topics. "
    "Base your answer on the search results and keep it short."
)


@dataclass
class Reply:
    text: str


# --------------------------------------------------------------------------- #
# Fake agent (tests)
# --------------------------------------------------------------------------- #
class FakeAgent:
    """Deterministic agent: routes messages to the same tool functions."""

    async def run(self, message: str) -> Reply:
        text = message.lower()

        if "weather" in text:
            match = re.search(r"weather (?:in|for) ([a-zA-Z ]+?)\??$", message.strip(), re.I)
            city = match.group(1) if match else "Dhaka"
            return Reply(get_weather(city))

        numbers = re.findall(r"-?\d+(?:\.\d+)?", message)
        if ("add" in text or "plus" in text or "+" in text) and len(numbers) >= 2:
            total = add_numbers(float(numbers[0]), float(numbers[1]))
            return Reply(f"The sum is {total:g}")

        lookup = re.match(
            r"^(?:what(?:'s| is)|who is|tell me about|search(?: for)?|look up)\s+(.+?)\??$",
            message.strip(),
            re.I,
        )
        if lookup:
            return Reply(search_web(lookup.group(1)))

        if "boom" in text:
            raise RuntimeError("simulated agent failure")

        return Reply("Hello! Ask me about the weather or to add two numbers.")


# --------------------------------------------------------------------------- #
# Tools for the real agent
# --------------------------------------------------------------------------- #
def _make_tools():
    """Wrap the plain functions in tools.py with the framework's @tool decorator."""
    from agent_framework import tool

    @tool(approval_mode="never_require")
    def get_weather_tool(
        city: Annotated[str, Field(description="City name, e.g. Dhaka")],
    ) -> str:
        """Get the current weather for a city."""
        return get_weather(city)

    @tool(approval_mode="never_require")
    def add_tool(
        a: Annotated[float, Field(description="First number")],
        b: Annotated[float, Field(description="Second number")],
    ) -> float:
        """Add two numbers."""
        return add_numbers(a, b)

    @tool(approval_mode="never_require")
    def search_web_tool(
        query: Annotated[str, Field(description="What to look up, e.g. 'WinSCP'")],
    ) -> str:
        """Search the internet for facts about software, people, places or other topics."""
        return search_web(query)

    return [get_weather_tool, add_tool, search_web_tool]


# --------------------------------------------------------------------------- #
# FREE options: GitHub Models / Ollama (OpenAI-compatible endpoints)
# --------------------------------------------------------------------------- #
PRESETS = {
    "github": {
        "base_url": "https://models.github.ai/inference",
        "key_env": "GITHUB_TOKEN",
        "model": "openai/gpt-4.1-mini",
    },
    "ollama": {
        "base_url": "http://localhost:11434/v1",
        "key_env": None,          # Ollama ignores the key, but the client needs a value
        "default_key": "ollama",
        "model": "llama3.1",
    },
}


def resolve_llm_settings(provider: str) -> dict:
    """Work out base_url / api_key / model from the provider preset + env overrides.

    Overrides: LLM_BASE_URL, LLM_API_KEY, LLM_MODEL.
    """
    if provider not in PRESETS:
        raise RuntimeError(
            f"Unknown LLM_PROVIDER '{provider}'. Use one of: {', '.join(PRESETS)}, azure."
        )
    preset = PRESETS[provider]

    api_key = os.getenv("LLM_API_KEY")
    if not api_key and preset["key_env"]:
        api_key = os.getenv(preset["key_env"])
    if not api_key:
        api_key = preset.get("default_key")
    if not api_key:
        raise RuntimeError(
            f"No API key found for provider '{provider}'. "
            f"Set {preset['key_env']} (or LLM_API_KEY) in your .env file."
        )

    return {
        "base_url": os.getenv("LLM_BASE_URL", preset["base_url"]),
        "api_key": api_key,
        "model": os.getenv("LLM_MODEL", preset["model"]),
    }


def build_openai_compatible_agent(provider: str):
    """Agent Framework agent that talks to any OpenAI-compatible endpoint."""
    cfg = resolve_llm_settings(provider)

    # The framework's OpenAI client (and the underlying openai SDK) read these
    # standard variables, so this works without depending on constructor details.
    os.environ["OPENAI_API_KEY"] = cfg["api_key"]
    os.environ["OPENAI_BASE_URL"] = cfg["base_url"]
    for name in ("OPENAI_CHAT_MODEL", "OPENAI_CHAT_MODEL_ID", "OPENAI_MODEL"):
        os.environ[name] = cfg["model"]

    # These endpoints speak the Chat Completions API. Newer framework versions call that
    # client OpenAIChatCompletionClient; older versions called it OpenAIChatClient.
    try:
        from agent_framework.openai import OpenAIChatCompletionClient as Client
    except ImportError:
        from agent_framework.openai import OpenAIChatClient as Client

    client = Client()
    make_agent = getattr(client, "as_agent", None) or client.create_agent
    return make_agent(name="MyFirstAgent", instructions=INSTRUCTIONS, tools=_make_tools())


# --------------------------------------------------------------------------- #
# Azure AI Foundry (needs an Azure subscription)
# --------------------------------------------------------------------------- #
async def build_azure_agent(stack: AsyncExitStack):
    from agent_framework.azure import AzureAIProjectAgentProvider
    from azure.identity.aio import AzureCliCredential

    credential = await stack.enter_async_context(AzureCliCredential())
    provider = await stack.enter_async_context(
        AzureAIProjectAgentProvider(credential=credential)
    )
    return await provider.create_agent(
        name="MyFirstAgent",
        instructions=INSTRUCTIONS,
        tools=_make_tools(),
    )


# --------------------------------------------------------------------------- #
# Entry point used by server.py
# --------------------------------------------------------------------------- #
async def build_agent(stack: AsyncExitStack):
    if os.getenv("AGENT_MODE", "real").lower() == "fake":
        return FakeAgent()

    provider = os.getenv("LLM_PROVIDER", "github").lower()
    if provider == "azure":
        return await build_azure_agent(stack)
    return build_openai_compatible_agent(provider)
