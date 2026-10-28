#!/usr/bin/env python3
"""Fail if a tracked file holds something that must not reach the public repo.

This repository is public. The check fails on:

  1. Tracked files that a repository .gitignore says should be ignored
     (force-added internal docs, local notes, build output).
  2. Paths that are never allowed, even if .gitignore is edited: signing
     material, env files, the Claude Code workspace, Xcode user state.
  3. Secrets: private key blocks and well-known token formats (GitHub, AWS,
     Anthropic, OpenAI, Slack, Google). Binary files are scanned for these too.
  4. Personal details in text files: email addresses other than the project
     contact and documentation placeholders, absolute paths into a home folder
     that is not a known placeholder account, and macOS temp folder paths.
  5. Files larger than 5 MB.

Usage:
  python3 scripts/check-public-hygiene.py            # every tracked file (CI)
  python3 scripts/check-public-hygiene.py --staged   # what the next commit records
  python3 scripts/check-public-hygiene.py FILE...    # only these files on disk

Run --staged before committing: it reads the staged blobs from the index, so
it checks exactly what the commit will publish, not the working tree.

A line that legitimately matches a personal-details rule (a test fixture, a
doc example) can opt out with a "hygiene: allow" comment on that line. Use it
only for placeholder data.
"""

from __future__ import annotations

import fnmatch
import os
import re
import subprocess
import sys
from typing import Callable, Iterable

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

# Emails that may appear: the project's published contact, plus addresses on
# domains reserved for documentation or that never reach a person.
ALLOWED_EMAILS = {"gyorgy@pueev.com"}
ALLOWED_EMAIL_DOMAINS = re.compile(
    r"(^|\.)(example\.(com|org|net)|users\.noreply\.github\.com|noreply\.[a-z.]+|anthropic\.com)$",
    re.IGNORECASE,
)

# Home folder names used as placeholders in tests and docs. "gyorgy" is the
# upstream maintainer's public handle, used in existing fixtures that capture
# real system output.
ALLOWED_HOME_NAMES = {
    "x", "g", "me", "you", "user", "username", "test", "someone", "nobody",
    "other", "shared", "pi", "muse", "devin", "kilo", "dsh", "józsef", "gyorgy",
}

Rule = tuple[str, re.Pattern[str], Callable[[re.Match[str]], bool]]


def always(_: re.Match[str]) -> bool:
    return True


def email_is_personal(match: re.Match[str]) -> bool:
    address = match.group(0)
    domain = address.rsplit("@", 1)[1]
    if address.lower() in ALLOWED_EMAILS or ALLOWED_EMAIL_DOMAINS.search(domain):
        return False
    # Retina asset names like background@2x.png look like addresses.
    return not re.fullmatch(r"\d+x\.(png|jpe?g|webp|gif|tiff?)", domain, re.IGNORECASE)


def home_is_personal(match: re.Match[str]) -> bool:
    return match.group(1).lower() not in ALLOWED_HOME_NAMES


SECRET_RULES: list[Rule] = [
    ("private key block", re.compile(r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----"), always),
    ("GitHub token", re.compile(r"\b(gh[pousr]_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{40,})\b"), always),
    ("AWS access key", re.compile(r"\b(AKIA|ASIA)[0-9A-Z]{16}\b"), always),
    ("Anthropic API key", re.compile(r"\bsk-ant-[A-Za-z0-9_-]{20,}"), always),
    ("OpenAI API key", re.compile(r"\bsk-(proj-)?[A-Za-z0-9]{32,}\b"), always),
    ("Slack token", re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}"), always),
    ("Google API key", re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b"), always),
]

PERSONAL_RULES: list[Rule] = [
    ("email address", re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}"), email_is_personal),
    ("absolute path into a home folder", re.compile(r"/Users/([^/\s\"'`)\]]+)/"), home_is_personal),  # hygiene: allow
    ("macOS temp path", re.compile(r"/private/(tmp|var/folders)/|/var/folders/[^/\s]+/|/tmp/claude-"), always),  # hygiene: allow
    ("Claude Code worktree path", re.compile(r"\.claude/worktrees/"), always),  # hygiene: allow
]


def git(*args: str) -> str:
    return subprocess.run(["git", *args], check=True, capture_output=True, text=True).stdout


def git_bytes(*args: str) -> bytes:
    return subprocess.run(["git", *args], check=True, capture_output=True).stdout


def nul_split(output: str) -> list[str]:
    return [p for p in output.split("\0") if p]


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


def scan_contents(path: str, data: bytes) -> list[str]:
    problems = []
    if b"\0" in data:
        # Binary: personal-details rules would only produce noise, but a key
        # or token is ASCII and must be caught wherever it sits.
        text = data.decode("latin-1")
        for label, pattern, applies in SECRET_RULES:
            for match in pattern.finditer(text):
                if applies(match):
                    problems.append(f"{path}: {label} at byte {match.start()}")
        return problems
    for number, line in enumerate(data.decode("utf-8", errors="replace").splitlines(), start=1):
        if ALLOW_MARKER in line:
            continue
        for label, pattern, applies in SECRET_RULES + PERSONAL_RULES:
            if any(applies(m) for m in pattern.finditer(line)):
                problems.append(f"{path}:{number}: {label}")
    return problems


def check(paths: Iterable[str], read: Callable[[str], bytes | None]) -> list[str]:
    problems: list[str] = []
    for path in paths:
        pattern = path_is_forbidden(path)
        if pattern:
            problems.append(f"{path}: path is never allowed in this repo (rule '{pattern}')")
            continue
        data = read(path)
        if data is None:
            continue
        if len(data) > MAX_BYTES:
            problems.append(f"{path}: larger than {MAX_BYTES // (1024 * 1024)} MB")
            continue
        problems += scan_contents(path, data)
    return problems


def read_disk(path: str) -> bytes | None:
    if not os.path.isfile(path):
        return None  # deleted in the working tree, or a submodule
    with open(path, "rb") as handle:
        return handle.read()


def read_index(path: str) -> bytes | None:
    return git_bytes("show", f":{path}")


def ignored_by_repo(paths: list[str] | None = None) -> list[str]:
    # Only the repository's own .gitignore files: a contributor's
    # .git/info/exclude or global excludes file must not change the result.
    args = ["ls-files", "-z", "-ci", "--exclude-per-directory=.gitignore"]
    return nul_split(git(*args, "--", *paths) if paths else git(*args))


def main(argv: list[str]) -> int:
    args = argv[1:]
    if args == ["--staged"]:
        files = nul_split(git("diff", "--cached", "--name-only", "-z", "--diff-filter=ACMR"))
        problems = [f"{p}: staged but matched by .gitignore" for p in ignored_by_repo(files)] if files else []
        problems += check(files, read_index)
    elif args:
        files = args
        problems = check(files, read_disk)
    else:
        files = nul_split(git("ls-files", "-z"))
        problems = [f"{p}: tracked but matched by .gitignore" for p in ignored_by_repo()]
        problems += check(files, read_disk)

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
