"""Deterministic offline provider for unit tests and CI. Never touches the network."""

import os

from src.common.providers.base import LLMRequest, LLMResponse


class FakeProvider:
    name = "fake"
    is_external = False

    def complete(self, request: LLMRequest) -> LLMResponse:
        # FAKE_LLM_REPLY is read per call so tests can change it with monkeypatch.setenv
        text = os.getenv("FAKE_LLM_REPLY") or f"[fake reply to: {request.prompt[:40]}]"
        return LLMResponse(
            text=text,
            # Rough word counts; real tokenizers are provider-specific
            input_tokens=max(1, len(request.prompt.split())),
            output_tokens=max(1, len(text.split())),
            model=request.model,
            provider=self.name,
        )
