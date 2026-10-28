#!/usr/bin/env python3
"""Report whether a newer Sparkle release exists than the one project.yml pins.

Sparkle is the app's only runtime dependency, and Dependabot can't see it: it
is pinned with `exactVersion` in project.yml (XcodeGen), not in Package.swift.
The weekly sparkle-watch workflow runs this and opens an issue when it's stale.

Usage:
  python3 scripts/check-sparkle-version.py

Reads GH_TOKEN (optional) to avoid the anonymous API rate limit. Prints a
summary and, on GitHub Actions, writes pinned=, latest=, tag= (the release's
tag exactly as published, for links) and newer= to $GITHUB_OUTPUT. Exits nonzero only when it can't determine the versions.
"""
import json
import os
import re
import sys
import urllib.request

PROJECT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "project.yml")
LATEST_URL = "https://api.github.com/repos/sparkle-project/Sparkle/releases/latest"
VERSION = re.compile(r"^\d+(\.\d+)*$")


def pinned_version() -> str:
    """The exactVersion under the Sparkle package in project.yml."""
    in_sparkle = False
    with open(PROJECT, encoding="utf-8") as f:
        for line in f:
            if re.match(r"^  \S", line):
                in_sparkle = line.strip() == "Sparkle:"
            elif in_sparkle and (m := re.match(r'^\s+exactVersion:\s*"?([^"\s]+)"?', line)):
                return m.group(1)
    raise SystemExit("Sparkle exactVersion not found in project.yml")


def latest_release() -> tuple:
    """(version without any "v" prefix, the raw release tag)."""
    request = urllib.request.Request(LATEST_URL, headers={"Accept": "application/vnd.github+json"})
    if token := os.environ.get("GH_TOKEN"):
        request.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(request, timeout=20) as response:
        tag = json.load(response)["tag_name"]
    return tag.removeprefix("v"), tag


def as_tuple(version: str) -> tuple:
    if not VERSION.match(version):
        raise SystemExit(f"unexpected version format: {version!r}")
    return tuple(int(part) for part in version.split("."))


def main() -> int:
    pinned = pinned_version()
    latest, tag = latest_release()
    newer = as_tuple(latest) > as_tuple(pinned)
    print(f"Sparkle pinned {pinned}, latest release {latest}: "
          + ("update available." if newer else "up to date."))
    if output := os.environ.get("GITHUB_OUTPUT"):
        with open(output, "a", encoding="utf-8") as f:
            f.write(f"pinned={pinned}\nlatest={latest}\ntag={tag}\nnewer={'true' if newer else 'false'}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
