from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

CheckTrigger = Literal["change", "idle", "save", "manual"]

DEFAULT_CONFIG_FILENAMES = (
    "academic-lsp.toml",
    ".academic-lsp.toml",
    ".academic-lsp/config.toml",
)


@dataclass(frozen=True)
class RuleConfig:
    files: list[str] = field(default_factory=lambda: [".academic-lsp/rules.md"])


@dataclass(frozen=True)
class LlmConfig:
    provider: str = "openai-compatible"
    base_url: str | None = None
    model: str | None = None
    temperature: float = 0.0
    api_key_env: str = "ACADEMIC_LSP_API_KEY"

    @property
    def api_key(self) -> str | None:
        return os.environ.get(self.api_key_env)


@dataclass(frozen=True)
class DiagnosticConfig:
    enabled: bool = True
    engine: Literal["deterministic", "llm"] = "deterministic"
    run_on: CheckTrigger = "idle"
    debounce_ms: int = 1500


@dataclass(frozen=True)
class AcademicLspConfig:
    rules: RuleConfig = field(default_factory=RuleConfig)
    llm: LlmConfig = field(default_factory=LlmConfig)
    diagnostics: dict[str, DiagnosticConfig] = field(
        default_factory=lambda: {
            "abbreviations": DiagnosticConfig(engine="deterministic", run_on="idle"),
            "forbidden_phrases": DiagnosticConfig(engine="deterministic", run_on="idle"),
            "concept_definitions": DiagnosticConfig(engine="llm", run_on="save"),
            "paragraph_transitions": DiagnosticConfig(engine="llm", run_on="save"),
        }
    )


def find_config_file(root: Path) -> Path | None:
    for filename in DEFAULT_CONFIG_FILENAMES:
        candidate = root / filename
        if candidate.exists():
            return candidate
    return None


def load_config(root: Path) -> AcademicLspConfig:
    config_file = find_config_file(root)
    if config_file is None:
        return AcademicLspConfig()

    data = tomllib.loads(config_file.read_text(encoding="utf-8"))
    rules = RuleConfig(files=list(data.get("rules", {}).get("files", RuleConfig().files)))

    llm_data = data.get("llm", {})
    llm = LlmConfig(
        provider=llm_data.get("provider", LlmConfig.provider),
        base_url=llm_data.get("base_url"),
        model=llm_data.get("model"),
        temperature=llm_data.get("temperature", LlmConfig.temperature),
        api_key_env=llm_data.get("api_key_env", LlmConfig.api_key_env),
    )

    diagnostics = AcademicLspConfig().diagnostics.copy()
    for name, diagnostic_data in data.get("diagnostics", {}).items():
        current = diagnostics.get(name, DiagnosticConfig())
        diagnostics[name] = DiagnosticConfig(
            enabled=diagnostic_data.get("enabled", current.enabled),
            engine=diagnostic_data.get("engine", current.engine),
            run_on=diagnostic_data.get("run_on", current.run_on),
            debounce_ms=diagnostic_data.get("debounce_ms", current.debounce_ms),
        )

    return AcademicLspConfig(rules=rules, llm=llm, diagnostics=diagnostics)
