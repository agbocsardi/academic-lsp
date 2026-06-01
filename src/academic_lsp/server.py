from __future__ import annotations

import argparse
import re
import time
from pathlib import Path
from urllib.parse import unquote, urlparse

from lsprotocol.types import (
    TEXT_DOCUMENT_DID_CHANGE,
    TEXT_DOCUMENT_DID_OPEN,
    TEXT_DOCUMENT_DID_SAVE,
    Diagnostic,
    DiagnosticSeverity,
    DidChangeTextDocumentParams,
    DidOpenTextDocumentParams,
    DidSaveTextDocumentParams,
    LogMessageParams,
    MessageType,
    Position,
    PublishDiagnosticsParams,
    Range,
)
from pygls.lsp.server import LanguageServer

from academic_lsp import __version__
from academic_lsp.config import DEFAULT_CONFIG_FILENAMES, AcademicLspConfig, load_config
from academic_lsp.diagnostics import find_abbreviation_diagnostics
from academic_lsp.llm import (
    LiteLlmClient,
    LlmClientError,
    LlmDiagnostic,
    check_prose_with_llm,
)

SERVER_NAME = "academic-lsp"

server = LanguageServer(SERVER_NAME, __version__)


def log_to_client(message: str, message_type: MessageType = MessageType.Log) -> None:
    try:
        server.window_log_message(
            LogMessageParams(type=message_type, message=f"{SERVER_NAME}: {message}")
        )
    except Exception:
        pass


def path_from_uri(uri: str) -> Path:
    parsed = urlparse(uri)
    if parsed.scheme != "file":
        raise ValueError(f"Only file:// URIs are supported: {uri}")
    return Path(unquote(parsed.path))


def find_project_root(path: Path) -> Path:
    directory = path if path.is_dir() else path.parent
    for candidate in (directory, *directory.parents):
        has_config = any((candidate / filename).exists() for filename in DEFAULT_CONFIG_FILENAMES)
        if has_config or (candidate / ".git").exists():
            return candidate
    return directory


def get_project_root(uri: str) -> Path:
    workspace_root = getattr(server.workspace, "root_path", None)
    if workspace_root:
        return Path(workspace_root)
    return find_project_root(path_from_uri(uri))


def load_rule_text(root: Path, config: AcademicLspConfig) -> str:
    rule_texts: list[str] = []
    for rule_file in config.rules.files:
        path = root / rule_file
        try:
            rule_texts.append(f"# {rule_file}\n\n{path.read_text(encoding='utf-8')}")
        except OSError:
            continue
    return "\n\n".join(rule_texts)


def should_run_llm_on_save(config: AcademicLspConfig) -> bool:
    has_save_llm_diagnostic = any(
        diagnostic.enabled and diagnostic.engine == "llm" and diagnostic.run_on == "save"
        for diagnostic in config.diagnostics.values()
    )
    return has_save_llm_diagnostic and bool(config.llm.model) and bool(config.llm.api_key)


def severity_from_string(severity: str) -> DiagnosticSeverity:
    match severity.lower():
        case "error":
            return DiagnosticSeverity.Error
        case "information" | "info":
            return DiagnosticSeverity.Information
        case "hint":
            return DiagnosticSeverity.Hint
        case _:
            return DiagnosticSeverity.Warning


def range_for_lines(lines: list[str], start_line: int, end_line: int) -> Range:
    end_character = len(lines[end_line]) if lines else 1
    return Range(
        start=Position(line=start_line, character=0),
        end=Position(line=end_line, character=max(end_character, 1)),
    )


def paragraph_ranges(text: str) -> list[Range]:
    lines = text.splitlines()
    ranges: list[Range] = []
    paragraph_start: int | None = None
    paragraph_end: int | None = None

    for line_number, line in enumerate(lines):
        stripped = line.strip()
        is_prose_line = bool(stripped) and not stripped.startswith("#")
        if is_prose_line:
            paragraph_start = line_number if paragraph_start is None else paragraph_start
            paragraph_end = line_number
            continue

        if paragraph_start is not None and paragraph_end is not None:
            ranges.append(range_for_lines(lines, paragraph_start, paragraph_end))
            paragraph_start = None
            paragraph_end = None

    if paragraph_start is not None and paragraph_end is not None:
        ranges.append(range_for_lines(lines, paragraph_start, paragraph_end))

    return ranges


def first_content_range(text: str) -> Range:
    lines = text.splitlines() or [""]
    for line_number, line in enumerate(lines):
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            return range_for_lines(lines, line_number, line_number)
    return range_for_lines(lines, 0, 0)


