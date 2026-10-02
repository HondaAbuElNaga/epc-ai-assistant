"""Single wrapper around the Claude API: retries, logging, token usage tracking."""

import logging
from dataclasses import dataclass

import anthropic

from src.common import config

log = logging.getLogger(__name__)


@dataclass
class Usage:
    calls: int = 0
    input_tokens: int = 0
    output_tokens: int = 0


usage = Usage()
_client: anthropic.Anthropic | None = None


def client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        if not config.ANTHROPIC_API_KEY:
            raise RuntimeError(
                "ANTHROPIC_API_KEY is not set. Copy .env.example to .env and add it."
            )
        _client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY, max_retries=3)
    return _client


def complete(
    prompt: str,
    *,
    system: str | None = None,
    model: str | None = None,
    max_tokens: int = 1024,
) -> str:
    """Send one user message and return the text reply."""
    kwargs = {
        "model": model or config.MODEL_MAIN,
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": prompt}],
    }
    if system:
        kwargs["system"] = system

    resp = client().messages.create(**kwargs)

    usage.calls += 1
    usage.input_tokens += resp.usage.input_tokens
    usage.output_tokens += resp.usage.output_tokens
    log.info(
        "LLM %s in=%d out=%d", kwargs["model"], resp.usage.input_tokens, resp.usage.output_tokens
    )

    return "".join(block.text for block in resp.content if block.type == "text")
