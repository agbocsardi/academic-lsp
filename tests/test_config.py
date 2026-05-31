from pathlib import Path

from academic_lsp.config import load_config


def test_default_triggers_are_idle_for_deterministic_and_save_for_llm(tmp_path: Path) -> None:
    config = load_config(tmp_path)

    assert config.diagnostics["abbreviations"].run_on == "idle"
    assert config.diagnostics["abbreviations"].engine == "deterministic"
    assert config.diagnostics["paragraph_transitions"].run_on == "save"
    assert config.diagnostics["paragraph_transitions"].engine == "llm"


def test_loads_project_config(tmp_path: Path) -> None:
    (tmp_path / "academic-lsp.toml").write_text(
        """
[rules]
files = ["rules.md"]

[llm]
base_url = "https://example.test/v1"
model = "deepseek-v4-flash"
api_key_env = "MY_KEY"

[diagnostics.abbreviations]
run_on = "save"
debounce_ms = 2500
""".strip(),
        encoding="utf-8",
    )

    config = load_config(tmp_path)

    assert config.rules.files == ["rules.md"]
    assert config.llm.base_url == "https://example.test/v1"
    assert config.llm.model == "deepseek-v4-flash"
    assert config.llm.api_key_env == "MY_KEY"
    assert config.diagnostics["abbreviations"].run_on == "save"
    assert config.diagnostics["abbreviations"].debounce_ms == 2500
