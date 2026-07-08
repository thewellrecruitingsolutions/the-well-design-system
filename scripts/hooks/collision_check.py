#!/usr/bin/env python3
"""
Per-prompt collision guardrail (generic, repo-agnostic).

Wired as a UserPromptSubmit hook (.claude/settings.json) so it runs on EVERY
prompt in any Claude Code session working in this repo. It is a deterministic,
READ-ONLY check that surfaces the highest-value parallel-work collision signals
inline before you type another instruction.

Canonical source: thewellrecruitingsolutions/claude-ops, scripts/hooks/collision_check.py.
This file is vendored (copied, not symlinked/submoduled) into each repo because
Claude Code hooks run as a repo-relative command with no cross-repo module
system - every repo that wants the hook needs its own physical copy. If you
improve this script, port the change back to the claude-ops canonical copy and
re-vendor it into the other repos that carry it.

Originally built for the-well-recruit (recruiter-hub-collision-monitor program)
with a hardcoded CORE_HUB file set specific to that repo's shared-shell files.
Generalized here: the CORE_HUB / IGNORE_OVERLAP lists are no longer hardcoded -
they load from an optional `.claude/collision-check.json` config file at the
repo root:

    {
      "core_files": ["components/Shell.tsx", "lib/db.ts"],
      "ignore_overlap": ["docs/BUILD_LOG.md"]
    }

If that file is absent or unreadable, both lists default to empty, and the
hook still gives you same-branch / file-overlap / on-main detection for free.
Core-file-bundling detection (rule below) only activates once a repo owner
opts in by adding `core_files` to the config - there is no default guess at
what counts as "core" for a repo this script doesn't know.

Design constraints (deliberate - do not weaken any of these when editing):
  - READ-ONLY. Only runs `git` reads and `gh pr` reads. Never mutates anything.
  - FAIL-OPEN. Any error (no gh auth, no network, no python dep, bad config
    JSON) -> exit 0, no output/no crash. A guardrail must never block you from
    working.
  - THROTTLED. Results cache in the temp dir for CACHE_TTL seconds so "run on
    every prompt" does not hammer the network. Most prompts hit the warm cache
    (<50ms).
  - QUIET WHEN CLEAN. Prints nothing on a clean check, so it adds no context
    noise. Only speaks up when it finds real collision risk (and then every
    prompt until fixed).

What it detects (current repo only):
  - same-branch / overwrite risk: two open PRs on one branch head.
  - file-overlap: your working changes touch a file another open PR also
    changes (BLOCK if it is a configured core file, WARN otherwise).
  - core-file bundling: your changes mix a configured core file with other
    (feature) files (should be split into a standalone PR) - only checked if
    `core_files` is configured.
  - on-main: uncommitted changes while sitting on main (you should branch
    first).

Exit code is always 0. Stdout (when non-empty) is injected into the session context.
"""

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import time

CACHE_TTL = 180  # seconds; a warm cache short-circuits the network calls
GH_LIMIT = 40    # cap PRs inspected per run

CONFIG_PATH = os.path.join(".claude", "collision-check.json")


def run(args, timeout=15):
    """Run a read-only command, return stdout or None on any failure."""
    try:
        out = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        if out.returncode != 0:
            return None
        return out.stdout
    except Exception:
        return None


def git(args):
    return run(["git", *args])


def norm(paths):
    return {p.strip().replace("\\", "/") for p in paths if p and p.strip()}


def _load_config(repo_root):
    """Load optional .claude/collision-check.json. Defaults to empty sets on
    any absence/error - a repo with no config still gets full same-branch,
    file-overlap, and on-main detection; it just opts out of core-file
    bundling detection until it adds a core_files list."""
    core_files, ignore_overlap = set(), set()
    path = os.path.join(repo_root, CONFIG_PATH)
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        core_files = set(data.get("core_files") or [])
        ignore_overlap = set(data.get("ignore_overlap") or [])
    except FileNotFoundError:
        pass
    except Exception:
        pass  # malformed config must never break the hook (fail-open)
    return core_files, ignore_overlap


