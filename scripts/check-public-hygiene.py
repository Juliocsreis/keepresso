#!/usr/bin/env python3
"""Fail if a tracked file holds something that must not reach the public repo.

This repository is public. The check scans only what git tracks (that is all
that can be pushed) and fails on:

  1. Tracked files that .gitignore says should be ignored (force-added
     internal docs, local notes, build output).
  2. Paths that are never allowed, even if .gitignore is edited: signing
     material, env files, the Claude Code workspace, Xcode user state.
  3. Secrets in file contents: private key blocks and well-known token
     formats (GitHub, AWS, Anthropic, OpenAI, Slack, Google).
  4. Personal identifiers: Apple ID email domains and absolute paths into a
     real home folder or a temp workspace.
  5. Files larger than 5 MB.

Usage:
  python3 scripts/check-public-hygiene.py            # every tracked file
  python3 scripts/check-public-hygiene.py FILE...    # only these files

A line that legitimately matches a content rule (a test fixture, a doc
example) can opt out by containing the marker "hygiene: allow" in a comment.
Use it sparingly and only for placeholder data.
"""

from __future__ import annotations

import fnmatch
import os
import re
import subprocess
import sys

ALLOW_MARKER = "hygiene: allow"
MAX_BYTES = 5 * 1024 * 1024

# Paths that must never be tracked. Matched against the repo-relative path
# with fnmatch; a pattern ending in "/" matches anything under that folder.
FORBIDDEN_PATHS = [
    ".claude/",
    ".env",
    ".env.*",
    "*.p12",
    "*.p8",
    "*.cer",
    "*.mobileprovision",
    "*.provisionprofile",
    "*.keychain",
    "*.keychain-db",
    "*_priv.pem",
    "*private_key*",
    "sparkle_private_key*",
    "eddsa_priv*",
    "ExportOptions.local.plist",
    "*.local.md",
    "*.xcuserstate",
    "xcuserdata/",
    "*.xcodeproj/",
    ".DS_Store",
    "docs/ROADMAP.md",
    "docs/RELEASING.md",
]

SECRET_PATTERNS = [
    ("private key block", re.compile(r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----")),
    ("GitHub token", re.compile(r"\b(gh[pousr]_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{40,})\b")),
    ("AWS access key", re.compile(r"\b(AKIA|ASIA)[0-9A-Z]{16}\b")),
    ("Anthropic API key", re.compile(r"\bsk-ant-[A-Za-z0-9_-]{20,}")),
    ("OpenAI API key", re.compile(r"\bsk-(proj-)?[A-Za-z0-9]{32,}\b")),
    ("Slack token", re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}")),
    ("Google API key", re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b")),
]

PERSONAL_PATTERNS = [
    ("Apple ID email", re.compile(r"[A-Za-z0-9._%+-]+@(icloud|me|mac)\.com\b", re.IGNORECASE)),
    (
        "absolute path into a home folder",
        re.compile(r"/Users/[^/\s\"'`]+/(Developer|Desktop|Documents|Downloads|Projects|Library/CloudStorage)/"),
    ),
    ("macOS temp path", re.compile(r"/private/(tmp|var/folders)/")),
    ("Claude Code worktree path", re.compile(r"\.claude/worktrees/")),  # hygiene: allow
]

CONTENT_RULES = SECRET_PATTERNS + PERSONAL_PATTERNS


def git(*args: str) -> str:
    return subprocess.run(["git", *args], check=True, capture_output=True, text=True).stdout


def tracked_files() -> list[str]:
    return [p for p in git("ls-files", "-z").split("\0") if p]


def path_is_forbidden(path: str) -> str | None:
    parts = path.split("/")
    for pattern in FORBIDDEN_PATHS:
        if pattern.endswith("/"):
            folder = pattern.rstrip("/")
            # Match the folder at any depth, including glob folders like *.xcodeproj.
            if any(fnmatch.fnmatch(part, folder) for part in parts[:-1]):
                return pattern
        elif fnmatch.fnmatch(parts[-1], pattern) or fnmatch.fnmatch(path, pattern):
            return pattern
    return None


def scan_contents(path: str) -> list[str]:
    try:
        with open(path, "rb") as handle:
            data = handle.read()
    except OSError as error:
        return [f"{path}: could not read ({error})"]
    if b"\0" in data[:8192]:
        return []  # binary file, skip content rules
    problems = []
    for number, line in enumerate(data.decode("utf-8", errors="replace").splitlines(), start=1):
        if ALLOW_MARKER in line:
            continue
        for label, pattern in CONTENT_RULES:
            if pattern.search(line):
                problems.append(f"{path}:{number}: {label}")
    return problems


def main(argv: list[str]) -> int:
    explicit = argv[1:]
    files = explicit or tracked_files()
    problems: list[str] = []

    if not explicit:
        ignored = [p for p in git("ls-files", "-z", "-ci", "--exclude-standard").split("\0") if p]
        problems += [f"{p}: tracked but matched by .gitignore" for p in ignored]

    for path in files:
        if not os.path.isfile(path):
            continue  # deleted in the working tree, or a submodule
        pattern = path_is_forbidden(path)
        if pattern:
            problems.append(f"{path}: path is never allowed in this repo (rule '{pattern}')")
            continue
        if os.path.getsize(path) > MAX_BYTES:
            problems.append(f"{path}: larger than {MAX_BYTES // (1024 * 1024)} MB")
            continue
        problems += scan_contents(path)

    if problems:
        print("Public repo hygiene check failed:\n")
        for problem in problems:
            print(f"  {problem}")
        print(
            "\nThis repo is public. Move secrets and personal details into env vars"
            " or git-ignored local files. For placeholder data in tests or docs,"
            f" add a '{ALLOW_MARKER}' comment on that line."
        )
        return 1

    print(f"Public repo hygiene check passed ({len(files)} files).")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