def range_for_text_match(text: str, needle: str) -> Range | None:
    match = re.search(rf"(?<![A-Za-z0-9-]){re.escape(needle)}(?![A-Za-z0-9-])", text, re.I)
    if match is None:
        return None

    match_index = match.start()
    line = text.count("\n", 0, match_index)
    previous_newline = text.rfind("\n", 0, match_index)
    character = match_index if previous_newline < 0 else match_index - previous_newline - 1
    return Range(
        start=Position(line=line, character=character),
        end=Position(line=line, character=character + len(needle)),
    )


def range_from_hint(text: str, range_hint: str) -> Range:
    paragraph_match = re.search(r"\b(?:paragraph|para|p)\s*(\d+)\b", range_hint, re.I)
    if paragraph_match:
        index = int(paragraph_match.group(1)) - 1
        paragraphs = paragraph_ranges(text)
        if 0 <= index < len(paragraphs):
            return paragraphs[index]

    return first_content_range(text)


def range_from_llm_diagnostic(text: str, diagnostic: LlmDiagnostic) -> Range:
    for quoted_text in re.findall(r"['\"]([^'\"]{2,})['\"]", diagnostic.message):
        matched_range = range_for_text_match(text, quoted_text)
        if matched_range is not None:
            return matched_range

    return range_from_hint(text, diagnostic.range_hint)


def llm_diagnostic_to_lsp(text: str, diagnostic: LlmDiagnostic) -> Diagnostic:
    message = diagnostic.message
    if diagnostic.rule:
        message = f"{message} [{diagnostic.rule}]"
    if diagnostic.range_hint and diagnostic.range_hint != "document":
        message = f"{message} ({diagnostic.range_hint})"

    return Diagnostic(
        range=range_from_llm_diagnostic(text, diagnostic),
        message=message,
        severity=severity_from_string(diagnostic.severity),
        code=diagnostic.code,
        source="academic-lsp:llm",
    )


def collect_llm_diagnostics(uri: str, text: str) -> list[Diagnostic]:
    root = get_project_root(uri)
    config = load_config(root)
    if not should_run_llm_on_save(config):
        log_to_client("skipping LLM diagnostics; no enabled save rule, model, or API key")
        return []

    rules = load_rule_text(root, config)
    if not rules.strip():
        log_to_client(f"skipping LLM diagnostics; no rule files found under {root}")
        return []

    started_at = time.monotonic()
    log_to_client("running LLM diagnostics on save")
    try:
        diagnostics = check_prose_with_llm(text, rules, LiteLlmClient(config.llm))
    except LlmClientError as error:
        log_to_client(f"LLM diagnostics failed: {error}", MessageType.Warning)
        return []
    except Exception as error:
        log_to_client(f"LLM diagnostics failed: {error}", MessageType.Warning)
        return []

    elapsed = time.monotonic() - started_at
    log_to_client(f"LLM diagnostics returned {len(diagnostics)} item(s) in {elapsed:.1f}s")
    return [llm_diagnostic_to_lsp(text, diagnostic) for diagnostic in diagnostics]


def publish_diagnostics(uri: str, text: str, *, include_llm: bool = False) -> None:
    diagnostics = [
        Diagnostic(
            range=Range(
                start=Position(line=item.line, character=item.start_character),
                end=Position(line=item.line, character=item.end_character),
            ),
            message=item.message,
            severity=DiagnosticSeverity.Warning,
            source=item.source,
        )
        for item in find_abbreviation_diagnostics(text)
    ]
    if include_llm:
        diagnostics.extend(collect_llm_diagnostics(uri, text))

    server.text_document_publish_diagnostics(
        PublishDiagnosticsParams(uri=uri, diagnostics=diagnostics)
    )


@server.feature(TEXT_DOCUMENT_DID_OPEN)
def did_open(ls: LanguageServer, params: DidOpenTextDocumentParams) -> None:
    document = params.text_document
    publish_diagnostics(document.uri, document.text)


@server.feature(TEXT_DOCUMENT_DID_CHANGE)
def did_change(ls: LanguageServer, params: DidChangeTextDocumentParams) -> None:
    document = ls.workspace.get_text_document(params.text_document.uri)
    publish_diagnostics(document.uri, document.source)


@server.feature(TEXT_DOCUMENT_DID_SAVE)
def did_save(ls: LanguageServer, params: DidSaveTextDocumentParams) -> None:
    document = ls.workspace.get_text_document(params.text_document.uri)
    publish_diagnostics(document.uri, document.source, include_llm=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Academic prose diagnostics language server")
    parser.add_argument("--version", action="version", version=f"{SERVER_NAME} {__version__}")
    parser.parse_args()
    server.start_io()


if __name__ == "__main__":
    main()
