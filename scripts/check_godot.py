"""Compile/import the Godot project and smoke-test its battle prototypes.

Usage:
    python scripts/check_godot.py
    python scripts/check_godot.py --godot "C:\\Apps\\Godot_v4.7.2-stable_win64_console.exe"

If Godot is not on PATH, set GODOT_BIN or pass --godot explicitly.
Both steps are required: the first parses/imports resources, the second
creates every playable monster at each supported Resonance rank.
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "godot"
SMOKE_SCRIPT = "res://tests/headless_smoke.gd"
SMOKE_SENTINEL = "GODOT_SMOKE_OK:"
ERROR_LINE = re.compile(
    r"^\s*(?:SCRIPT ERROR:|ERROR:|FATAL:|Parser Error:|Parse Error:)",
    re.IGNORECASE,
)


def error_lines(output: str) -> list[str]:
    """Some Godot parser errors do not set the process exit code."""
    return [line for line in output.splitlines() if ERROR_LINE.match(line)]


def run_check(label: str, command: list[str], *, smoke: bool = False) -> bool:
    print(f"\n=== {label} ===", flush=True)
    print(" ".join(command), flush=True)
    try:
        finished = subprocess.run(
            command,
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=180,
            check=False,
        )
    except subprocess.TimeoutExpired:
        print(f"FAILED: {label} timed out after 180 seconds.", file=sys.stderr)
        return False
    except OSError as exc:
        print(f"FAILED: could not launch Godot: {exc}", file=sys.stderr)
        return False

    output = finished.stdout or ""
    print(output, end="" if output.endswith("\n") else "\n", flush=True)
    problems = error_lines(output)
    if finished.returncode != 0:
        print(f"FAILED: {label} exited with {finished.returncode}.", file=sys.stderr)
        return False
    if problems:
        print(
            f"FAILED: {label} logged {len(problems)} Godot error(s).",
            file=sys.stderr,
        )
        return False
    if smoke and SMOKE_SENTINEL not in output:
        print(
            "FAILED: smoke test did not report completion; "
            "its script may not have executed.",
            file=sys.stderr,
        )
        return False

    print(f"PASS: {label}", flush=True)
    return True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--godot",
        default=os.environ.get("GODOT_BIN", "godot"),
        help="Godot executable name or path (default: GODOT_BIN or godot)",
    )
    args = parser.parse_args(argv)

    binary = shutil.which(args.godot)
    if binary is None:
        print(
            f"Godot executable not found: {args.godot}\n"
            "Install Godot 4.7.2 and add it to PATH, or pass "
            '--godot "C:\\path\\to\\Godot_console.exe".',
            file=sys.stderr,
        )
        return 2

    if not PROJECT.joinpath("project.godot").is_file():
        print("Godot project.godot not found.", file=sys.stderr)
        return 2
    if not PROJECT.joinpath("tests", "headless_smoke.gd").is_file():
        print("Godot headless smoke-test script not found.", file=sys.stderr)
        return 2

    base = [binary, "--headless", "--path", str(PROJECT)]
    if not run_check(
        "Godot editor import and GDScript compilation",
        base + ["--editor", "--import", "--quit"],
    ):
        return 1

    if not run_check(
        "Godot battle monster and Resonance smoke test",
        base + ["--script", SMOKE_SCRIPT],
        smoke=True,
    ):
        return 1

    print("\nGodot headless validation PASSED.", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
