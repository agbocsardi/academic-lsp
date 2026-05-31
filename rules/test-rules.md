# Test rules

This rule pack documents the rules currently exercised by the test suite.

## Rule: undefined-abbreviation

Warn when an all-caps abbreviation appears before it has been defined in the document.

Recognized definition shape:

```text
Long Form (LF)
```

Example diagnostic:

```text
Define 'LSP' before first use, e.g. 'Long Form (LSP)'.
```

Test coverage:

- `tests/test_diagnostics.py::test_warns_when_abbreviation_is_used_before_definition`
- `tests/test_diagnostics.py::test_allows_abbreviation_after_definition`

## Rule: undefined-term

Example LLM diagnostic rule used by the current structured-output parser test.

The LLM should flag prose that uses a central technical term before defining it.

Example diagnostic:

```text
Define the central term before using it.
```

Test coverage:

- `tests/test_llm.py::test_check_prose_with_llm_maps_structured_diagnostics`

## Notes

These are test fixtures, not the full intended writing rule set.
They should stay aligned with tests and be updated when diagnostic codes change.
