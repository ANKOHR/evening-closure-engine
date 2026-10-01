# Evening Closure Engine

Identify unfinished important work before the day ends, using explicit local task records. Built for Henry's school, outreach, builds and applications.

Hypothesis: deterministic closure checks can be trusted when every behavior is tested against planted ground truth. The synthetic acceptance outcome is validated locally; daily usefulness remains unmeasured.

## Quickstart

Python 3.10 or newer and setuptools are required. There are no runtime dependencies, model calls, network calls, database servers or GPU packages. Install from local files:

```powershell
$env:PIP_DISABLE_PIP_VERSION_CHECK = "1"
python -m pip install --no-deps --no-build-isolation -e .
ece fixtures --out demo
ece run --input demo
ece report --format md
python -m pytest -q
```

If the Python user Scripts directory is absent from PATH, add the directory reported by pip to your shell PATH, or use `python -m evening_closure_engine.cli` in place of `ece`. Pytest is a development dependency and must already be installed for offline testing.

The starter input is a hand-written set of five cases:

```powershell
ece run --input demo/starter
ece report --format json
```

It selects starter-1 and starter-5: one overdue, one due today, one blocked. Run with `--input demo` again to restore the 200-record report.

## Input format reference

Use UTF-8 JSON documents directly inside one input directory. Files are processed in filename order, without recursion. `expectations.json` is reserved test metadata and never used to calculate results. CSV, YAML and JSONL files produce a named unsupported-format schema error; convert them to the documented JSON schema. Other extensions are documentation and ignored.

```json
{
  "synthetic": false,
  "source": "Henry's tasks entered by Henry",
  "as_of": "2026-09-30",
  "records": [
    {
      "id": "school-1",
      "title": "Submit assignment",
      "priority": "high",
      "status": "open",
      "due": "2026-09-30"
    }
  ]
}
```

This example is illustrative, not shipped real data or measured work. Set `synthetic: false` only for real data you enter. Provenance is a declaration by the input author, not something the engine independently verifies.

All four document fields are required; unknown fields are rejected. `as_of` is the explicit reference date, never the computer clock. All files must share it. An empty directory produces zero counts and no reference date.

Each record requires `id`, `title`, `priority`, `status`, `due`. IDs must be unique across all files. IDs, titles and source strings must be nonempty, at most 10000 characters, and contain no em dash. Unicode, newlines and Windows path strings are supported; escape backslashes in JSON normally. Priorities: low, normal, high, critical. Statuses: open, in_progress, blocked, done, cancelled. Dates must be ISO YYYY-MM-DD calendar dates.

Optional `created` must not be later than `as_of`. Future due dates are valid and excluded until due. Optional `estimated_minutes` is a hypothetical user estimate, an integer from 0 through 100000; negative values, booleans and floats are rejected. Money fields are not supported; unknown amounts are rejected rather than silently counted. No record is silently dropped due to validation failure.

Closure means high or critical priority, an unfinished status (open, in_progress or blocked), and due on or before `as_of`. Overdue means strictly before `as_of`; due_today means equal to it. Blocked counts only qualifying closure tasks. Total counts every valid input record. Overdue plus due_today equals needs_closure. These rules can miss important undated or future work; such work is outside the current schema and decision rule.

## Subcommand catalogue

Every subcommand provides `--help` and examples.

| Command | Purpose | Example |
| --- | --- | --- |
| fixtures | Write labelled 200-record fixtures and five-record starter | `ece fixtures --out demo` |
| run | Parse, validate, compute, save and display closure report | `ece run --input demo` |
| report | Render the last saved computation | `ece report --format json --out closure.json` |
| check | Validate inputs and print computed counts and provenance as JSON | `ece check --input demo` |
| plan | Display qualifying tasks ordered by due date, critical before high, then ID | `ece plan --input demo` |

