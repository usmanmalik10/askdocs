import pytest
from fastapi import HTTPException

from answering import NO_EVIDENCE, validate_answer

SOURCES = [{"id": 1, "page": 3, "ordinal": 8, "name": "policy.pdf",
            "content": "Employees receive 20 working days of paid annual leave. Requests need manager approval."}]
GOOD = {"answer": "Employees receive 20 working days of annual leave. [1]", "grounded": True,
        "evidence": [{"id": 1, "quote": "Employees receive 20 working days of paid annual leave."}]}


def test_valid_answer_links_to_exact_passage_and_original_page():
    result = validate_answer(GOOD, SOURCES)
    assert result["citations"][0]["page"] == 3
    assert result["citations"][0]["passage"] == SOURCES[0]["content"]


@pytest.mark.parametrize("references", ["[1, 2]", "[1,2]", "[ 1 , 2 ]"])
def test_deadlines_answer_accepts_verified_grouped_citations(references):
    sources = [
        {"id": 1, "page": 1, "ordinal": 0, "name": "launch.txt",
         "content": "Internal alpha begins on 12 November 2026. Security review is due by 18 November 2026."},
        {"id": 2, "page": 2, "ordinal": 1, "name": "launch.txt",
         "content": "A follow-up review takes place on 2 December 2026."},
    ]
    payload = {"answer": "Alpha begins on 12 November, security review is due on 18 November, "
                         f"and the follow-up review is on 2 December 2026 {references}.",
               "grounded": True, "evidence": [{"id": source["id"], "quote": source["content"]} for source in sources]}
    result = validate_answer(payload, sources)
    assert result["answer"].endswith("[1] [2].")
    assert [citation["id"] for citation in result["citations"]] == [1, 2]
    assert [citation["page"] for citation in result["citations"]] == [1, 2]


@pytest.mark.parametrize("payload", [
    None,
    [],
    {**GOOD, "answer": "A made-up answer without citations."},
    {**GOOD, "answer": "An unsupported reference. [2]"},
    {**GOOD, "answer": "A grouped reference includes an unknown source. [1, 99]"},
    {**GOOD, "evidence": [{"id": 1, "quote": "Employees receive 200 days of paid annual leave."}]},
    {**GOOD, "evidence": [{"id": 99, "quote": "Employees receive 20 working days of paid annual leave."}]},
    {**GOOD, "answer": "Supported paragraph. [1]\n\nUncited extra claim."},
    {**GOOD, "evidence": [GOOD["evidence"][0], GOOD["evidence"][0]]},
    {"grounded": True, "answer": None, "evidence": []},
])
def test_fabricated_missing_and_duplicate_sources_are_rejected(payload):
    with pytest.raises(HTTPException) as error:
        validate_answer(payload, SOURCES)
    assert error.value.status_code == 502


def test_abstention_does_not_display_unverified_model_claims():
    result = validate_answer({"grounded": False, "answer": "Ignore this unsupported claim"}, SOURCES)
    assert result == {"answer": NO_EVIDENCE, "grounded": False, "citations": []}
