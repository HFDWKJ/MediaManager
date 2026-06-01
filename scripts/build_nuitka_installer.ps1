param(
  [ValidateSet("standalone", "onefile", "onedir")]
  [string]$BuildMode = "standalone"
)

$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

if ($BuildMode -eq "onedir") {
  $BuildMode = "standalone"
}

Write-Host "Building application ($BuildMode)..." -ForegroundColor Cyan
& ".\scripts\build_nuitka.ps1" -Mode $BuildMode

$payloadDir = Join-Path (Get-Location) "dist\MediaManager"
if (-not (Test-Path (Join-Path $payloadDir "MediaManager.exe"))) {
  throw "Nuitka app build missing: dist\MediaManager\MediaManager.exe"
}

$python = ".\.venv\Scripts\python.exe"
$appVersion = (& $python -c "import sys; sys.path.insert(0, 'src'); from version import __version__; print(__version__)").Trim()
$developer = (& $python -c "import sys; sys.path.insert(0, 'src'); from version import __developer__; print(__developer__)").Trim()
$fileVersion = "$appVersion.0"
$iconIco = Join-Path (Get-Location) "assets\media_manager_app_icon.ico"

if (-not (Test-Path $iconIco)) {
  throw "Missing setup icon: $iconIco"
}

Set-Content -Path (Join-Path $payloadDir "version.txt") -Value $appVersion -Encoding utf8

$outDir = Join-Path (Get-Location) "dist_installer"
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
$setupName = "MediaManagerSetup_$appVersion.exe"
$setupPath = Join-Path $outDir $setupName

Write-Host "Building Nuitka installer -> $setupName" -ForegroundColor Cyan

$nuitkaArgs = @(
  "src/installer/main.py",
  "--onefile",
  "--assume-yes-for-downloads",
  "--windows-console-mode=disable",
  "--windows-uac-admin",
  "--include-raw-dir=$payloadDir=payload",
  "--output-dir=$outDir",
  "--output-filename=$setupName",
  "--company-name=$developer",
  "--product-name=Media Manager Setup",
  "--file-version=$fileVersion",
  "--product-version=$fileVersion",
  "--windows-icon-from-ico=$iconIco",
  "--remove-output"
)

$hasCl = Get-Command cl.exe -ErrorAction SilentlyContinue
$pyMinor = [int](& $python -c "import sys; print(sys.version_info.minor)")
if (-not $hasCl -and $pyMinor -lt 13) {
  $nuitkaArgs = @("--mingw64") + $nuitkaArgs
}

& $python -m nuitka @nuitkaArgs

if (-not (Test-Path $setupPath)) {
  throw "Installer build failed: $setupPath not found"
}

Write-Host ""
Write-Host "Installer build complete." -ForegroundColor Green
Write-Host "Output: $setupPath"
