import copy
import pytest
from evening_closure_engine.core import evaluate, SchemaError
from evening_closure_engine.fixtures import fixture_document


@pytest.mark.parametrize("field,value", [("estimated_minutes", -1), ("estimated_minutes", True), ("estimated_minutes", 100001), ("created", "2026-10-01"), ("due", "bad"), ("priority", "urgent"), ("title", "x" * 10001), ("amount", -10)])
def test_rejects_adversarial_values(field, value):
    doc = fixture_document(1)
    doc["records"][0][field] = value
    with pytest.raises(SchemaError, match=field):
        evaluate([doc])


def test_duplicate_ids_rejected():
    doc = fixture_document(2)
    doc["records"][1]["id"] = doc["records"][0]["id"]
    with pytest.raises(SchemaError, match="duplicate"):
        evaluate([doc])
    with pytest.raises(SchemaError, match="duplicate"):
        evaluate([fixture_document(1), fixture_document(1)])


def test_corruption_changes_computed_figures():
    doc = fixture_document()
    baseline = evaluate([doc])
    changed = copy.deepcopy(doc)
    changed["records"][0]["status"] = "done"
    result = evaluate([changed])
    assert result["counts"]["needs_closure"] == baseline["counts"]["needs_closure"] - 1
    assert result["counts"]["blocked"] == 9
    assert "task-000" not in [t["id"] for t in result["tasks"]]


def test_future_due_is_valid_but_excluded():
    doc = fixture_document(1)
    doc["records"][0]["due"] = "2099-01-01"
    assert evaluate([doc])["counts"]["needs_closure"] == 0


def test_schema_drift_and_mixed_dates():
    doc = fixture_document(1)
    del doc["records"][0]["due"]
    with pytest.raises(SchemaError, match="due"):
        evaluate([doc])
    a, b = fixture_document(0), fixture_document(0)
    b["as_of"] = "2026-10-01"
    with pytest.raises(SchemaError, match="as_of"):
        evaluate([a, b])
