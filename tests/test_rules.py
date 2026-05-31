from pathlib import Path


BASIC_RULES = Path("rules/basic-academic-prose.md")


def test_basic_ruleset_documents_tested_deterministic_rule() -> None:
    rules = BASIC_RULES.read_text(encoding="utf-8")

    assert "Rule: define-abbreviations" in rules
    assert "Long Form (LF)" in rules
    assert "Define 'LSP' before first use" in rules
    assert "AI, API, PDF, URL, URI, DOI" in rules


def test_basic_ruleset_documents_tested_llm_rule() -> None:
    rules = BASIC_RULES.read_text(encoding="utf-8")

    assert "Rule: define-central-terms" in rules
    assert "Define the central term before using it." in rules
    assert '"span_id": "p1"' in rules
    assert '"code": "define-central-terms"' in rules


def test_basic_ruleset_documents_inline_feedback_constraint() -> None:
    rules = BASIC_RULES.read_text(encoding="utf-8")

    assert "Rule: keep-inline-feedback-short" in rules
    assert "Messages should be short, specific, and actionable." in rules
