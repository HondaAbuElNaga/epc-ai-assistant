"""The contract every LLM provider (adapter) must follow, plus shared errors."""

from dataclasses import dataclass
from typing import ClassVar, Protocol


@dataclass(frozen=True)
class LLMRequest:
    prompt: str
    model: str
    system: str | None = None
    max_tokens: int = 1024


@dataclass(frozen=True)
class LLMResponse:
    text: str
    input_tokens: int
    output_tokens: int
    model: str
    provider: str


class LLMProvider(Protocol):
    """An adapter that turns an LLMRequest into an LLMResponse for one vendor or runtime."""

    name: ClassVar[str]
    # True if data leaves the machine/company network (e.g. a cloud API).
    is_external: ClassVar[bool]

    def complete(self, request: LLMRequest) -> LLMResponse: ...


class DataClassificationError(RuntimeError):
    """Confidential data was about to be sent to an external provider."""


class UnknownProviderError(ValueError):
    """LLM_PROVIDER names a provider that is not registered."""
