# AGENTS.md

Rules for AI coding agents (Claude Code, Cursor, Codex, and others) working in
this repository. For the project map, architecture, build commands, and code
conventions, read [`CLAUDE.md`](CLAUDE.md); everything there applies to every
agent, not only Claude.

## This repository is public

Every commit, file, and commit message can be read by anyone. Before you stage
or commit anything, make sure it belongs in a public open-source repo.

### Never commit

- **Secrets**: private keys, signing certificates (`.p12`, `.p8`, `.cer`),
  provisioning profiles, the Sparkle EdDSA private key, API keys and tokens,
  `.env` files. CI and release secrets live in GitHub Actions secrets; local
  ones live in the Keychain or in your shell environment.
- **Personal details**: email addresses (other than the project's published
  contact), personal Apple Developer Team IDs, real names of machines or
  accounts, and absolute paths into someone's home folder or a temp workspace.
  Read these from environment variables (see `KEEPRESSO_TEAM` in
  `scripts/install-local.sh`) or use placeholders like `XXXXXXXXXX` and
  `/Users/g/...`.
- **Internal working files**: anything listed in `.gitignore`, including
  `.claude/`, `docs/ROADMAP.md`, `docs/RELEASING.md`, planning and findings
  notes, and `*.local.md` files. Never `git add -f` an ignored file.
- **Generated or build output**: `Keepresso.xcodeproj/`, `build/`, `.build/`,
  `DerivedData/`, DMGs, `.app` bundles, `xcuserdata/`, `.DS_Store`.

### Check before you commit

Check exactly what the next commit will record (staged content, read from the
index):

```sh
python3 scripts/check-public-hygiene.py --staged
```

CI runs the same script with no arguments, which scans every tracked file.
It fails on force-added ignored files, forbidden paths, private keys and
token formats (in binary files too), email addresses other than the project
contact, home folder paths that are not placeholder accounts, macOS temp
paths, and files over 5 MB. CI only runs after a push, so a leak it catches
is already public: run the staged check first.

If a line is placeholder data that trips a rule (a test fixture path, a doc
example), add a `hygiene: allow` comment on that line. Never use the marker to
let a real value through.

If you find something sensitive that is already committed, stop and tell the
user. Removing it from the working tree does not remove it from history, and
rewriting published history is their decision.

## Commits and pull requests

- Keep commit messages tidy and release-worthy: a short imperative subject and
  a body that explains why. No internal notes, ticket chatter, or local paths.
- Commit or push only when the user asks. Work on a branch, not on `main`.
- Never use em dashes in any prose: docs, comments, commit messages, UI copy.

## Before opening a pull request

```sh
python3 scripts/check-public-hygiene.py
python3 tools/localization/check_all.py
swift build && swift test
```
