#!/usr/bin/env python3
"""log_claude_cost.py - record what the Claude Code CLI cost inside one GitHub Actions job.

CANONICAL COPY: thewellrecruitingsolutions/claude-ops .github/scripts/log_claude_cost.py
Identical copies live at the same path in every repo whose workflows run `claude -p`
(they are private repos, so a shared action cannot reach them). Change this file in
claude-ops first, then copy it byte-for-byte; never edit a copy on its own.

Why: Claude Code runs in Actions (review gates, nightly self-healing, audits) bill the
shared ANTHROPIC_API_KEY and nothing recorded what they cost. The Batch API cannot
serve an agentic CLI session, so measuring is the only lever.

How: Claude Code writes a transcript per session (subagents included) under
~/.claude/projects/**/*.jsonl. Every assistant line carries message.model and
message.usage. A message with several content blocks is written as several lines with
the same message id and the same usage, so usage is counted once per message id.
Each message is priced at its model's list price (5-minute cache writes 1.25x input,
1-hour cache writes 2x, cache reads at the model's read multiple) and one row per model
is inserted into ops.llm_spend.

It deliberately does NOT write ops.agent_spend: that ledger feeds fleet_guard's $500/mo
hard stop for the Brain agent fleet, and CLI spend landing there would switch the fleet off.

Never fails the job. Any problem prints a ::warning:: and exits 0.

Usage (last step of the job, after every claude step):
    - name: Log Claude cost
      if: always()
      env:
        SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
        SUPABASE_SERVICE_ROLE_KEY: ${{ secrets.SUPABASE_SERVICE_ROLE_KEY }}
      run: python3 .github/scripts/log_claude_cost.py

Optional env: CLAUDE_COST_LABEL (appended to the workflow name, e.g. a phase name),
CLAUDE_PROJECTS_DIR (defaults to ~/.claude/projects).
"""
import glob
import json
import os
import sys
import urllib.request

# USD per million tokens: (input, output, cache-read multiple of input).
# Verified 2026-10-08 against platform.claude.com/docs/en/about-claude/pricing,
# matching the-well-vault lib/models.ts MODEL_PRICES. Longest prefix wins, so a
# dated id (claude-haiku-4-5-20251001) prices as its family.
PRICES = {
    "claude-fable-5-1": (10.0, 50.0, 0.025),
    "claude-opus-5-5": (4.0, 20.0, 0.05),
    "claude-opus-5": (5.0, 25.0, 0.1),
    "claude-sonnet-5-5": (2.0, 10.0, 0.05),
    "claude-sonnet-5": (2.0, 10.0, 0.1),
    "claude-sonnet-4-6": (3.0, 15.0, 0.1),
    "claude-haiku-5-5": (0.1, 0.5, 0.05),
    "claude-haiku-4-5": (1.0, 5.0, 0.1),
}
# Haiku 5.5 bills a prompt above 100K input tokens at a higher rate.
HAIKU_55_LONG = (100_000, 0.5, 2.5)
# An id with no row is priced at the most expensive non-Fable rate so the ledger
# errs high, never low.
UNKNOWN = PRICES["claude-opus-5"]


def price_for(model):
    best = None
    for prefix in PRICES:
        if model.startswith(prefix) and (best is None or len(prefix) > len(best)):
            best = prefix
    return PRICES[best] if best else UNKNOWN


def message_cost(model, u):
    inp = u.get("input_tokens") or 0
    out = u.get("output_tokens") or 0
    c_read = u.get("cache_read_input_tokens") or 0
    c_write = u.get("cache_creation_input_tokens") or 0
    split = u.get("cache_creation") or {}
    w_1h = split.get("ephemeral_1h_input_tokens") or 0
    w_5m = c_write - w_1h if c_write >= w_1h else c_write
    p_in, p_out, read_mult = price_for(model)
    if model.startswith("claude-haiku-5-5") and inp + c_read + c_write > HAIKU_55_LONG[0]:
        p_in, p_out = HAIKU_55_LONG[1], HAIKU_55_LONG[2]
    usd = (inp * p_in + out * p_out + c_read * p_in * read_mult
           + w_5m * p_in * 1.25 + w_1h * p_in * 2.0) / 1_000_000
    return usd, inp, out, c_read, c_write


