#!/usr/bin/env python3
"""
check_no_em_dash.py - deterministic guardrail for the house no-dash rule.

The Well bans em dashes and en dashes everywhere (code, comments, docs, emails).
Agents keep reintroducing them, so we catch it here on every PR instead of
relying on the review gate to notice.

Usage:
  # scan explicit files
  python scripts/ci/check_no_em_dash.py path/to/file.py another.tsx

  # scan files changed vs a base ref (CI)
  python scripts/ci/check_no_em_dash.py --changed --base origin/main

  # scan the whole tree (slow, occasional)
  python scripts/ci/check_no_em_dash.py --all

Exits 0 if clean, 1 if any offender is found (prints file:line:col and the
offending character so the fix is obvious). Hyphen "-" is the sanctioned
replacement.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

# Characters we ban: EM DASH and EN DASH plus the two common "smart" variants
# (horizontal bar, figure dash) that sneak in from copy-paste. Keyed by
# codepoint via chr() so this source file itself stays dash-clean.
BANNED = {
    chr(0x2014): "EM DASH (U+2014)",
    chr(0x2013): "EN DASH (U+2013)",
    chr(0x2015): "HORIZONTAL BAR (U+2015)",
    chr(0x2012): "FIGURE DASH (U+2012)",
}

# Only scan text-like files. Binary/asset/lock files are skipped.
SCAN_SUFFIXES = {
    ".py", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".css", ".scss",
    ".html", ".md", ".mdx", ".json", ".yml", ".yaml", ".toml", ".txt",
    ".sh", ".ps1", ".sql", ".env", ".cfg", ".ini",
}

# Never scan these (generated / vendored / huge).
SKIP_DIRS = {
    ".git", "node_modules", ".next", "dist", "build", "__pycache__",
    ".venv", "venv", "coverage", ".turbo", "out",
}

# Never scan these specific files (generated snapshots that may contain
# em-dashes inside regex literals or SQL COMMENT strings we do not own).
SKIP_FILES = {
    "supabase/migrations/00000000000000_baseline.sql",
}


def _is_scannable(path: Path) -> bool:
    if path.suffix.lower() not in SCAN_SUFFIXES:
        return False
    if str(path) in SKIP_FILES or str(path).replace("\\", "/") in SKIP_FILES:
        return False
    return not any(part in SKIP_DIRS for part in path.parts)


def _changed_files(base: str) -> list[Path]:
    try:
        # Merge-base diff so we only flag what THIS branch introduced.
        merge_base = subprocess.run(
            ["git", "merge-base", base, "HEAD"],
            capture_output=True, text=True, check=False,
        ).stdout.strip() or base
        out = subprocess.run(
            ["git", "diff", "--name-only", "--diff-filter=ACMR", merge_base, "HEAD"],
            capture_output=True, text=True, check=True,
        ).stdout
    except subprocess.CalledProcessError as e:
        print(f"git diff failed: {e}", file=sys.stderr)
        sys.exit(2)
    return [Path(p) for p in out.splitlines() if p.strip()]


def _all_files() -> list[Path]:
    return [p for p in Path(".").rglob("*") if p.is_file()]


def scan(paths: list[Path]) -> list[tuple[str, int, int, str]]:
    """Return list of (file, line_no, col, description) offenders."""
    offenders: list[tuple[str, int, int, str]] = []
    for path in paths:
        if not path.is_file() or not _is_scannable(path):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for lineno, line in enumerate(text.splitlines(), 1):
            for col, ch in enumerate(line, 1):
                if ch in BANNED:
                    offenders.append((str(path), lineno, col, BANNED[ch]))
    return offenders


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Ban em/en dashes in tracked text files.")
    ap.add_argument("files", nargs="*", help="explicit files to scan")
    ap.add_argument("--changed", action="store_true", help="scan files changed vs base")
    ap.add_argument("--base", default="origin/main", help="base ref for --changed")
    ap.add_argument("--all", action="store_true", help="scan the whole tree")
    args = ap.parse_args(argv)

    if args.all:
        paths = _all_files()
    elif args.changed:
        paths = _changed_files(args.base)
    elif args.files:
        paths = [Path(f) for f in args.files]
    else:
        ap.error("give files, or --changed, or --all")
        return 2

    offenders = scan(paths)
    if not offenders:
        print("check_no_em_dash: clean (no em/en dashes found).")
        return 0

    print("check_no_em_dash: FAILED. Replace these with a hyphen '-':\n")
    for fpath, lineno, col, desc in offenders:
        print(f"  {fpath}:{lineno}:{col}  {desc}")
    print(f"\n{len(offenders)} offending character(s) found.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
