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
$markSvgSrc  = "$svgDir\the-well-mark-gold.svg"               # ring mark only (no wordmark)
$vaultPublic = "C:\Users\scper\OneDrive - The Well Recruiting Solutions\Documents - Leadership\Cowork Folder\Claude Code\the-well-vault\public"

# PNG sources for apps that use raster logos (PDF generation, etc.)
$logoBlackPng       = "$brandRoot\..\..\..\Brand System\01 Full Logo\the-well-logo-gold-on-black.png"
$logoTransparentPng = "$brandRoot\..\..\..\Brand System\01 Full Logo\the-well-logo-gold-transparent.png"

# ── App targets (add new apps here) ──────────────────────────────────────────

$base = "C:\Users\scper\OneDrive - The Well Recruiting Solutions\Documents - Leadership\Cowork Folder\Claude Code"

$apps = @(
    @{
        name      = "the-well-vault"
        public    = $vaultPublic
        repo      = "$base\the-well-vault"
        pngLogos  = $false
    },
    @{
        name      = "the-well-content-studio"
        public    = "$base\the-well-content-studio\studio\public"
        repo      = "$base\the-well-content-studio"
        pngLogos  = $false
    },
    @{
        name      = "the-well-salesengine-tmp"
        public    = "$base\the-well-salesengine-tmp\public"
        repo      = "$base\the-well-salesengine-tmp"
        pngLogos  = $false
    },
    @{
        name      = "talentplan-app"
        public    = "$base\talentplan-app\public"
        repo      = "$base\talentplan-app"
        pngLogos  = $true    # also needs raster logo PNGs for PDF generation
    },
    @{
        name      = "thewell-sales"
        public    = "$base\thewell-sales\public"
        repo      = "$base\thewell-sales"
        pngLogos  = $true
    },
    @{
        name      = "the-well-website"
        public    = "$base\the-well-website"   # custom paths handled below
        repo      = "$base\the-well-website"
        pngLogos  = $false   # handled separately via website-specific paths
        isWebsite = $true
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
    Write-Host "-> $($app.name)" -ForegroundColor Yellow

    if ($app.isWebsite) {
        # Website has a different folder structure — copy to asset subdirs
        $faviconDst = "$($app.public)\assets\favicons"
        $logoDst    = "$($app.public)\assets\logos"
        $markDst    = "$($app.public)\assets\logos\mark"
        $svgDst     = "$($app.public)\assets\logos\svg"
        $brandSrc   = "C:\Users\scper\OneDrive - The Well Recruiting Solutions\Documents - Leadership\Cowork Folder\Brand System"

        foreach ($f in $favicons) {
            Copy-Item "$faviconsDir\$f" "$faviconDst\$f" -Force
        }
        foreach ($f in @("the-well-logo-gold-on-black.png","the-well-logo-gold-on-ivory.png","the-well-logo-black-on-ivory.png","the-well-logo-gold-transparent.png")) {
            Copy-Item "$brandSrc\01 Full Logo\$f" "$logoDst\$f" -Force
        }
        foreach ($f in @("the-well-mark-gold-on-black.png","the-well-mark-gold-on-ivory.png","the-well-mark-black-on-ivory.png","the-well-mark-gold-on-black-512.png","the-well-mark-gold-transparent-512.png")) {
            Copy-Item "$brandSrc\02 Mark Only\$f" "$markDst\$f" -Force
        }
        foreach ($f in @("the-well-logo-gold-transparent.svg","the-well-logo-gold-on-black.svg","the-well-logo-gold-transparent-v2.svg")) {
            Copy-Item "$svgDir\$f" "$svgDst\$f" -Force
        }
        Write-Host "  ok  website assets updated"
    } else {
        # Standard app: public/ gets favicons + SVGs
        if (-not (Test-Path $app.public)) {
            New-Item -ItemType Directory -Path $app.public | Out-Null
        }

        foreach ($f in $favicons) {
            Copy-Item "$faviconsDir\$f" "$($app.public)\$f" -Force
        }
        Write-Host "  ok  favicons ($($favicons.Count))"

        Copy-Item $logoSvgSrc "$($app.public)\the-well-logo.svg" -Force
        Write-Host "  ok  the-well-logo.svg"

        Copy-Item $markSvgSrc "$($app.public)\the-well-mark.svg" -Force
        Write-Host "  ok  the-well-mark.svg"

        # PNG logos for apps that use them (PDF generation)
        if ($app.pngLogos) {
            Copy-Item $logoBlackPng       "$($app.public)\the-well-logo.png" -Force
            Copy-Item $logoTransparentPng "$($app.public)\the-well-logo-transparent.png" -Force
            Write-Host "  ok  logo PNGs"
        }
    }

    # Git commit + push
    Push-Location $app.repo
    try {
        $status = git status --porcelain 2>&1
        if ($status) {
            git add -A | Out-Null
            $n = ($status | Measure-Object).Count
            git commit -m "chore: sync brand assets from Brand System ($n files)" | Out-Null
            git push origin main | Out-Null
            Write-Host "  pushed  ($n files)" -ForegroundColor Green
        } else {
            Write-Host "  no changes" -ForegroundColor DarkGray
        }
    } catch {
        Write-Warning "  git error: $_"
    }
    Pop-Location

    Write-Host ""
}

Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "Done. All apps synced." -ForegroundColor Green
Write-Host "Vercel will auto-deploy each repo." -ForegroundColor DarkGray
Write-Host ""
