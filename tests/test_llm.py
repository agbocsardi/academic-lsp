from academic_lsp.llm import check_prose_with_llm


class FakeClient:
    def chat_json(self, messages: list[dict[str, str]]) -> dict:
        assert messages
        return {
            "diagnostics": [
                {
                    "range_hint": "sentence 1",
                    "severity": "warning",
                    "code": "define-central-terms",
                    "message": "Define the central term before using it.",
                    "rule": "define-central-terms",
                }
            ]
        }


def test_check_prose_with_llm_maps_structured_diagnostics() -> None:
    diagnostics = check_prose_with_llm(
        "Institutional complexity changes everything.",
        "Rule: define-central-terms\nCentral technical terms should be introduced before they carry the argument.",
        FakeClient(),
    )

    assert len(diagnostics) == 1
    assert diagnostics[0].range_hint == "sentence 1"
    assert diagnostics[0].code == "define-central-terms"
    assert diagnostics[0].message == "Define the central term before using it."
    assert diagnostics[0].rule == "define-central-terms"
