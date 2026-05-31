# Basic academic prose rules

A small baseline rule set for editor diagnostics and LLM evals.

The goal is not to enforce style preferences. The goal is to catch concrete prose issues that are useful as inline editor feedback.

## Rule: define-abbreviations

Abbreviations should be defined before first use unless they are common academic or technical abbreviations.

Recognized definition shape for deterministic checks:

```text
Long Form (LF)
```

Good diagnostic:

```text
Define 'LSP' before first use, e.g. 'Long Form (LSP)'.
```

Do not flag:

- abbreviations already defined earlier in the document
- abbreviations defined on the same line
- common terms such as AI, API, PDF, URL, URI, DOI
- roman numerals

## Rule: define-central-terms

Central technical terms should be introduced before they carry the argument.

Flag a span when a specialized concept is doing explanatory work but has not yet been defined or grounded.

Good diagnostic:

```text
Define the central term before using it.
```

Do not flag broad ordinary words, generic academic vocabulary, or terms that are immediately explained.

## Rule: connect-paragraphs

A paragraph should make its connection to the previous paragraph clear.

Flag a paragraph when it introduces a new claim, mechanism, construct, or context without an obvious bridge from the previous span.

Good diagnostic:

```text
Connect this paragraph to the previous claim.
```

Do not flag deliberate section openings or paragraphs that clearly continue the same topic.

## Rule: keep-inline-feedback-short

Diagnostics should fit inline virtual text.

Messages should be short, specific, and actionable.

Prefer:

```text
Define 'LSP' before first use.
```

Avoid:

```text
The abbreviation LSP appears in this paragraph without having been defined previously, which may confuse readers unfamiliar with the terminology.
```

## LLM output contract

LLM diagnostics should return structured JSON using only server-provided span IDs.

```json
{
  "diagnostics": [
    {
      "span_id": "p1",
      "severity": "warning",
      "code": "define-central-terms",
      "message": "Define the central term before using it.",
      "rule": "define-central-terms"
    }
  ]
}
```

The server owns the span-to-range mapping. The model should not return line numbers.
