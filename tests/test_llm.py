from academic_lsp.llm import check_prose_with_llm


class FakeClient:
    def chat_json(self, messages: list[dict[str, str]]) -> dict:
        assert messages
        return {
            "diagnostics": [
                {
                    "range_hint": "sentence 1",
                    "severity": "warning",
                    "code": "undefined-term",
                    "message": "Define the central term before using it.",
                    "rule": "Define technical terms.",
                }
            ]
        }


def test_check_prose_with_llm_maps_structured_diagnostics() -> None:
    diagnostics = check_prose_with_llm(
        "Institutional complexity changes everything.",
        "Define technical terms.",
        FakeClient(),
    )

    assert len(diagnostics) == 1
    assert diagnostics[0].range_hint == "sentence 1"
    assert diagnostics[0].code == "undefined-term"
    assert diagnostics[0].message == "Define the central term before using it."
    assert diagnostics[0].rule == "Define technical terms."
