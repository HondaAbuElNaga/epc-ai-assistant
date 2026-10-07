"""Provider-agnostic LLM interface + data classification guard.

Spec: specs/2026-10-06-llm-provider-interface/spec.md. No test here calls a real API.
"""

import ast
from pathlib import Path

import pytest

from src.common import config, llm
from src.common.providers import DataClassificationError, UnknownProviderError
from src.common.providers.anthropic_provider import AnthropicProvider

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def fake_env(monkeypatch):
    """Fake provider on public data, independent of whatever is in .env."""
    monkeypatch.setenv("LLM_PROVIDER", "fake")
    monkeypatch.setenv("DATA_CLASSIFICATION", "public")
    monkeypatch.delenv("FAKE_LLM_REPLY", raising=False)


def test_fake_provider_returns_reply_and_counts_usage(fake_env, monkeypatch):
    monkeypatch.setenv("FAKE_LLM_REPLY", "hello from fake")

    assert llm.complete("hi") == "hello from fake"
    assert llm.usage.calls == 1
    assert llm.usage.input_tokens > 0
    assert llm.usage.output_tokens > 0
    assert llm.last_call().provider == "fake"


def test_fake_provider_default_reply_is_deterministic(fake_env):
    assert llm.complete("same prompt") == llm.complete("same prompt")
    assert llm.usage.calls == 2


def test_unknown_provider_lists_valid_ones(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "unknown")
    monkeypatch.setenv("DATA_CLASSIFICATION", "public")

    with pytest.raises(UnknownProviderError) as exc:
        llm.complete("hi")
    message = str(exc.value)
    assert "unknown" in message
    assert "anthropic" in message and "fake" in message


def test_guard_blocks_confidential_data_before_any_client_is_created(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "anthropic")
    monkeypatch.setenv("DATA_CLASSIFICATION", "confidential")

    def must_not_be_called(*args, **kwargs):
        raise AssertionError("the external provider was created despite the guard")

    monkeypatch.setattr(AnthropicProvider, "__init__", must_not_be_called)

    with pytest.raises(DataClassificationError):
        llm.complete("secret contract price")
    assert llm.usage.calls == 0


def test_guard_allows_confidential_data_on_local_provider(fake_env, monkeypatch):
    monkeypatch.setenv("DATA_CLASSIFICATION", "confidential")

    assert llm.complete("secret contract price")
    assert llm.usage.calls == 1


def test_data_classification_defaults_to_public(monkeypatch):
    monkeypatch.delenv("DATA_CLASSIFICATION", raising=False)
    assert config.data_classification() == "public"


def test_invalid_data_classification_raises(fake_env, monkeypatch):
    monkeypatch.setenv("DATA_CLASSIFICATION", "confidental")  # typo on purpose

    with pytest.raises(ValueError, match="confidental"):
        llm.complete("hi")


def test_fast_tier_uses_the_configured_fast_model(fake_env, monkeypatch):
    monkeypatch.setenv("FAKE_MODEL_FAST", "fake-small")

    llm.complete("hi", tier="fast")
    assert llm.last_call().model == "fake-small"


def test_anthropic_tier_models_overridable_from_env(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_MODEL_FAST", "my-fast-model")
    assert config.model_for("anthropic", "fast") == "my-fast-model"


def test_unknown_tier_raises(fake_env):
    with pytest.raises(ValueError, match="tier"):
        llm.complete("hi", tier="huge")


def test_explicit_model_wins_over_tier(fake_env):
    llm.complete("hi", tier="fast", model="x")
    assert llm.last_call().model == "x"


def test_legacy_model_constants_are_anthropic_tier_aliases():
    assert config.MODEL_MAIN == config.model_for("anthropic", "main")
    assert config.MODEL_FAST == config.model_for("anthropic", "fast")


def _imports_anthropic(path: Path) -> bool:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            names = [node.module or ""]
        else:
            continue
        if any(name == "anthropic" or name.startswith("anthropic.") for name in names):
            return True
    return False


def test_only_providers_import_the_anthropic_sdk():
    providers_dir = ROOT / "src" / "common" / "providers"
    offenders = [
        str(path.relative_to(ROOT))
        for path in (ROOT / "src").rglob("*.py")
        if providers_dir not in path.parents and _imports_anthropic(path)
    ]
    assert offenders == [], f"Import provider SDKs only in src/common/providers/: {offenders}"
