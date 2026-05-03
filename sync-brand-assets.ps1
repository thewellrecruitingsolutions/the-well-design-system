# sync-brand-assets.ps1
# The Well Recruiting Solutions — Brand Asset Sync
#
# Copies canonical favicons and logo SVGs from this Brand System folder
# to every app's public/ directory, then commits and pushes each repo.
#
# Run this any time you update a logo, favicon, or add a new app.
#
# Usage:
#   Open PowerShell, navigate here, then run:
#   .\sync-brand-assets.ps1
#
# To add a new app, add its public/ path to the $apps array below.

$ErrorActionPreference = "Stop"

# ── Paths ────────────────────────────────────────────────────────────────────

$brandRoot  = $PSScriptRoot   # this folder — Brand System/
$faviconsDir = "$brandRoot\03 Favicons"
$svgDir      = "$brandRoot\04 SVG Files"

# SVG source files
$logoSvgSrc  = "$svgDir\the-well-logo-gold-transparent.svg"   # full logo (mark + wordmark)
# Note: the-well-mark.svg (ring mark only) is mastered in the Vault's public/ — not in Brand System.
# The Vault is the canonical source for the mark SVG. Sync copies vault → other apps.
$vaultPublic = "C:\Users\scper\OneDrive - The Well Recruiting Solutions\Documents - Leadership\Cowork Folder\Claude Code\the-well-vault\public"
$markSvgSrc  = "$vaultPublic\the-well-mark.svg"

# ── App targets (add new apps here) ──────────────────────────────────────────

$apps = @(
    @{
        name   = "the-well-vault"
        public = $vaultPublic
        repo   = "C:\Users\scper\OneDrive - The Well Recruiting Solutions\Documents - Leadership\Cowork Folder\Claude Code\the-well-vault"
    },
    @{
        name   = "the-well-content-studio"
        public = "C:\Users\scper\OneDrive - The Well Recruiting Solutions\Documents - Leadership\Cowork Folder\Claude Code\the-well-content-studio\studio\public"
        repo   = "C:\Users\scper\OneDrive - The Well Recruiting Solutions\Documents - Leadership\Cowork Folder\Claude Code\the-well-content-studio"
    },
    @{
        name   = "the-well-salesengine"
        public = "C:\Users\scper\OneDrive - The Well Recruiting Solutions\Documents - Leadership\Cowork Folder\Claude Code\the-well-salesengine-tmp\public"
        repo   = "C:\Users\scper\OneDrive - The Well Recruiting Solutions\Documents - Leadership\Cowork Folder\Claude Code\the-well-salesengine-tmp"
    }
)

# ── Favicon files to sync ─────────────────────────────────────────────────────

$favicons = @(
    "favicon-16.png",
    "favicon-32.png",
    "favicon-64.png",
    "favicon-128.png",
    "favicon-256.png",
    "favicon-512.png",
    "apple-touch-icon-180.png"
)

# ── Sync ──────────────────────────────────────────────────────────────────────

Write-Host ""
Write-Host "The Well — Brand Asset Sync" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host ""

foreach ($app in $apps) {
    Write-Host "→ $($app.name)" -ForegroundColor Yellow

    # Ensure public/ exists
    if (-not (Test-Path $app.public)) {
        New-Item -ItemType Directory -Path $app.public | Out-Null
        Write-Host "  Created public/ directory"
    }

    # Copy favicons
    foreach ($f in $favicons) {
        $src = "$faviconsDir\$f"
        $dst = "$($app.public)\$f"
        if (Test-Path $src) {
            Copy-Item $src $dst -Force
        } else {
            Write-Warning "  Missing favicon source: $src"
        }
    }
    Write-Host "  ✓ Favicons copied ($($favicons.Count) files)"

    # Copy logo SVG (full logo — mark + wordmark)
    if (Test-Path $logoSvgSrc) {
        Copy-Item $logoSvgSrc "$($app.public)\the-well-logo.svg" -Force
        Write-Host "  ✓ the-well-logo.svg copied"
    } else {
        Write-Warning "  Missing logo SVG: $logoSvgSrc"
    }

    # Copy mark SVG (from Vault — canonical ring-mark source)
    if ($app.name -ne "the-well-vault") {
        if (Test-Path $markSvgSrc) {
            Copy-Item $markSvgSrc "$($app.public)\the-well-mark.svg" -Force
            Write-Host "  ✓ the-well-mark.svg copied from Vault"
        } else {
            Write-Warning "  Missing mark SVG source: $markSvgSrc"
        }
    } else {
        Write-Host "  ✓ the-well-mark.svg — Vault is the source, skipping self-copy"
    }

    # Git commit + push
    Push-Location $app.repo
    try {
        $status = git status --porcelain 2>&1
        if ($status) {
            git add public/ | Out-Null
            $changedFiles = ($status | Measure-Object).Count
            git commit -m "chore: sync brand assets from Brand System ($changedFiles files updated)" | Out-Null
            git push origin main | Out-Null
            Write-Host "  ✓ Committed + pushed ($changedFiles changed files)" -ForegroundColor Green
        } else {
            Write-Host "  ✓ No changes — assets already up to date" -ForegroundColor DarkGray
        }
    } catch {
        Write-Warning "  Git error in $($app.name): $_"
    }
    Pop-Location

    Write-Host ""
}

Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "Done. All apps synced." -ForegroundColor Green
Write-Host "Vercel will auto-deploy each repo." -ForegroundColor DarkGray
Write-Host ""
