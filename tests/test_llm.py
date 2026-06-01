from academic_lsp.config import AcademicLspConfig, DiagnosticConfig, LlmConfig
from academic_lsp.llm import LlmDiagnostic, check_prose_with_llm
from academic_lsp.server import (
    llm_diagnostic_to_lsp,
    range_from_hint,
    range_from_llm_diagnostic,
    should_run_llm_on_save,
)


class FakeClient:
    def chat_json(self, messages: list[dict[str, str]]) -> dict:
        assert messages
        assert "Make messages specific" in messages[0]["content"]
        assert "quote the exact concept" in messages[0]["content"]
        return {
            "diagnostics": [
                {
                    "range_hint": "sentence 1",
                    "severity": "warning",
                    "code": "define-central-terms",
                    "message": "Define 'institutional complexity' before using it.",
                    "rule": "define-central-terms",
                }
            ]
        }


def test_check_prose_with_llm_maps_structured_diagnostics() -> None:
    diagnostics = check_prose_with_llm(
        "Institutional complexity changes everything.",
        (
            "Rule: define-central-terms\n"
            "Central technical terms should be introduced before they carry the argument."
        ),
        FakeClient(),
    )

    assert len(diagnostics) == 1
    assert diagnostics[0].range_hint == "sentence 1"
    assert diagnostics[0].code == "define-central-terms"
    assert diagnostics[0].message == "Define 'institutional complexity' before using it."
    assert diagnostics[0].rule == "define-central-terms"


def test_range_hint_maps_to_markdown_paragraph() -> None:
    diagnostic_range = range_from_hint(
        "# Title\n\nFirst prose paragraph.\n\nSecond prose paragraph.",
        "paragraph 2",
    )

    assert diagnostic_range.start.line == 4
    assert diagnostic_range.start.character == 0
    assert diagnostic_range.end.line == 4


def test_quoted_term_takes_priority_over_range_hint() -> None:
    diagnostic_range = range_from_llm_diagnostic(
        "# Title\n\nAOM submissions are tricky.\n\nSecond prose paragraph.",
        LlmDiagnostic(
            range_hint="paragraph 2",
            severity="warning",
            code="define-abbreviations",
            message="Define 'AOM' before first use.",
            rule="define-abbreviations",
        ),
    )

    assert diagnostic_range.start.line == 2
    assert diagnostic_range.start.character == 0
    assert diagnostic_range.end.character == 3


def test_quoted_term_match_is_whole_word() -> None:
    diagnostic_range = range_from_llm_diagnostic(
        "# academic-lsp smoke test\n\nThe LSP improves feedback.",
        LlmDiagnostic(
            range_hint="paragraph 1",
            severity="warning",
            code="define-abbreviations",
            message="Define 'LSP' before first use.",
            rule="define-abbreviations",
        ),
    )

    assert diagnostic_range.start.line == 2
    assert diagnostic_range.start.character == 4


def test_llm_diagnostic_maps_to_range_hint() -> None:
    diagnostic = llm_diagnostic_to_lsp(
        "# Title\n\nFirst prose paragraph.\n\nSecond prose paragraph.",
        LlmDiagnostic(
            range_hint="paragraph 2",
            severity="warning",
            code="define-central-terms",
            message="Define 'second prose paragraph' before using it.",
            rule="define-central-terms",
        ),
    )

    assert diagnostic.range.start.line == 4
    assert diagnostic.range.start.character == 0
    assert diagnostic.source == "academic-lsp:llm"
    assert diagnostic.code == "define-central-terms"
    assert "paragraph 2" in diagnostic.message


def test_llm_save_requires_enabled_save_diagnostic_model_and_key(monkeypatch) -> None:
    monkeypatch.setenv("ACADEMIC_LSP_API_KEY", "test-key")

    config = AcademicLspConfig(
        llm=LlmConfig(model="openai/test-model"),
        diagnostics={
            "concept_definitions": DiagnosticConfig(engine="llm", run_on="save"),
        },
    )

    assert should_run_llm_on_save(config)


def test_llm_save_is_skipped_without_model(monkeypatch) -> None:
    monkeypatch.setenv("ACADEMIC_LSP_API_KEY", "test-key")

    config = AcademicLspConfig(
        llm=LlmConfig(model=None),
        diagnostics={
            "concept_definitions": DiagnosticConfig(engine="llm", run_on="save"),
        },
    )

    assert not should_run_llm_on_save(config)