def main():
    repo_root = git(["rev-parse", "--show-toplevel"])
    if not repo_root:
        return  # not a git repo / git missing -> stay silent
    repo_root = repo_root.strip()

    branch = git(["rev-parse", "--abbrev-ref", "HEAD"])
    branch = branch.strip() if branch else ""
    if not branch:
        return

    cache_key = hashlib.sha1(f"{repo_root}::{branch}".encode()).hexdigest()[:16]
    cache_path = os.path.join(tempfile.gettempdir(), f"collision_check_{cache_key}.txt")

    # Warm cache: replay last result (may be empty) without touching the network.
    try:
        if os.path.exists(cache_path) and (time.time() - os.path.getmtime(cache_path)) < CACHE_TTL:
            with open(cache_path, "r", encoding="utf-8") as fh:
                cached = fh.read()
            if cached.strip():
                sys.stdout.write(cached)
            return
    except Exception:
        pass

    core_files, ignore_overlap = _load_config(repo_root)

    findings = []  # (severity, text)

    # --- On main with uncommitted changes: branch first. ---
    if branch in ("main", "HEAD"):
        dirty = git(["status", "--porcelain"])
        if dirty and dirty.strip():
            findings.append((
                "WARN",
                "You are on `main` with uncommitted changes. Branch off first "
                "(`git checkout -b feat/<topic>`) - never push to main.",
            ))
        _emit(findings, cache_path)
        return

    # --- Your working changeset (committed vs origin/main + staged + unstaged). ---
    git(["fetch", "origin", "--quiet"])
    changed = set()
    for spec in (["diff", "--name-only", "origin/main...HEAD"],
                 ["diff", "--name-only", "HEAD"],
                 ["diff", "--cached", "--name-only"]):
        out = git(spec)
        if out:
            changed |= norm(out.splitlines())
    changed -= ignore_overlap

    # --- Core-file bundling in your own changeset (only if configured). ---
    if core_files:
        core_touched = changed & core_files
        other_touched = changed - core_files
        if core_touched and other_touched:
            findings.append((
                "WARN",
                "Your changes mix core/shared file(s) "
                f"({', '.join(sorted(core_touched))}) with other files. Consider "
                "splitting the core-file change into its own PR.",
            ))

    # --- Open PRs in this repo (read-only). ---
    prs = _list_open_prs()
    if prs is None:
        # gh unavailable/unauthed -> note it once, still emit any local findings.
        findings.append((
            "INFO",
            "collision-check: PR overlap checks skipped (gh CLI unavailable or not "
            "authenticated). Local checks still ran.",
        ))
        _emit(findings, cache_path)
        return

    # same-branch / overwrite risk
    by_head = {}
    for pr in prs:
        by_head.setdefault(pr.get("headRefName", ""), []).append(pr)
    for head, group in by_head.items():
        if head and len(group) > 1:
            nums = ", ".join(f"#{p['number']}" for p in group)
            findings.append((
                "BLOCK",
                f"Branch `{head}` has {len(group)} open PRs ({nums}). The next push from "
                "either session silently discards the other's commits. Repoint one branch "
                "and queue the later PR behind the earlier.",
            ))

    # file-overlap between your changeset and other open PRs
    if changed:
        for pr in prs:
            if pr.get("headRefName") == branch:
                continue
            pr_files = norm(f.get("path", "") for f in (pr.get("files") or []))
            overlap = (pr_files & changed) - ignore_overlap
            if not overlap:
                continue
            core_ov = overlap & core_files
            sev = "BLOCK" if core_ov else "WARN"
            findings.append((
                sev,
                f"Your changes overlap open PR #{pr['number']} "
                f"({pr.get('headRefName', '?')}) on: {', '.join(sorted(overlap))}. "
                + ("Configured core file - coordinate via a single PR. "
                   if core_ov else "Last merge wins silently - coordinate merge order. "),
            ))

    _emit(findings, cache_path)


def _list_open_prs():
    """Return list of open PRs with files, or None if gh is unusable."""
    raw = run([
        "gh", "pr", "list", "--state", "open",
        "--limit", str(GH_LIMIT),
        "--json", "number,headRefName,author,files",
    ], timeout=25)
    if raw is None:
        return None
    try:
        return json.loads(raw)
    except Exception:
        return None


def _emit(findings, cache_path):
    text = _format(findings)
    try:
        with open(cache_path, "w", encoding="utf-8") as fh:
            fh.write(text)
    except Exception:
        pass
    if text.strip():
        sys.stdout.write(text)


def _format(findings):
    if not findings:
        return ""
    order = {"BLOCK": 0, "WARN": 1, "INFO": 2}
    findings = sorted(findings, key=lambda f: order.get(f[0], 3))
    n = {"BLOCK": 0, "WARN": 0, "INFO": 0}
    for sev, _ in findings:
        n[sev] = n.get(sev, 0) + 1
    lines = [
        "[collision guardrail] "
        f"{n['BLOCK']} BLOCK / {n['WARN']} WARN / {n['INFO']} INFO "
        "(this repo; read-only, cached; see scripts/hooks/collision_check.py):",
    ]
    for sev, text in findings:
        lines.append(f"  {sev}: {text}")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass  # fail-open: never break the prompt
    sys.exit(0)
