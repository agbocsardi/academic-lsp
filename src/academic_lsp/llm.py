from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Protocol

from academic_lsp.config import LlmConfig


@dataclass(frozen=True)
class LlmDiagnostic:
    range_hint: str
    severity: str
    code: str
    message: str
    rule: str | None = None


class ChatJsonClient(Protocol):
    def chat_json(self, messages: list[dict[str, str]]) -> Any: ...


class LlmClientError(RuntimeError):
    pass


class LiteLlmClient:
    def __init__(self, config: LlmConfig) -> None:
        if not config.model:
            raise LlmClientError("LLM model is not configured")
        if not config.api_key:
            raise LlmClientError(f"LLM API key env var is not set: {config.api_key_env}")

        self.config = config

    def chat_json(self, messages: list[dict[str, str]]) -> Any:
        try:
            from litellm import completion
        except ImportError as error:
            raise LlmClientError(
                "LiteLLM is not installed. Run with `uv run --with litellm ...` or install the dev extra."
            ) from error

        kwargs: dict[str, Any] = {
            "model": self.config.model,
            "messages": messages,
            "temperature": self.config.temperature,
            "api_key": self.config.api_key,
            "response_format": {"type": "json_object"},
        }
        if self.config.base_url:
            kwargs["api_base"] = self.config.base_url

        response = completion(**kwargs)
        content = response.choices[0].message.content
        return json.loads(content)


def check_prose_with_llm(text: str, rules: str, client: ChatJsonClient) -> list[LlmDiagnostic]:
    result = client.chat_json(
        [
            {
                "role": "system",
                "content": (
                    "You are an academic prose diagnostic engine. "
                    "Return only JSON with a top-level diagnostics array. "
                    "Each diagnostic must have range_hint, severity, code, message, and optional rule. "
                    "Be conservative: flag only concrete issues grounded in the provided rules."
                ),
            },
            {
                "role": "user",
                "content": f"Rules:\n{rules}\n\nText:\n{text}",
            },
        ]
    )

    diagnostics = result.get("diagnostics", [])
    return [
        LlmDiagnostic(
            range_hint=item.get("range_hint", "document"),
            severity=item.get("severity", "warning"),
            code=item.get("code", "llm-diagnostic"),
            message=item.get("message", ""),
            rule=item.get("rule"),
        )
        for item in diagnostics
    ]
