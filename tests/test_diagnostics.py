from academic_lsp.diagnostics import find_abbreviation_diagnostics


def test_warns_when_abbreviation_is_used_before_definition() -> None:
    text = "This paper uses LSP diagnostics for prose."

    diagnostics = find_abbreviation_diagnostics(text)

    assert len(diagnostics) == 1
    assert "LSP" in diagnostics[0].message
    assert diagnostics[0].line == 0
    assert diagnostics[0].start_character == 16
    assert diagnostics[0].end_character == 19
    assert len(diagnostics[0].message) < 80


def test_allows_abbreviation_after_definition() -> None:
    text = "Language Server Protocol (LSP) diagnostics are useful. LSP works for prose too."

    diagnostics = find_abbreviation_diagnostics(text)

    assert diagnostics == []


def test_warns_when_abbreviation_precedes_definition_on_same_line() -> None:
    text = "AOM submissions are tricky. Academy of Management (AOM) reviewers expect clarity."

    diagnostics = find_abbreviation_diagnostics(text)

    assert len(diagnostics) == 1
    assert "AOM" in diagnostics[0].message
    assert diagnostics[0].start_character == 0
