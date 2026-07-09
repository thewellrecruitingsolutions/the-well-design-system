# Changelog — the-well-design-system

Format: date, one-line summary. See `git log` for full commit-level history; this file
is a human-readable summary layer added retroactively (2026-07-09) rather than a
strictly-maintained-from-day-one log, so entries before that date are reconstructed from
commit history at a coarser grain.

## 2026-07-09

- Added repo hygiene baseline: `ARCHITECTURE.md`, `CONTRIBUTING.md`, this
  `CHANGELOG.md`, `.editorconfig`, `CODEOWNERS`. (Phase 11, monthly audit.)

## 2026-07-07 and earlier (reconstructed from commit history)

- Added `workflow-guard.yml` secret-expression-leak scan; removed a redundant
  human-review-required gate on workflow-touching PRs in favor of this mechanical
  check (closes chaos-drill finding CHAOS-C05).
- Documented the theme-paired token rule (`--color-scheme` and light/dark CSS custom
  property pairing) after two independent bugs in Sales Engine (Log-a-call date field,
  Workboard reschedule field) were traced to hardcoded, non-theme-aware values.
- Added `review-gate.yml` (advisory Claude-based PR review).
- Added `gitleaks.yml` (secret scanning, standardized across all org repos
  2026-06-22 secrets-centralization capstone).
- Added `no-em-dash.yml` / `scripts/ci/check_no_em_dash.py` (house no-dash rule for
  outbound-facing content).
- Initial design system v1 (April 2026 brand refresh): color tokens, typography
  (Cinzel/Cormorant Garamond/Inter), favicon/logo asset locations,
  `sync-brand-assets.ps1`, scaffolding checklist. Wired into the-well-vault,
  the-well-content-studio, the-well-salesengine.
