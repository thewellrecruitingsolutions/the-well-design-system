# Contributing — the-well-design-system

## Working agreements

This repo follows the org-wide working agreements in every repo's `CLAUDE.md`
(PR-only, never push to main; enable auto-merge right after opening; rebase on
`origin/main` before pushing since main requires up-to-date branches). Full rationale
lives in `claude-ops/PARALLEL_WORK.md`.

## Before you open a PR

- One unit of work = one branch = one PR.
- Run `gh pr list` first to avoid duplicating in-flight work.
- This repo is **PUBLIC** — never commit secrets, API keys, tokens, or internal-only
  infrastructure details, even ones that look harmless (see `SECURITY.md`). Supabase
  anon keys are the one exception (designed to be public) but avoid them here anyway
  since this repo has no reason to reference any backend.
- Dashes: em and en dashes are fine everywhere except sales and marketing copy, QFS
  client reply drafts and candidate-facing messages (2026-10-16 dash policy, full text
  in `~/.claude/CLAUDE.md`). This repo holds none of that copy.

## Making a change

- **Token/typography/copy-rule changes** (`README.md`): update the table or rule, and
  check whether the change needs to be manually propagated into the three consuming
  apps' `globals.css` (the scaffolding checklist in `README.md` lists exactly which
  files each app needs updated).
- **Asset changes** (logos, favicons): update source files in the `Brand System/`
  OneDrive folder, then run `sync-brand-assets.ps1` locally to propagate into each
  consuming app's `public/` directory.
- **CI/script changes** (`scripts/`, `.github/workflows/`): keep the scope of each
  script narrow and dependency-free where possible (see `scan_workflow_secret_leaks.py`
  and `check_no_em_dash.py` for the existing style: stdlib-only, self-tested,
  fail-loud). If a workflow touches `.github/workflows/**`, it is scanned by
  `workflow-guard.yml`'s secret-expression-leak check on every PR (a required status
  check).

## CI gates on every PR

- `gitleaks` — literal secret scanning (push + PR).
- `no-em-dash` — kept as a required check name; always passes here (no sales/marketing
  copy in this repo, see the 2026-10-16 dash policy).
- `workflow-guard` — secret-expression leak scan on `.github/workflows/**` (required
  check).
- `review-gate` — advisory Claude-based review (quality/security/fit/conventions
  lenses); posts a severity-classified comment but never blocks merge.

## Ownership

See `CODEOWNERS`. Route questions on brand direction, token changes, or the sync script
to the owner listed there.
