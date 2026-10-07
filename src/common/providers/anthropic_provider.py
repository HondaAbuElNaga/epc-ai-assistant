"""Claude via the Anthropic API. External: data leaves the machine."""

import anthropic

from src.common import config
from src.common.providers.base import LLMRequest, LLMResponse


class AnthropicProvider:
    name = "anthropic"
    is_external = True

    def __init__(self) -> None:
        api_key = config.anthropic_api_key()
        if not api_key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY is not set. Copy .env.example to .env and add it."
            )
        self._client = anthropic.Anthropic(api_key=api_key, max_retries=3)

    def complete(self, request: LLMRequest) -> LLMResponse:
        kwargs = {
            "model": request.model,
            "max_tokens": request.max_tokens,
            "messages": [{"role": "user", "content": request.prompt}],
        }
        if request.system:
            kwargs["system"] = request.system

        resp = self._client.messages.create(**kwargs)

        return LLMResponse(
            text="".join(block.text for block in resp.content if block.type == "text"),
            input_tokens=resp.usage.input_tokens,
            output_tokens=resp.usage.output_tokens,
            model=request.model,
            provider=self.name,
        )
