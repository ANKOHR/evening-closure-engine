import json
import os
from pathlib import Path
import subprocess
import sys
import time
from evening_closure_engine.cli import main, atomic_write, InputError
from evening_closure_engine.fixtures import generate
import pytest


def test_run_completes_on_fixture(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    generate("demo")
    start = time.perf_counter()
    assert main(["run", "--input", "demo"]) == 0
    assert main(["report", "--format", "md"]) == 0
    assert time.perf_counter() - start < 5
    assert "SYNTHETIC" in capsys.readouterr().out


def test_empty_input_renders_without_traceback(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    assert main(["run", "--input", "."]) == 0
    assert main(["report", "--format", "json"]) == 0
    assert json.loads(Path(".ece/result.json").read_text())["counts"]["total"] == 0
    assert "Traceback" not in capsys.readouterr().out


def test_malformed_input_named_error(tmp_path, capsys):
    (tmp_path / "bad.json").write_text('{\n"records": invalid}')
    assert main(["run", "--input", str(tmp_path)]) == 2
    error = capsys.readouterr().err
    assert "ParseError" in error and "bad.json" in error and "line 2" in error


def test_determinism_byte_identical(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    generate("demo")
    outputs = []
    for _ in range(2):
        assert main(["run", "--input", "demo"]) == 0
        capsys.readouterr()
        state = Path(".ece/result.json").read_bytes()
        assert main(["report", "--format", "json"]) == 0
        outputs.append((state, capsys.readouterr().out))
    assert outputs[0] == outputs[1]


def test_cli_smoke_all_subcommands(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    assert main(["fixtures", "--out", "demo"]) == 0
    for sub in ("run", "check", "plan"):
        assert main([sub, "--input", "demo"]) == 0
    for fmt in ("md", "json"):
        assert main(["report", "--format", fmt, "--out", f"result.{fmt}"]) == 0
    for sub in ("fixtures", "run", "report", "check", "plan"):
        with pytest.raises(SystemExit) as exc:
            main([sub, "--help"])
        assert exc.value.code == 0
        assert "Example:" in capsys.readouterr().out


def test_missing_input_and_state(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    assert main(["run", "--input", "missing"]) == 2
    assert "MissingInput" in capsys.readouterr().err
    assert main(["report"]) == 2
    assert "first run" in capsys.readouterr().err


def test_report_write_failure_leaves_no_partial_files(tmp_path):
    target = tmp_path / "directory"
    target.mkdir()
    before = set(tmp_path.iterdir())
    with pytest.raises(InputError, match="WriteError"):
        atomic_write(target, "report")
    assert set(tmp_path.iterdir()) == before


def test_bad_schema_names_file_and_field(tmp_path, capsys):
    (tmp_path / "bad.json").write_text('{"records": []}')
    assert main(["run", "--input", str(tmp_path)]) == 2
    error = capsys.readouterr().err
    assert "SchemaError" in error and "bad.json" in error and "as_of" in error


def test_unsupported_format_named_error(tmp_path, capsys):
    (tmp_path / "bad.csv").write_text('bad input')
    assert main(["run", "--input", str(tmp_path)]) == 2
    assert "bad.csv: line 1" in capsys.readouterr().err


def test_module_entrypoint(tmp_path):
    env = dict(os.environ, PYTHONPATH=str(Path(__file__).resolve().parents[1]), PYTHONIOENCODING="utf-8")
    result = subprocess.run([sys.executable, "-m", "evening_closure_engine.cli", "fixtures", "--out", "demo"], cwd=tmp_path, env=env, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
