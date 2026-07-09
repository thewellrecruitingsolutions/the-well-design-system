# Architecture — the-well-design-system

This repo is not an application. It has no runtime server, no build step, no package
manager manifest, and no deploy target of its own. It is a documentation + static-asset
source of truth that three other Next.js apps consume by copy-paste / manual sync, not by
importing a package.

## What lives here

- `README.md` — the actual design system: CSS custom-property tokens (color, type,
  spacing), typography rules, favicon/logo asset locations, theme-pairing rules, and a
  scaffolding checklist for wiring a new app to this system.
- `sync-brand-assets.ps1` — a PowerShell script, run manually by a human from a local
  `Brand System/` OneDrive folder (not checked into this repo). Copies canonical
  favicons/logo SVGs into each consuming app's `public/` directory, then commits and
  pushes directly to that app's own repo. This is the only distribution mechanism; there
  is no npm package and no CI-driven publish step.
- `scripts/ci/check_no_em_dash.py` — CI lint enforcing the house no-em-dash rule on
  outbound-facing content directories.
- `scripts/security/scan_workflow_secret_leaks.py` — CI scanner catching
  `${{ secrets.* }}` expressions that would leak into logs/artifacts (complements
  gitleaks, which only catches literal committed secret values).
- `scripts/hooks/collision_check.py` — a vendored (copied, not symlinked) Claude Code
  `UserPromptSubmit` hook; canonical source is `claude-ops/scripts/hooks/collision_check.py`.
- `.github/workflows/` — `gitleaks.yml` (secret scan), `no-em-dash.yml` (content lint),
  `review-gate.yml` (advisory Claude-based PR review, never blocks merge),
  `workflow-guard.yml` (secret-expression leak scan, a required check).

## Consumers

The-well-vault, the-well-content-studio, and the-well-salesengine each re-declare this
repo's CSS custom properties in their own `globals.css` (Tailwind v3 apps also expose
them as `well-*` Tailwind utilities). Talent Plan is explicitly excluded. There is no
shared npm package, so a change here has zero effect on a consuming app until either (a)
a human runs `sync-brand-assets.ps1` (for logo/favicon assets), or (b) a human manually
copies the updated token/typography values into that app's `globals.css` per the
scaffolding checklist in `README.md`.

## Why so little automation

This repo is intentionally low-complexity: no build, no test suite, no runtime. The
existing CI (gitleaks, no-em-dash, workflow-guard, advisory review-gate) matches that —
lint/scan gates appropriate to a docs-and-assets repo, not a full application pipeline.
See `SELF_PENTEST_the-well-design-system.md` for the security posture and rationale for
why a full STRIDE threat model was skipped here.
