param(
  [ValidateSet("standalone", "onefile", "onedir")]
  [string]$BuildMode = "standalone"
)

$ErrorActionPreference = "Stop"

Set-Location (Split-Path $PSScriptRoot -Parent)

if ($BuildMode -eq "onedir") {
  $BuildMode = "standalone"
}

Write-Host "Building app ($BuildMode)..." -ForegroundColor Cyan
& ".\scripts\build_nuitka.ps1" -Mode $BuildMode

if ($BuildMode -ne "standalone") {
  throw "Installer requires the standalone build. Re-run with: .\scripts\build_installer.ps1 -BuildMode standalone"
}

$iss = Join-Path (Get-Location) "installers\media_manager.iss"
if (-not (Test-Path $iss)) {
  throw "Inno Setup script not found: $iss"
}

function Resolve-BuildSourceDir {
  $repo = Get-Location
  $candidates = @(
    (Join-Path $repo "dist\MediaManager"),
    (Join-Path $repo "dist\MediaManager.dist"),
    (Join-Path $repo "dist\main.dist")
  )
  foreach ($dir in $candidates) {
    if (-not (Test-Path $dir)) { continue }
    foreach ($name in @("MediaManager.exe", "main.exe")) {
      if (Test-Path (Join-Path $dir $name)) {
        return (Resolve-Path $dir).Path
      }
    }
  }
  throw @"
Could not find Nuitka standalone output.
Expected one of:
  dist\MediaManager\MediaManager.exe
  dist\MediaManager.dist\MediaManager.exe

Run .\scripts\build_nuitka.ps1 first and confirm the exe exists.
"@
}

function Find-ISCC {
  $candidates = @(
    "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
    "${env:ProgramFiles}\Inno Setup 6\ISCC.exe",
    "${env:ProgramFiles(x86)}\Inno Setup 5\ISCC.exe",
    "${env:ProgramFiles}\Inno Setup 5\ISCC.exe"
  )
  foreach ($p in $candidates) {
    if ($p -and (Test-Path $p)) { return $p }
  }
  $cmd = Get-Command ISCC.exe -ErrorAction SilentlyContinue
  if ($cmd) { return $cmd.Source }
  return $null
}

$buildSourceDir = Resolve-BuildSourceDir
$buildOutputDir = Join-Path (Get-Location) "dist_installer"
New-Item -ItemType Directory -Force -Path $buildOutputDir | Out-Null

$iscc = Find-ISCC
if (-not $iscc) {
  throw @"
Inno Setup is not installed (ISCC.exe not found).

Install Inno Setup first, then re-run:
  https://jrsoftware.org/isinfo.php

Expected paths:
  $env:ProgramFiles(x86)\Inno Setup 6\ISCC.exe
  $env:ProgramFiles\Inno Setup 6\ISCC.exe
"@
}

Write-Host "Compiling installer with: $iscc" -ForegroundColor Cyan
Write-Host "Packaging files from: $buildSourceDir" -ForegroundColor Cyan
$appVersion = (& ".\.venv\Scripts\python.exe" -c "import sys; sys.path.insert(0, 'src'); from version import __version__; print(__version__)").Trim()
& $iscc "/DBuildSourceDir=$buildSourceDir" "/DBuildOutputDir=$buildOutputDir" "/DAppVersion=$appVersion" $iss

Write-Host ""
Write-Host "Installer output folder: $buildOutputDir" -ForegroundColor Green
Get-ChildItem $buildOutputDir -Filter "*Setup*.exe" -ErrorAction SilentlyContinue | ForEach-Object {
  Write-Host ("  " + $_.FullName)
}

Write-Host ""
Write-Host "Installer build complete." -ForegroundColor Green
