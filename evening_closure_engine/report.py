"""Deterministic reports with explicit provenance."""
import json


def banner(result):
    sources = result["provenance"]
    if not sources:
        return "Data provenance: no input records or sources."
    return "Data provenance: " + "; ".join(("SYNTHETIC fixture" if p["synthetic"] else "REAL data declared by the input author, not independently verified") + ": " + p["source"] for p in sources)


def render(result, format="md"):
    if format == "json":
        return json.dumps({"provenance_banner": banner(result), **result}, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    lines = ["# Evening Closure Engine", "", banner(result), "", result["honesty"], "", f"Reference date: {result['as_of'] or 'none'}", ""]
    lines += [f"- {key}: {value}" for key, value in result["counts"].items()]
    lines += ["", "## Work needing closure", ""]
    for task in result["tasks"]:
        title = task["title"].replace("\n", " ").replace("\r", " ")
        lines.append(f"- {task['id']}: {title} | {task['priority']} | {task['status']} | due {task['due']}")
    if not result["tasks"]:
        lines.append("No qualifying unfinished work in the supplied inputs.")
    return "\n".join(lines) + "\n"
