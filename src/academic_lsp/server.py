from __future__ import annotations

import argparse

from lsprotocol.types import (
    Diagnostic,
    DiagnosticSeverity,
    DidChangeTextDocumentParams,
    DidOpenTextDocumentParams,
    Position,
    PublishDiagnosticsParams,
    Range,
    TEXT_DOCUMENT_DID_CHANGE,
    TEXT_DOCUMENT_DID_OPEN,
)
from pygls.lsp.server import LanguageServer

from academic_lsp import __version__
from academic_lsp.diagnostics import find_abbreviation_diagnostics

SERVER_NAME = "academic-lsp"

server = LanguageServer(SERVER_NAME, __version__)


def publish_diagnostics(uri: str, text: str) -> None:
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


def main() -> None:
    parser = argparse.ArgumentParser(description="Academic prose diagnostics language server")
    parser.add_argument("--version", action="version", version=f"{SERVER_NAME} {__version__}")
    parser.parse_args()
    server.start_io()


if __name__ == "__main__":
    main()
