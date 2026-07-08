# Security Policy

This repo holds static brand assets (design tokens, fonts, logos, scaffolding
guide). It has no runtime server, no auth, and no user data.

## Reporting a vulnerability

If you find a secret, credential, or sensitive internal detail committed to
this repo (or any other security concern), report it directly to Steve
Perry (internal - steve@emailthewell.com). Do not open a public issue for
anything that looks like a live credential.

## Scope notes

- This repo is PUBLIC. Do not commit secrets, API keys, or internal-only
  infrastructure details here.
- Secret scanning runs on every push and PR via `.github/workflows/gitleaks.yml`.
