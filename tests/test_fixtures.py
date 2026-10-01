import json
from evening_closure_engine.fixtures import generate, EXPECTED_COUNTS, EXPECTED_IDS
from evening_closure_engine.cli import load_inputs


def test_fixtures_labelled_synthetic(tmp_path):
    generate(tmp_path)
    for path in tmp_path.rglob("*.json"):
        assert json.loads(path.read_text())["synthetic"] is True
    assert "<!-- SYNTHETIC" in (tmp_path / "SYNTHETIC.md").read_text()
    assert len(json.loads((tmp_path / "starter/tasks.json").read_text())["records"]) == 5


def test_fixture_ground_truth_matches_hand_computed(tmp_path):
    generate(tmp_path)
    result = load_inputs(tmp_path)
    expected = json.loads((tmp_path / "expectations.json").read_text())
    assert result["counts"] == expected["counts"] == EXPECTED_COUNTS
    assert sorted(t["id"] for t in result["tasks"]) == expected["ids"] == EXPECTED_IDS


def test_expectations_are_never_used_as_computed_results(tmp_path):
    generate(tmp_path)
    before = load_inputs(tmp_path)
    (tmp_path / "expectations.json").write_text('{"synthetic": true, "counts": {"total": 999999}}')
    assert load_inputs(tmp_path) == before


def test_starter_hand_written_ground_truth(tmp_path):
    generate(tmp_path)
    result = load_inputs(tmp_path / "starter")
    assert result["counts"] == {"total": 5, "needs_closure": 2, "overdue": 1, "due_today": 1, "blocked": 1}
    assert {t["id"] for t in result["tasks"]} == {"starter-1", "starter-5"}
