"""Local CLI. Examples are included in every subcommand's help."""
import argparse
import json
import os
from pathlib import Path
import sys
import tempfile
from .core import SchemaError, evaluate
from .fixtures import generate
from .report import render


class InputError(ValueError):
    pass


def load_inputs(directory):
    path = Path(directory)
    if not path.is_dir():
        raise InputError(f"MissingInput: {path}: use --input <existing directory>")
    documents = []
    for file in sorted(path.iterdir()):
        if file.is_file() and file.suffix.lower() in (".csv", ".yaml", ".yml", ".jsonl"):
            raise InputError(f"SchemaError: {file}: line 1: unsupported format; use JSON task documents")
    for file in sorted(path.glob("*.json")):
        if file.name == "expectations.json":
            continue
        try:
            doc = json.loads(file.read_text(encoding="utf-8-sig"))
        except json.JSONDecodeError as exc:
            raise InputError(f"ParseError: {file}: line {exc.lineno}: {exc.msg}") from exc
        except UnicodeError as exc:
            raise InputError(f"ParseError: {file}: line 1: expected UTF-8") from exc
        try:
            evaluate([doc])
        except (SchemaError, TypeError) as exc:
            raise InputError(f"SchemaError: {file}: line 1 (document validation): {exc}") from exc
        documents.append(doc)
    try:
        return evaluate(documents)
    except SchemaError as exc:
        raise InputError(f"SchemaError: {path}: line 1 (cross-file validation): {exc}") from exc


def atomic_write(path, content):
    path = Path(path)
    temp = None
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n", dir=path.parent, delete=False) as handle:
            temp = Path(handle.name)
            handle.write(content)
        os.replace(temp, path)
    except OSError as exc:
        raise InputError(f"WriteError: {path}: {exc}") from exc
    finally:
        if temp is not None and temp.exists():
            temp.unlink()


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Identify important unfinished tasks due by an explicit reference date.")
    parser.add_argument("--state", default=".ece/result.json", help="Local result file, default .ece/result.json")
    subs = parser.add_subparsers(dest="command", required=True)
    f = subs.add_parser("fixtures", help="Generate labelled synthetic data", epilog="Example: ece fixtures --out demo")
    f.add_argument("--out", required=True)
    r = subs.add_parser("run", help="Compute and persist closure results", epilog="Example: ece run --input demo")
    r.add_argument("--input", required=True)
    report = subs.add_parser("report", help="Render saved results with provenance", epilog="Example: ece report --format md")
    report.add_argument("--format", choices=("md", "json"), default="md")
    report.add_argument("--out", help="Optional atomic report output path")
    for name, description in (("check", "Check task inputs and display closure counts"), ("plan", "List closure tasks in deterministic due-date and priority order")):
        sub = subs.add_parser(name, help=description, description=description, epilog=f"Example: ece {name} --input demo")
        sub.add_argument("--input", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "fixtures":
            generate(args.out)
            print("SYNTHETIC fixtures generated: 200 records plus five-record starter.")
        elif args.command in ("run", "check", "plan"):
            result = load_inputs(args.input)
            if args.command == "run":
                atomic_write(args.state, json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n")
            print(render(result, "json" if args.command == "check" else "md"), end="")
        else:
            state = Path(args.state)
            if not state.is_file():
                raise InputError(f"MissingInput: {state}: first run ece run --input <dir>")
            try:
                result = json.loads(state.read_text(encoding="utf-8"))
                output = render(result, args.format)
            except (ValueError, KeyError, TypeError) as exc:
                raise InputError(f"StateError: {state}: rerun ece run to rebuild results: {exc}") from exc
            if args.out:
                atomic_write(args.out, output)
            else:
                print(output, end="")
        return 0
    except (InputError, OSError) as exc:
        print(str(exc).replace("\u2014", "-"), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
