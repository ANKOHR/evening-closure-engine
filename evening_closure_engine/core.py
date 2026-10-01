"""Pure validation and closure logic. No predicted or estimated savings."""
from datetime import date


class SchemaError(ValueError):
    """An explicit input violates the task schema."""


def validate_document(doc):
    def fail(field, message):
        raise SchemaError(f"{field}: {message}")
    if not isinstance(doc, dict):
        fail("document", "expected object")
    required = {"synthetic", "source", "as_of", "records"}
    if set(doc) != required:
        fail("document", f"missing or unknown fields: {sorted(set(doc) ^ required)}")
    if type(doc["synthetic"]) is not bool:
        fail("synthetic", "expected boolean")
    if not isinstance(doc["source"], str) or not doc["source"].strip() or len(doc["source"]) > 10000:
        fail("source", "expected nonempty string up to 10000 characters")
    def day(value, field):
        try:
            if not isinstance(value, str) or len(value) != 10:
                raise ValueError()
            return date.fromisoformat(value)
        except ValueError:
            fail(field, "expected ISO date YYYY-MM-DD")
    as_of = day(doc["as_of"], "as_of")
    if not isinstance(doc["records"], list):
        fail("records", "expected array")
    seen = set()
    for i, task in enumerate(doc["records"]):
        prefix = f"records[{i}]"
        if not isinstance(task, dict):
            fail(prefix, "expected object")
        fields = {"id", "title", "priority", "status", "due"}
        optional = {"created", "estimated_minutes"}
        if not fields <= set(task) or set(task) - fields - optional:
            fail(prefix, f"missing or unknown fields: {sorted((fields - set(task)) | (set(task) - fields - optional))}")
        for field in ("id", "title"):
            value = task[field]
            if not isinstance(value, str) or not value.strip() or len(value) > 10000 or "\u2014" in value:
                fail(f"{prefix}.{field}", "expected nonempty string up to 10000 characters without em dash")
        if task["id"] in seen:
            fail(f"{prefix}.id", "duplicate id")
        seen.add(task["id"])
        if task["priority"] not in ("low", "normal", "high", "critical"):
            fail(f"{prefix}.priority", "expected low, normal, high or critical")
        if task["status"] not in ("open", "in_progress", "blocked", "done", "cancelled"):
            fail(f"{prefix}.status", "invalid status")
        day(task["due"], f"{prefix}.due")
        if "created" in task and day(task["created"], f"{prefix}.created") > as_of:
            fail(f"{prefix}.created", "future creation date relative to as_of")
        if "estimated_minutes" in task:
            value = task["estimated_minutes"]
            if type(value) is not int or not 0 <= value <= 100000:
                fail(f"{prefix}.estimated_minutes", "expected integer between 0 and 100000; hypothetical user estimate")
    if "\u2014" in doc["source"]:
        fail("source", "em dash is not supported")
    return doc


def evaluate(documents):
    """Count exactly the supplied records, with no discovery of missing work."""
    all_tasks = []
    provenance = []
    seen = set()
    dates = set()
    for doc in documents:
        validate_document(doc)
        dates.add(doc["as_of"])
        provenance.append({"source": doc["source"], "synthetic": doc["synthetic"]})
        for task in doc["records"]:
            if task["id"] in seen:
                raise SchemaError(f"id: duplicate id across files: {task['id']}")
            seen.add(task["id"])
            all_tasks.append(task)
    if len(dates) > 1:
        raise SchemaError("as_of: input files must use the same reference date")
    as_of = next(iter(dates), None)
    selected = [t for t in all_tasks if t["priority"] in ("high", "critical") and t["status"] in ("open", "in_progress", "blocked") and t["due"] <= as_of]
    selected.sort(key=lambda t: (t["due"], 0 if t["priority"] == "critical" else 1, t["id"]))
    overdue = sum(t["due"] < as_of for t in selected)
    return {"as_of": as_of, "provenance": sorted(provenance, key=lambda p: (p["source"], p["synthetic"])), "counts": {"total": len(all_tasks), "needs_closure": len(selected), "overdue": overdue, "due_today": len(selected) - overdue, "blocked": sum(t["status"] == "blocked" for t in selected)}, "tasks": selected, "honesty": "Computed from explicit inputs only. Estimated minutes are hypothetical user estimates. Time and money saved are unmeasured and are not reported."}
