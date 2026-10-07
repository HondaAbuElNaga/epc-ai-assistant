"""Single entry point for all LLM calls: provider selection, data guard, tiers, usage tracking.

Modules call `complete(prompt, tier="main"|"fast")` and never import a provider SDK. The provider
is chosen by LLM_PROVIDER in .env; DATA_CLASSIFICATION=confidential blocks external providers.
"""

import logging
from dataclasses import dataclass

from src.common import config
from src.common.providers import (
    DataClassificationError,
    LLMProvider,
    LLMRequest,
    LLMResponse,
    UnknownProviderError,
)
from src.common.providers.anthropic_provider import AnthropicProvider
from src.common.providers.fake_provider import FakeProvider

log = logging.getLogger(__name__)

# name -> provider class. Classes declare is_external, so the guard can run before any
# instance (and therefore any client or network connection) is created.
PROVIDERS: dict[str, type[LLMProvider]] = {
    AnthropicProvider.name: AnthropicProvider,
    FakeProvider.name: FakeProvider,
}

_instances: dict[str, LLMProvider] = {}


@dataclass
class Usage:
    calls: int = 0
    input_tokens: int = 0
    output_tokens: int = 0


usage = Usage()
_last: LLMResponse | None = None


def reset_usage() -> None:
    global _last
    usage.calls = usage.input_tokens = usage.output_tokens = 0
    _last = None


def clear_provider_cache() -> None:
    _instances.clear()


def last_call() -> LLMResponse | None:
    """The last response (provider, model, tokens), or None before the first call."""
    return _last


def _provider_class(name: str) -> type[LLMProvider]:
    try:
        return PROVIDERS[name]
    except KeyError:
        valid = ", ".join(sorted(PROVIDERS))
        raise UnknownProviderError(
            f"LLM_PROVIDER={name!r} is not a known provider. Valid: {valid}"
        ) from None


def _check_data_guard(provider_cls: type[LLMProvider]) -> None:
    if config.data_classification() == "confidential" and provider_cls.is_external:
        raise DataClassificationError(
            f"DATA_CLASSIFICATION=confidential but LLM_PROVIDER={provider_cls.name!r} is an "
            "external service. Use a local provider for confidential data."
        )


def complete(
    prompt: str,
    *,
    system: str | None = None,
    tier: str = "main",
    model: str | None = None,
    max_tokens: int = 1024,
) -> str:
    """Send one user message and return the text reply. An explicit `model` wins over `tier`."""
    global _last
    name = config.llm_provider()
    provider_cls = _provider_class(name)
    _check_data_guard(provider_cls)  # before any client exists

    request = LLMRequest(
        prompt=prompt,
        system=system,
        model=model or config.model_for(name, tier),
        max_tokens=max_tokens,
    )
    if name not in _instances:
        _instances[name] = provider_cls()
    resp = _instances[name].complete(request)

    usage.calls += 1
    usage.input_tokens += resp.input_tokens
    usage.output_tokens += resp.output_tokens
    _last = resp
    log.info(
        "LLM %s/%s in=%d out=%d", resp.provider, resp.model, resp.input_tokens, resp.output_tokens
    )

    return resp.text
