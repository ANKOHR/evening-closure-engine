import json
from evening_closure_engine.core import evaluate
from evening_closure_engine.fixtures import fixture_document, EXPECTED_COUNTS, EXPECTED_IDS
from evening_closure_engine.report import render


def test_report_matches_ground_truth_exact():
    output = json.loads(render(evaluate([fixture_document()]), "json"))
    assert output["counts"] == EXPECTED_COUNTS
    assert sorted(t["id"] for t in output["tasks"]) == EXPECTED_IDS


def test_report_zero_false_positives():
    result = evaluate([fixture_document()])
    assert {t["id"] for t in result["tasks"]} == set(EXPECTED_IDS)


def test_report_carries_provenance_banner():
    doc = fixture_document()
    for fmt in ("md", "json"):
        assert "Data provenance:" in render(evaluate([doc]), fmt)
        assert "SYNTHETIC" in render(evaluate([doc]), fmt)
    doc["synthetic"] = False
    doc["source"] = "Henry entered tasks"
    assert "REAL data declared" in render(evaluate([doc]))


def test_hypothetical_figures_labelled():
    doc = fixture_document(1)
    doc["records"][0]["estimated_minutes"] = 15
    for fmt in ("md", "json"):
        output = render(evaluate([doc]), fmt)
        assert "hypothetical user estimates" in output
        assert "saved are unmeasured" in output


def test_handles_unicode_and_long_inputs():
    doc = fixture_document(1)
    doc["records"][0]["title"] = "学校 café C:\\Users\\henry " + "x" * 9000
    for fmt in ("md", "json"):
        assert doc["records"][0]["title"][:8] in render(evaluate([doc]), fmt)


def test_no_em_dashes_in_outputs():
    for fmt in ("md", "json"):
        assert chr(8212) not in render(evaluate([fixture_document()]), fmt)
