param(
  [ValidateSet("standalone", "onefile")]
  [string]$InstallerMode = "standalone"
)

$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

Write-Host "Building application (standalone)..." -ForegroundColor Cyan
& ".\scripts\build_nuitka.ps1" -Mode standalone

$payloadDir = Join-Path (Get-Location) "dist\MediaManager"
if (-not (Test-Path (Join-Path $payloadDir "MediaManager.exe"))) {
  throw "Nuitka app build missing: dist\MediaManager\MediaManager.exe"
}

$python = ".\.venv\Scripts\python.exe"
$appVersion = (& $python -c "import sys; sys.path.insert(0, 'src'); from version import __version__; print(__version__)").Trim()
$developer = (& $python -c "import sys; sys.path.insert(0, 'src'); from version import __developer__; print(__developer__)").Trim()
$versionParts = @($appVersion -split '\.' | ForEach-Object { [int]$_ })
while ($versionParts.Count -lt 4) { $versionParts += 0 }
if ($versionParts.Count -gt 4) { $versionParts = $versionParts[0..3] }
$fileVersion = ($versionParts -join '.')
$iconIco = Join-Path (Get-Location) "assets\media_manager_app_icon.ico"

if (-not (Test-Path $iconIco)) {
  throw "Missing setup icon: $iconIco"
}

Set-Content -Path (Join-Path $payloadDir "version.txt") -Value $appVersion -Encoding utf8

$outDir = Join-Path (Get-Location) "dist_installer"
$buildDir = Join-Path $outDir "_build"
if (Test-Path $buildDir) {
  Remove-Item $buildDir -Recurse -Force
}
New-Item -ItemType Directory -Force -Path $buildDir | Out-Null

$setupExeName = "MediaManagerSetup_$appVersion.exe"
$stageName = "MediaManagerSetup_$appVersion"
$stageDir = Join-Path $outDir $stageName
$zipPath = Join-Path $outDir "$stageName.zip"

Write-Host "Building Nuitka installer ($InstallerMode) -> $setupExeName" -ForegroundColor Cyan

$nuitkaArgs = @(
  "src/installer/main.py",
  "--assume-yes-for-downloads",
  "--windows-console-mode=disable",
  "--windows-uac-admin",
  "--include-raw-dir=$payloadDir=payload",
  "--output-dir=$buildDir",
  "--output-filename=$setupExeName",
  "--company-name=$developer",
  "--product-name=Media Manager Setup",
  "--file-version=$fileVersion",
  "--product-version=$fileVersion",
  "--windows-icon-from-ico=$iconIco",
  "--remove-output"
)

if ($InstallerMode -eq "onefile") {
  $nuitkaArgs = @("--onefile") + $nuitkaArgs
  Write-Host "Note: onefile installers are more likely to be flagged by Windows Defender." -ForegroundColor Yellow
} else {
  $nuitkaArgs = @("--standalone") + $nuitkaArgs
}

$hasCl = Get-Command cl.exe -ErrorAction SilentlyContinue
$pyMinor = [int](& $python -c "import sys; print(sys.version_info.minor)")
if (-not $hasCl -and $pyMinor -lt 13) {
  $nuitkaArgs = @("--mingw64") + $nuitkaArgs
}

& $python -m nuitka @nuitkaArgs

function Resolve-InstallerDist {
  param([string]$Root)
  $candidates = @(
    (Join-Path $Root "installer.dist"),
    (Join-Path $Root "main.dist")
  )
  foreach ($dir in $candidates) {
    $exe = Join-Path $dir $setupExeName
    if ((Test-Path $dir) -and (Test-Path $exe)) {
      return (Resolve-Path $dir).Path
    }
  }
  return $null
}

if ($InstallerMode -eq "onefile") {
  $onefile = Join-Path $buildDir $setupExeName
  if (-not (Test-Path $onefile)) {
    throw "Installer onefile build failed: $onefile not found"
  }
  Copy-Item $onefile (Join-Path $outDir $setupExeName) -Force
  Write-Host ""
  Write-Host "Installer build complete (onefile)." -ForegroundColor Green
  Write-Host "Output: $outDir\$setupExeName"
  exit 0
}

$builtDir = Resolve-InstallerDist -Root $buildDir
if (-not $builtDir) {
  throw "Installer standalone build failed: could not find installer.dist with $setupExeName"
}

if (Test-Path $stageDir) {
  Remove-Item $stageDir -Recurse -Force
}
Copy-Item $builtDir $stageDir -Recurse

if (-not (Test-Path (Join-Path $stageDir "payload\MediaManager.exe"))) {
  throw "Staged installer is missing payload\MediaManager.exe"
}

if (Test-Path $zipPath) {
  Remove-Item $zipPath -Force
}
Compress-Archive -Path $stageDir -DestinationPath $zipPath -CompressionLevel Optimal

Write-Host ""
Write-Host "Installer build complete (standalone folder)." -ForegroundColor Green
Write-Host "  Folder: $stageDir"
Write-Host "  Zip:    $zipPath"
Write-Host ""
Write-Host "User steps: extract the zip, then run $setupExeName inside the folder."
