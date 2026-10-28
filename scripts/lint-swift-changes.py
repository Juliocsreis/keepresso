#!/usr/bin/env python3
"""Run `swift format lint` and report only findings on lines this branch changed.

The codebase predates swift-format, so linting whole files would bury a change
under thousands of findings in code it never touched (and rewriting upstream
code would turn every upstream merge into a conflict). This keeps the bar at
"don't add new problems".

Layout diagnostics from swift-format's pretty printer (indentation, line breaks,
spacing, trailing commas) are skipped: they disagree with how this project wraps
code. Line length and trailing whitespace are kept, except that a line carrying
a long string literal may run long (user-facing copy stays on one line so the
localization catalogs can match it). Rule settings live in .swift-format.

Usage:
  python3 scripts/lint-swift-changes.py [BASE]   # BASE defaults to origin/main

Exits nonzero when any changed line has a finding. On GitHub Actions each
finding is also emitted as a workflow annotation on the pull request.
"""
import os
import re
import subprocess
import sys

LAYOUT_RULES = {"Indentation", "AddLines", "RemoveLine", "Spacing", "TrailingComma"}
FINDING = re.compile(r"^(?P<path>.+?):(?P<line>\d+):(?P<col>\d+): (?:warning|error): \[(?P<rule>\w+)\] (?P<msg>.*)$")
STRING = re.compile(r'"(?:[^"\\\n]|\\.)*"')
LONG_STRING = 40
HUNK = re.compile(r"^@@ -\d+(?:,\d+)? \+(?P<start>\d+)(?:,(?P<count>\d+))? @@")


def git(*args: str) -> str:
    return subprocess.run(["git", *args], check=True, capture_output=True, text=True).stdout


def changed_lines(base: str) -> dict:
    """Map each added or modified Swift file to the line numbers it adds."""
    diff = git("diff", "--unified=0", "--diff-filter=AM", "--no-color", f"{base}...HEAD", "--", "*.swift")
    lines: dict = {}
    path = None
    for row in diff.splitlines():
        if row.startswith("+++ "):
            path = row[6:] if row.startswith("+++ b/") else None
        elif path and (m := HUNK.match(row)):
            start = int(m["start"])
            count = int(m["count"]) if m["count"] is not None else 1
            lines.setdefault(path, set()).update(range(start, start + count))
    return {p: ls for p, ls in lines.items() if ls}


def holds_long_string(path: str, line: int) -> bool:
    """Whether a source line carries a string literal of LONG_STRING+ chars."""
    try:
        with open(path, encoding="utf-8") as f:
            text = f.read().splitlines()[line - 1]
    except (OSError, IndexError):
        return False
    return any(len(m.group(0)) >= LONG_STRING for m in STRING.finditer(text))


def main() -> int:
    base = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("BASE_REF", "origin/main")
    targets = changed_lines(base)
    if not targets:
        print(f"No changed Swift lines against {base}.")
        return 0
    run = subprocess.run(
        ["swift", "format", "lint", "--configuration", ".swift-format", *sorted(targets)],
        capture_output=True, text=True,
    )
    findings = []
    for row in (run.stderr + run.stdout).splitlines():
        m = FINDING.match(row)
        if not m or m["rule"] in LAYOUT_RULES:
            continue
        path, line = os.path.relpath(m["path"]), int(m["line"])
        if line not in targets.get(path, ()):
            continue
        if m["rule"] == "LineLength" and holds_long_string(path, line):
            continue
        finding = (path, line, int(m["col"]), m["rule"], m["msg"])
        if finding not in findings:
            findings.append(finding)
    annotate = os.environ.get("GITHUB_ACTIONS") == "true"
    for path, line, col, rule, msg in findings:
        print(f"{path}:{line}:{col}: [{rule}] {msg}")
        if annotate:
            print(f"::warning file={path},line={line},col={col},title=swift-format {rule}::{msg}")
    total = sum(len(v) for v in targets.values())
    print(f"swift-format: {len(findings)} finding(s) on {total} changed line(s) in {len(targets)} file(s).")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
