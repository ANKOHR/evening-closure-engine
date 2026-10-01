"""Labelled synthetic fixtures. No randomness; seed is not applicable."""
import json
from pathlib import Path

# Hand-computed blocks: 20 overdue + 20 today; 40 done + 40 low + 40 future + 40 cancelled.
EXPECTED_COUNTS = {"total": 200, "needs_closure": 40, "overdue": 20, "due_today": 20, "blocked": 10}
EXPECTED_IDS = [f"task-{i:03d}" for i in range(40)]


def fixture_document(count=200):
    records = []
    for i in range(count):
        block = i // 40
        records.append({"id": f"task-{i:03d}", "title": f"Synthetic task {i:03d}", "priority": "low" if block == 2 else "high", "status": "done" if block == 1 else "cancelled" if block == 4 else "blocked" if i < 10 else "open", "due": "2026-10-01" if block == 3 else "2026-09-29" if i < 20 else "2026-09-30"})
    return {"synthetic": True, "source": "Labelled synthetic fixture, not Henry's real tasks", "as_of": "2026-09-30", "records": records}


def generate(out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    for name, doc in (("tasks.json", fixture_document()), ("expectations.json", {"synthetic": True, "label": "SYNTHETIC hand-computed ground truth", "counts": EXPECTED_COUNTS, "ids": EXPECTED_IDS})):
        (out / name).write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    starter = out / "starter"
    starter.mkdir(exist_ok=True)
    # Five explicitly written cases: overdue, done, low priority, future, due today.
    doc = {"synthetic": True, "source": "SYNTHETIC five-record starter", "as_of": "2026-09-30", "records": [
        {"id": "starter-1", "title": "Submit school assignment", "priority": "high", "status": "open", "due": "2026-09-29"},
        {"id": "starter-2", "title": "Send application", "priority": "critical", "status": "done", "due": "2026-09-30"},
        {"id": "starter-3", "title": "Tidy notes", "priority": "low", "status": "open", "due": "2026-09-30"},
        {"id": "starter-4", "title": "Prepare next week outreach", "priority": "high", "status": "open", "due": "2026-10-02"},
        {"id": "starter-5", "title": "Finish build review", "priority": "critical", "status": "blocked", "due": "2026-09-30"}
    ]}
    (starter / "tasks.json").write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    (out / "SYNTHETIC.md").write_text("<!-- SYNTHETIC fixture label -->\nAll data here is synthetic. JSON files carry synthetic: true; JSON does not allow header comments.\n", encoding="utf-8")
