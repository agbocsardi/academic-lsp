from __future__ import annotations

import re
from dataclasses import dataclass

ABBREVIATION_RE = re.compile(r"\b[A-Z][A-Z0-9]{1,}\b")
DEFINITION_RE = re.compile(r"\b(?P<long>[A-Z][A-Za-z0-9 ,\-/]{3,}?)\s*\((?P<abbr>[A-Z][A-Z0-9]{1,})\)")

IGNORED_ABBREVIATIONS = {
    "I",
    "II",
    "III",
    "IV",
    "V",
    "VI",
    "VII",
    "VIII",
    "IX",
    "X",
    "AI",
    "API",
    "PDF",
    "URL",
    "URI",
    "DOI",
}


@dataclass(frozen=True)
class ProseDiagnostic:
    line: int
    start_character: int
    end_character: int
    message: str
    source: str = "academic-lsp"


def find_abbreviation_diagnostics(text: str) -> list[ProseDiagnostic]:
    """Warn when an abbreviation is used before a local definition.

    Definition shape currently recognized: `Long Form (LF)`.
    """
    defined: set[str] = set()
    diagnostics: list[ProseDiagnostic] = []

    for line_number, line in enumerate(text.splitlines()):
        definitions_on_line = {match.group("abbr") for match in DEFINITION_RE.finditer(line)}

        for match in ABBREVIATION_RE.finditer(line):
            abbr = match.group(0)
            if abbr in IGNORED_ABBREVIATIONS or abbr in defined or abbr in definitions_on_line:
                continue

            diagnostics.append(
                ProseDiagnostic(
                    line=line_number,
                    start_character=match.start(),
                    end_character=match.end(),
                    message=f"Define '{abbr}' before first use, e.g. 'Long Form ({abbr})'.",
                )
            )

        defined.update(definitions_on_line)

    return diagnostics
