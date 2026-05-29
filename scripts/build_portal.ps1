param(
  [ValidateSet("standalone", "onefile")]
  [string]$BuildMode = "standalone"
)

$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

Write-Host "Building portable (portal) edition..." -ForegroundColor Cyan
& ".\scripts\build_nuitka.ps1" -Mode $BuildMode

if ($BuildMode -eq "onefile") {
  throw "Portable edition requires standalone build (folder with data/). Use -BuildMode standalone."
}

$source = Join-Path (Get-Location) "dist\MediaManager"
if (-not (Test-Path (Join-Path $source "MediaManager.exe"))) {
  throw "Build output not found: dist\MediaManager\MediaManager.exe"
}

$appVersion = (& ".\.venv\Scripts\python.exe" -c "import sys; sys.path.insert(0, 'src'); from version import __version__; print(__version__)").Trim()
$portalRoot = Join-Path (Get-Location) "dist_portal\MediaManager"
$dataDir = Join-Path $portalRoot "data"

if (Test-Path $portalRoot) {
  Remove-Item $portalRoot -Recurse -Force
}
New-Item -ItemType Directory -Force -Path $portalRoot | Out-Null
Copy-Item "$source\*" $portalRoot -Recurse

"" | Set-Content -Path (Join-Path $portalRoot "portable.marker") -Encoding utf8
New-Item -ItemType Directory -Force -Path $dataDir | Out-Null

@'
Media Manager — portable data folder
====================================

On first run the app creates:
  config.json   — settings and library root paths
  catalog.db    — catalog database
  logs\         — application log

To move to another PC: copy the entire MediaManager folder (including this data\ folder).
Use Tools → Export database for backups; Import database to restore.

Library folder paths inside config.json are absolute paths on each machine —
re-add or edit library roots after moving if drive letters differ.
'@ | Set-Content -Path (Join-Path $dataDir "README.txt") -Encoding utf8

if (Test-Path "CHANGELOG.md") {
  Copy-Item "CHANGELOG.md" $portalRoot -Force
}

$zipPath = Join-Path (Get-Location) "dist_portal\MediaManagerPortal_v$appVersion.zip"
if (Test-Path $zipPath) {
  Remove-Item $zipPath -Force
}
Compress-Archive -Path $portalRoot -DestinationPath $zipPath

Write-Host ""
Write-Host "Portable build complete." -ForegroundColor Green
Write-Host "  Folder: $portalRoot"
Write-Host "  Zip:    $zipPath"
Write-Host ""
Write-Host "Run MediaManager.exe from the folder (no installer). Data lives in data\"
