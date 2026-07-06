# The Well Design System v1

**Effective:** April 2026 brand refresh
**Last updated:** 2026-05-16
**Source of truth:** `Brand System/` folder on OneDrive (local — not in git)
**Applies to:** The Vault · Content Studio · Sales Engine _(not Talent Plan)_
**Repo visibility:** PUBLIC — do not commit secrets, API keys, or anon JWTs even though Supabase anon keys are designed to be public. The monthly audit's [OPUS_RERUN_QUEUE.md](../OPUS_RERUN_QUEUE.md) QUEUE-002 runs a gitleaks scan against full history.

---

## Brand mood

> Rolex restraint. Private bank authority. Executive search precision.
> Deep, quiet confidence. Every touchpoint should feel edited by someone expensive.

Dark backgrounds. Gold used sparingly. Generous negative space. Never gradients, never bright white, never blue finance clichés.

---

## Colors

| Token | Hex | Role |
|---|---|---|
| `--gold` | `#BE9E44` | Logo, headlines, accents, gold CTAs |
| `--gold-hover` | `#D4AF50` | Gold hover state |
| `--gold-dim` | `#9A7F36` | Subdued gold (borders, secondary accents) |
| `--canvas` | `#161819` | Page background |
| `--canvas-2` | `#1B1F20` | Sidebar / chrome |
| `--card-bg` | `#232729` | Card surface |
| `--card-hover` | `#2A2F31` | Card hover |
| `--teal` | `#2A4C4A` | Primary button, active states |
| `--teal-light` | `#3A6460` | Button border, teal hover |
| `--ivory` | `#F8F5F0` | Primary text |
| `--dim-ivory` | `#C2BDB4` | Secondary text |
| `--warm-gray` | `#8E8378` | Tertiary text |
| `--attr-grey` | `#787870` | Labels, footnotes |
| `--text-muted` | `#9A9690` | Placeholder, ghost UI |
| `--danger` | `#C0524B` | Errors, destructive actions |
| `--color-scheme` | `dark` / `light` | Native UA chrome (date pickers, form controls) — must track the active theme, see rule below |

All tokens are defined as CSS custom properties in each app's `globals.css`.
Tailwind v3 apps also expose them as `well-*` utilities (e.g. `bg-well-gold`, `text-well-ivory`).

---

## Theme-paired tokens (light/dark) — required rule