def collect(projects_dir):
    seen = set()
    totals = {}
    for path in glob.glob(os.path.join(projects_dir, "**", "*.jsonl"), recursive=True):
        with open(path, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                try:
                    rec = json.loads(line)
                except ValueError:
                    continue
                msg = rec.get("message") if isinstance(rec, dict) else None
                if not isinstance(msg, dict) or rec.get("type") != "assistant":
                    continue
                model, usage = msg.get("model"), msg.get("usage")
                if not model or not isinstance(usage, dict) or model == "<synthetic>":
                    continue
                key = msg.get("id") or rec.get("requestId") or rec.get("uuid")
                if key in seen:
                    continue
                seen.add(key)
                usd, inp, out, c_read, c_write = message_cost(model, usage)
                t = totals.setdefault(model, {"usd": 0.0, "in": 0, "out": 0, "c_read": 0, "c_write": 0, "calls": 0})
                t["usd"] += usd
                t["in"] += inp
                t["out"] += out
                t["c_read"] += c_read
                t["c_write"] += c_write
                t["calls"] += 1
    return totals


def main():
    projects_dir = os.environ.get("CLAUDE_PROJECTS_DIR") or os.path.expanduser("~/.claude/projects")
    totals = collect(projects_dir)
    repo = os.environ.get("GITHUB_REPOSITORY", "local/unknown")
    workflow = os.environ.get("GITHUB_WORKFLOW", "unknown")
    label = os.environ.get("CLAUDE_COST_LABEL", "").strip()
    run_id = os.environ.get("GITHUB_RUN_ID")
    run_url = f"{os.environ.get('GITHUB_SERVER_URL', 'https://github.com')}/{repo}/actions/runs/{run_id}" if run_id else None

    if not totals:
        print("log_claude_cost: no Claude Code usage found in this job (nothing to log).")
        return
    grand = sum(t["usd"] for t in totals.values())
    lines = [f"Claude Code cost this job: ${grand:.4f}"]
    for model, t in sorted(totals.items(), key=lambda kv: -kv[1]["usd"]):
        lines.append(f"  {model}: ${t['usd']:.4f}  calls={t['calls']} in={t['in']} out={t['out']} "
                     f"cache_read={t['c_read']} cache_write={t['c_write']}")
    print("\n".join(lines))
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as fh:
            fh.write("\n```\n" + "\n".join(lines) + "\n```\n")

    url, key = os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        print("::warning::log_claude_cost: SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY not set; cost printed but not stored.")
        return
    rows = [{
        "source": "gha_claude_cli",
        "repo": repo.split("/")[-1],
        "workflow": f"{workflow}:{label}" if label else workflow,
        "run_id": int(run_id) if run_id and run_id.isdigit() else None,
        "run_url": run_url,
        "model": model,
        "calls": t["calls"],
        "tokens_in": t["in"],
        "tokens_out": t["out"],
        "tokens_cache_read": t["c_read"],
        "tokens_cache_write": t["c_write"],
        "est_cost_usd": round(t["usd"], 6),
    } for model, t in totals.items()]
    req = urllib.request.Request(
        url.rstrip("/") + "/rest/v1/llm_spend",
        data=json.dumps(rows).encode(),
        method="POST",
        headers={
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Content-Profile": "ops",
            "Prefer": "return=minimal",
        },
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        print(f"log_claude_cost: stored {len(rows)} row(s) in ops.llm_spend (HTTP {resp.status}).")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # never fail the job over bookkeeping
        print(f"::warning::log_claude_cost failed: {type(exc).__name__}: {exc}")
    sys.exit(0)