`ece --state work/result.json run --input work` overrides the local state path. Use the same global option before `report`. Default state is `.ece/result.json` relative to the current directory. Reports are snapshots of the most recent run; rerun after input changes. `check` and `plan` do not replace the saved result. All output is deterministic for identical inputs, including serialization and order. No random generator is used; seed is not applicable. Paths and measured benchmark times are environment-specific evidence, not deterministic domain output.

## Architecture

```text
local JSON -> cli.load_inputs -> core.validate_document
                             -> core.evaluate -> local .ece/result.json
                                              -> report.render -> stdout / atomic report file
fixtures.generate -> labelled synthetic JSON + independent expectations
```

Core validation and evaluation are pure and perform no I/O. The CLI owns all file access. Reports retain source declarations, reference date, counts and each selected task, so figures are traceable to task IDs. Plan is a deterministic list for Henry to review, not a prediction or a schedule optimizer.

## Honesty boundary

The engine only computes from supplied records. It does not discover tasks, infer importance, predict completion or measure time or money saved. Savings are unmeasured and are not reported. Optional estimated minutes remain labelled hypothetical user estimates on every report surface; they are not aggregated into claimed savings. All real source labels are declared by the author. There is no bundled personal data. Real trial results should be recorded privately, not committed here.

## Fixture labelling and acceptance evidence

All fixture JSON files carry `synthetic: true`. JSON does not permit header comments, so `SYNTHETIC.md` supplies an explicit header comment and each JSON source or label carries the synthetic designation. Every generated report has a provenance banner. The five-record starter is also synthetic.

The independent hand-computed 200-record truth is: first 20 overdue, next 20 due today; 40 done, 40 low priority, 40 future and 40 cancelled excluded. First 10 qualifying records are blocked. Expected counts: total 200, needs_closure 40, overdue 20, due_today 20, blocked 10. Expected IDs are task-000 through task-039. Tests compare the full selected ID set, proving zero false positives and all planted cases found, and verify counts exactly. Mutating a qualifying task to done changes the computed figures. Expectations never drive the engine.

`benchmark.json` records measured local runtime on synthetic data. `demo-report.md` is the actual generated synthetic report. These are not savings measurements. Test coverage includes malformed input, schema drift, missing files, future dates, invalid estimates, duplicate IDs, Unicode, long strings, deterministic bytes, empty inputs and atomic report write failures.

## Failure modes

ParseError identifies the malformed JSON filename and actual parser line. SchemaError identifies file, offending field and document-validation line 1 (semantic errors have no parser line). MissingInput gives a usage hint. StateError instructs rebuilding a corrupted result file. WriteError names the destination; report writes use a temporary file in the destination directory and atomic replacement, removing temporary files on failure. Failures return exit code 2, without application tracebacks. argparse usage errors also return 2. Fixture generation is for a dedicated directory and overwrites its generated files; it is not an atomic multi-file transaction. The CLI does not protect against concurrent runs replacing the same state file.

## Two-week evidence-based improvement hook and verdict

Start the window only when Henry begins real use; record start and end dates privately. For each evening, independently hand-check the same task source, record expected and reported IDs, false positives, false negatives and whether the tool was used. Primary metric: task classification error rate = (false positives + false negatives) / total records in the hand-checked sample. A zero-record sample is unmeasurable, not 0 percent accuracy. Also record evenings used out of 14. Do not report time saved without a measured baseline.

After 14 days, if measured error exceeds 10 percent or the tool was not actually used, record the finding and fix the top failure cause or kill with a written reason. Record exactly one improvement chosen from that evidence, rerun the hand-check, and preserve before/after figures.

Verdict is PENDING: the two-week evidence window has not happened. No real-use accuracy, daily adoption or revenue is claimed. At the window end, write the dated evidence and reason in a private trial record: expand if daily use or revenue is earned; integrate if it heavily overlaps a sibling tool; commercialise if a buyer would pay as-is; maintain as portfolio evidence otherwise; kill if never used or unable to meet acceptance criteria. The build passes synthetic acceptance; that alone does not establish real usefulness.

Publishing is handled by a separate verification step. This build makes no external network calls and does not publish to GitHub.