Apps with a light/dark toggle (Sales Engine's two-skin light "tool" skin;
see `[data-theme="light"]` in that app's `globals.css`) re-declare the SAME
`--token` names inside a `[data-theme="light"]` block so every `var(--…)`
reference flips automatically. **Never hardcode a literal color, or a
literal browser-chrome hint like CSS `colorScheme`, that bypasses this.** A
hardcoded value looks correct in whichever theme the author was looking at
and goes invisible in the other one — this is exactly what broke the
Log-a-call date field (Sales Engine PR #295) and recurred a second time in
the Workboard reschedule field the same week.

Applies to:
- **Foreground/background pairs** — always read `var(--ivory)` /
  `var(--canvas)` etc., never `"#fff"` / `"#000"` or a bare hex.
- **Native UA chrome hints** — `colorScheme` (date/time pickers, form
  controls) must read a theme-aware token, not a literal `"dark"` /
  `"light"`. Add `--color-scheme: dark;` to `:root` and
  `--color-scheme: light;` to `[data-theme="light"]`, then reference it as
  `colorScheme: "var(--color-scheme, dark)"` in the component. Never write
  `colorScheme: "dark"` (or `"light"`) directly unless the surface is
  provably theme-independent (e.g. a client-facing panel that always
  re-asserts `data-theme="dark"` regardless of the app-wide toggle) — and if
  so, comment why.
- **CI enforcement** — any app with a light/dark toggle should carry a
  Playwright suite that renders its interactive surfaces in both themes and
  asserts (a) WCAG AA text contrast (≥4.5:1) via computed-style sampling and
  (b) that every `<input>`'s computed `color-scheme` matches the active
  theme. See `the-well-salesengine/e2e/contrast.spec.ts` for the reference
  implementation — copy its `checkSurfaceContrast` /
  `checkColorSchemeMatchesTheme` helpers into new apps rather than
  reinventing them.

---

## Typography

Three families. Each has exactly one job.

| Family | CSS var | Job | Never use for |
|---|---|---|---|
| **Cinzel** | `--font-display` | App name, page titles, section headers, sidebar label | Body copy, data tables, small sizes |
| **Cormorant Garamond** | `--font-editorial` | Pull quotes, callouts, stat moments | UI controls, labels |
| **Inter** | `--font-body` | Everything else — body, labels, buttons, forms, data | Hero headlines |

### Web loading

**Tailwind v3 apps** (Vault, Sales Engine) — Google Fonts `<link>` in `layout.tsx`:
```html
<link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@400;500;600;700&family=Cormorant+Garamond:ital,wght@0,400;0,500;0,600;1,400;1,500&family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet" />
```

**Tailwind v4 apps** (Content Studio) — `next/font/google` in `layout.tsx`:
```tsx
import { Inter, Cinzel, Cormorant_Garamond } from "next/font/google"
const cinzel    = Cinzel({ variable: "--font-display", subsets: ["latin"], weight: ["400","500","600","700"], display: "swap" })
const cormorant = Cormorant_Garamond({ variable: "--font-editorial", subsets: ["latin"], weight: ["400","500","600"], style: ["normal","italic"], display: "swap" })
```

### Typography utility classes

Available on all apps via `globals.css`:

| Class | Font | Use |
|---|---|---|
| `.serif` | Cinzel | Display headings |
| `.well-heading` | Cinzel, tracked, ALL CAPS | App title, section headers, sidebar labels |
| `.editorial` | Cormorant Garamond italic | Pull quotes, callouts |
| `.label` | Inter, 10px, tracked, ALL CAPS, `--attr-grey` | Data table column headers, field labels |
| `.tnum` | Inter (tabular figures) | Numbers in tables, stats |

### Print / PDF (the-well-brain)
ReportLab scripts use **DM Serif Display** for headlines — the print equivalent of Cinzel. Do **not** change Python/PDF scripts to Cinzel. Cinzel is a web font only.

---

## Logo & favicon assets

**Canonical source:** `Brand System/` folder (OneDrive, not in git)

| Asset | Source folder | Filename in `public/` |
|---|---|---|
| Full logo (mark + wordmark) | `Brand System/04 SVG Files/` | `the-well-logo.svg` |
| Ring mark only | Vault `public/` (hand-crafted SVG) | `the-well-mark.svg` |
| Favicon 16 × 16 | `Brand System/03 Favicons/` | `favicon-16.png` |
| Favicon 32 × 32 | `Brand System/03 Favicons/` | `favicon-32.png` |
| Favicon 64 × 64 | `Brand System/03 Favicons/` | `favicon-64.png` |
| Favicon 128, 256, 512 | `Brand System/03 Favicons/` | `favicon-{n}.png` |
| Apple touch icon | `Brand System/03 Favicons/` | `apple-touch-icon-180.png` |

### Updating assets

When logos or favicons change in `Brand System/`:

```powershell
# Run from the Brand System folder
.\sync-brand-assets.ps1
```

This copies all favicons + SVGs to every app's `public/` folder, commits, and pushes. Vercel auto-deploys from there. The script lives at `Brand System/sync-brand-assets.ps1`.

To add a new app, open the script and add an entry to the `$apps` array.

---

## Favicon wiring

**Tailwind v3 apps** — `<link>` tags in `layout.tsx` `<head>`:
```html
<link rel="icon" type="image/png" sizes="32x32" href="/favicon-32.png" />
<link rel="icon" type="image/png" sizes="16x16" href="/favicon-16.png" />
<link rel="icon" type="image/png" sizes="64x64" href="/favicon-64.png" />
<link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon-180.png" />
```

**Tailwind v4 apps** — `metadata.icons` in `layout.tsx`:
```ts
icons: {
  icon: [
    { url: "/favicon-32.png", sizes: "32x32", type: "image/png" },
    { url: "/favicon-16.png", sizes: "16x16", type: "image/png" },
    { url: "/favicon-64.png", sizes: "64x64", type: "image/png" },
  ],
  apple: [{ url: "/apple-touch-icon-180.png", sizes: "180x180", type: "image/png" }],
},
```

---

## Tailwind token extensions (v3 apps)

`tailwind.config.ts` `theme.extend`:

```ts
colors: {
  well: {
    // bg/deeper/surface are aliases of the canonical --canvas / --canvas-2 / --card-bg tokens (see Colors table)
    bg: "#161819",   deeper: "#1B1F20",  surface: "#232729",
    gold: "#BE9E44", "gold-hover": "#D4AF50", "gold-dim": "#9A7F36",
    teal: "#2A4C4A", "teal-light": "#3A6460",
    ivory: "#F8F5F0", muted: "#C2BDB4", dim: "#8E8378", attr: "#787870",
    danger: "#C0524B",
  },
},
fontFamily: {
  "well-display":   ['"Cinzel"', "Georgia", "serif"],
  "well-editorial": ['"Cormorant Garamond"', "Georgia", "serif"],
  "well-body":      ['"Inter"', "-apple-system", "sans-serif"],
},
letterSpacing: {
  "well-headline": "0.045em",
  "well-label":    "0.18em",
  "well-button":   "0.08em",
},
```

---

## Scaffolding a new app

Checklist when creating a new The Well web app:

- [ ] Copy canonical `:root` token block into `globals.css` (copy from any existing app)
- [ ] Add typography utility classes to `globals.css` (`.serif`, `.well-heading`, `.editorial`, `.label`, `.tnum`)
- [ ] Wire fonts in `layout.tsx` (Google Fonts link or `next/font/google` — see above)
- [ ] Copy `the-well-logo.svg` and `the-well-mark.svg` from Vault `public/` into app `public/`
- [ ] Run `Brand System/sync-brand-assets.ps1` to copy in favicons
- [ ] Add favicon link tags to `layout.tsx`
- [ ] For Tailwind v3: extend `tailwind.config.ts` with `well-*` utilities
- [ ] Add the new app to the `$apps` array in `sync-brand-assets.ps1`
- [ ] Add app to the "Apps using Design System v1" table in this doc

---

## Apps using Design System v1

| App | Repo | Tailwind | Live URL | Status |
|---|---|---|---|---|
| The Vault | [the-well-vault](https://github.com/thewellrecruitingsolutions/the-well-vault) | v3 | vault.thewell.solutions | ✅ Wired |
| Content Studio | [the-well-content-studio](https://github.com/thewellrecruitingsolutions/the-well-content-studio) | v4 | — | ✅ Wired |
| Sales Engine | [the-well-salesengine](https://github.com/thewellrecruitingsolutions/the-well-salesengine) | v3 | sales.thewell.solutions | ✅ Wired |
| Talent Plan | — | — | — | ⏸ Excluded |

---

## Copy rules (applies to all UI copy in all apps)

- No em dashes — use hyphens
- Never use the word "platform"
- No personalization fields (no recipient name, date, presenter)
- Stress communication as a partnership value
- Stats: 44 Days Median Time-to-Fill · 90+ RIA Firms Served
- AUM range: always $200M to $50B+

---

*Source: `Brand System/thewell-brand-reference.md` · Last design system update: May 2026*
