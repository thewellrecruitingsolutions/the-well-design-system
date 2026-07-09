#!/usr/bin/env python3
"""Fail if a GitHub Actions workflow leaks a ${{ secrets.* }} expression.

Closes chaos-drill finding CHAOS-C05: gitleaks (see .github/workflows/gitleaks.yml)
only matches literal secret VALUES committed to the repo. It is structurally blind
to a workflow step that interpolates a secrets.* EXPRESSION into something that
ends up in logs, files, artifacts, or step outputs -- e.g.:

    run: echo "${{ secrets.SUPABASE_SERVICE_ROLE_KEY }}"

which prints the real secret value to the public/internal Actions log at runtime,
even though no secret literal ever touched git history.

This scanner is deliberately conservative (regex-based, no YAML step-graph
evaluation) so it can run with zero dependencies beyond PyYAML-free stdlib. It
flags any `${{ secrets.<NAME> }}` expression that appears on a line that also
looks like an output/echo/print/write/redirect/artifact-upload operation. A
`${{ secrets.* }}` reference used ONLY as `env:` value (never printed) is safe
and intentionally not flagged -- see ALLOWED patterns below.

Usage: scan_workflow_secret_leaks.py <workflows_dir>
Exit 0: no findings. Exit 1: at least one finding (printed with file:line).
"""
import re
import sys
from pathlib import Path

SECRET_EXPR = re.compile(r"\$\{\{\s*secrets\.[A-Za-z0-9_]+\s*\}\}")

# Lines matching any of these are the "leak sink" shapes we care about.
# Kept intentionally broad; false positives are cheap (an ignore-comment
# escape hatch is provided below), false negatives are the expensive failure
# mode for a secret-leak scanner.
SINK_PATTERNS = [
    re.compile(r"\becho\b", re.IGNORECASE),
    re.compile(r"\bprintf\b", re.IGNORECASE),
    re.compile(r"\bprint\s*\(", re.IGNORECASE),
    re.compile(r"console\.(log|error|warn|info|debug)", re.IGNORECASE),
    re.compile(r">>\s*\$GITHUB_(OUTPUT|ENV|STEP_SUMMARY|PATH)"),
    re.compile(r">\s*\$GITHUB_(OUTPUT|ENV|STEP_SUMMARY|PATH)"),
    re.compile(r"\bset-output\b"),  # deprecated but still seen
    re.compile(r"[>|]{1,2}\s*[\w./\-]+\.(log|txt|json|md|out)\b"),  # redirect to a file
    re.compile(r"\btee\b"),
    re.compile(r"upload-artifact"),
    re.compile(r"actions/cache/save"),
    re.compile(r"\bcat\s*<<"),  # heredoc dumped to stdout
]

# A trailing `# workflow-guard: allow (reason)` comment on the same line opts
# a specific, reviewed line out (e.g. a documented masked-echo pattern).
ALLOW_COMMENT = re.compile(r"#\s*workflow-guard:\s*allow\b")


def scan_file(path: Path) -> list[str]:
    findings = []
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError as e:
        return [f"{path}: could not read ({e})"]

    for lineno, line in enumerate(lines, start=1):
        if not SECRET_EXPR.search(line):
            continue
        if ALLOW_COMMENT.search(line):
            continue
        if any(p.search(line) for p in SINK_PATTERNS):
            findings.append(
                f"{path}:{lineno}: secrets.* expression reaches an output/leak sink: "
                f"{line.strip()}"
            )
    return findings


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: scan_workflow_secret_leaks.py <workflows_dir>", file=sys.stderr)
        return 2

    root = Path(sys.argv[1])
    if not root.is_dir():
        print(f"Not a directory: {root}", file=sys.stderr)
        return 2

    yml_files = sorted(root.rglob("*.yml")) + sorted(root.rglob("*.yaml"))
    all_findings: list[str] = []
    for f in yml_files:
        all_findings.extend(scan_file(f))

    if all_findings:
        print("FAIL: secret-expression leak scan found issues:\n")
        for finding in all_findings:
            print(f"  {finding}")
        print(
            "\nA ${{ secrets.* }} expression is being interpolated into a step that "
            "echoes, prints, writes, or uploads its output. Fix: never print a secret "
            "value; if you need to prove a secret is set, echo a boolean/length instead "
            "(e.g. `[ -n \"$TOKEN\" ] && echo present || echo missing`), and pass secrets "
            "via `env:` to a script rather than substituting them into shell strings. "
            "If this is a reviewed false positive, add a trailing "
            "`# workflow-guard: allow (reason)` comment on that exact line."
        )
        return 1

    print(f"PASS: scanned {len(yml_files)} workflow file(s) under {root}, no secret leaks found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
