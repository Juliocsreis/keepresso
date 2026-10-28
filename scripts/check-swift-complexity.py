#!/usr/bin/env python3
"""Fail when a branch adds a too-complex or too-long Swift function.

Limits match the team's Python rules (ruff C901 and PLR0915): cyclomatic
complexity at most 12, and at most 50 lines of code per function, measured by
lizard. Tests are exempt, as they are there.

It's a ratchet, not a full scan: about 30 existing functions already exceed
these limits, mostly upstream code, and blocking every change that touches them
would force large rewrites of code this fork wants to keep mergeable. A
function fails only if it's over a limit and either is new or got worse on that
metric than on the base branch.

Usage:
  python3 scripts/check-swift-complexity.py [BASE]   # BASE defaults to origin/main

Needs lizard (tools/ci/requirements.txt). On GitHub Actions each finding is
also emitted as an annotation on the pull request.
"""
import os
import subprocess
import sys
from collections import defaultdict

import lizard

MAX_COMPLEXITY = 12
MAX_NLOC = 50
SCOPE = ("Sources/",)


def git(*args: str) -> str:
    return subprocess.run(["git", *args], check=True, capture_output=True, text=True).stdout


def functions(path: str, code: str) -> tuple:
    """Index a file's functions by full signature and by bare name, in file order.

    Signatures repeat (the same method in two types), so each key holds a list
    and base and head entries are paired by position. The by-name index pairs a
    function whose parameter list changed with its old self.
    """
    by_signature, by_name = defaultdict(list), defaultdict(list)
    for fn in lizard.analyze_file.analyze_source_code(path, code).function_list:
        by_signature[fn.long_name].append(fn)
        by_name[fn.name].append(fn)
    return by_signature, by_name


def counterpart(fn, head_by_name: dict, before: tuple):
    """The base version of a head function, or None if it's new."""
    by_signature, by_name = before
    same = [f for f in head_by_name[fn.name] if f.long_name == fn.long_name]
    index = same.index(fn)
    if index < len(by_signature[fn.long_name]):
        return by_signature[fn.long_name][index]
    index = head_by_name[fn.name].index(fn)
    return by_name[fn.name][index] if index < len(by_name[fn.name]) else None


def main() -> int:
    base = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("BASE_REF", "origin/main")
    changed = [
        p for p in git("diff", "--name-only", "--diff-filter=AM", f"{base}...HEAD", "--", "*.swift").split()
        if p.startswith(SCOPE)
    ]
    merge_base = git("merge-base", base, "HEAD").strip()
    findings = []
    for path in changed:
        with open(path, encoding="utf-8") as f:
            head, head_by_name = functions(path, f.read())
        try:
            base_code = git("show", f"{merge_base}:{path}")
        except subprocess.CalledProcessError:
            base_code = ""  # new file
        before = functions(path, base_code)
        for fns in head.values():
            for fn in fns:
                old = counterpart(fn, head_by_name, before)
                problems = []
                if fn.cyclomatic_complexity > MAX_COMPLEXITY and (old is None or fn.cyclomatic_complexity > old.cyclomatic_complexity):
                    was = f", was {old.cyclomatic_complexity}" if old else ""
                    problems.append(f"complexity {fn.cyclomatic_complexity} > {MAX_COMPLEXITY}{was}")
                if fn.nloc > MAX_NLOC and (old is None or fn.nloc > old.nloc):
                    was = f", was {old.nloc}" if old else ""
                    problems.append(f"{fn.nloc} lines > {MAX_NLOC}{was}")
                if problems:
                    findings.append((path, fn.start_line, fn.name, "; ".join(problems)))

    annotate = os.environ.get("GITHUB_ACTIONS") == "true"
    for path, line, name, problem in findings:
        print(f"{path}:{line}: {name}: {problem}")
        if annotate:
            print(f"::error file={path},line={line},title=Function too complex or long::{name}: {problem}")
    print(f"Swift complexity: {len(findings)} finding(s) in {len(changed)} changed file(s) "
          f"(limits: complexity {MAX_COMPLEXITY}, {MAX_NLOC} lines).")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
