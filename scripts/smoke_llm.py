from __future__ import annotations

import os
from pathlib import Path

from academic_lsp.config import AcademicLspConfig, LlmConfig
from academic_lsp.llm import LiteLlmClient, check_prose_with_llm


RULES = """
# Smoke rules

- Flag paragraphs that make a claim without explaining why it follows from the previous sentence.
- Flag undefined technical terms when they are central to the paragraph.
""".strip()

TEXT = """
Platform governance improves organizational performance. Institutional complexity changes everything. Therefore, our model is complete.
""".strip()


def main() -> None:
    base_url = os.environ.get("ACADEMIC_LSP_LLM_BASE_URL", "https://opencode.ai/zen/go/v1")
    model = os.environ.get("ACADEMIC_LSP_LLM_MODEL", "openai/deepseek-v4-flash")
    api_key_env = os.environ.get("ACADEMIC_LSP_LLM_API_KEY_ENV", "OPENCODE_API_KEY")
    temperature = float(os.environ.get("ACADEMIC_LSP_LLM_TEMPERATURE", "0"))

    config = AcademicLspConfig(
        llm=LlmConfig(
            provider="litellm",
            base_url=base_url,
            model=model,
            api_key_env=api_key_env,
            temperature=temperature,
        )
    )

    print(f"base_url={config.llm.base_url}")
    print(f"model={config.llm.model}")
    print(f"api_key_env={config.llm.api_key_env}")
    print(f"api_key_set={bool(config.llm.api_key)}")
    print(f"temperature={config.llm.temperature}")

    diagnostics = check_prose_with_llm(TEXT, RULES, LiteLlmClient(config.llm))
    if not diagnostics:
        print("No diagnostics returned.")
        return

    for diagnostic in diagnostics:
        print("---")
        print(f"range_hint: {diagnostic.range_hint}")
        print(f"severity: {diagnostic.severity}")
        print(f"code: {diagnostic.code}")
        print(f"message: {diagnostic.message}")
        if diagnostic.rule:
            print(f"rule: {diagnostic.rule}")


if __name__ == "__main__":
    main()
