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
- No em dashes or en dashes in outbound-facing copy (`.md`/`.txt` files under
  content/email/template/outbound-style directories). Plain hyphens only. Enforced by
  `.github/workflows/no-em-dash.yml`.

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
- `no-em-dash` — content lint on changed files.
- `workflow-guard` — secret-expression leak scan on `.github/workflows/**` (required
  check).
- `review-gate` — advisory Claude-based review (quality/security/fit/conventions
  lenses); posts a severity-classified comment but never blocks merge.

## Ownership

See `CODEOWNERS`. Route questions on brand direction, token changes, or the sync script
to the owner listed there.
