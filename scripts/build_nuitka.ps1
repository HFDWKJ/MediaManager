param(
  [ValidateSet("standalone", "onefile")]
  [string]$Mode = "standalone"
)

$ErrorActionPreference = "Stop"

Set-Location (Split-Path $PSScriptRoot -Parent)

if (-not (Test-Path ".venv")) {
  python -m venv .venv
}

$python = ".\.venv\Scripts\python.exe"
& $python -m pip install --upgrade pip
& $python -m pip install -r requirements.txt
& $python -m pip install "nuitka>=2.0" ordered-set

$appVersion = (& $python -c "import sys; sys.path.insert(0, 'src'); from version import __version__; print(__version__)").Trim()
$fileVersion = "$appVersion.0"
$developer = (& $python -c "import sys; sys.path.insert(0, 'src'); from version import __developer__; print(__developer__)").Trim()

Write-Host "Building with Nuitka ($Mode) v$appVersion..." -ForegroundColor Cyan

$nuitkaArgs = @(
  "src/main.py",
  "--assume-yes-for-downloads",
  "--enable-plugin=pyqt6",
  "--windows-console-mode=disable",
  "--include-package=core",
  "--include-package=gui",
  "--include-package=utils",
  "--include-module=version",
  "--include-data-files=CHANGELOG.md=CHANGELOG.md",
  "--output-dir=dist",
  "--output-filename=MediaManager.exe",
  "--company-name=$developer",
  "--product-name=Media Manager",
  "--file-version=$fileVersion",
  "--product-version=$fileVersion",
  "--remove-output"
)

if ($Mode -eq "onefile") {
  $nuitkaArgs = @("--onefile") + $nuitkaArgs
} else {
  $nuitkaArgs = @("--standalone") + $nuitkaArgs
}

# Nuitka can locate MSVC even when cl.exe is not on PATH.
$hasCl = Get-Command cl.exe -ErrorAction SilentlyContinue
$pyMinor = [int](& $python -c "import sys; print(sys.version_info.minor)")
if (-not $hasCl -and $pyMinor -lt 13) {
  Write-Host "MSVC not found in PATH; using MinGW64 for Nuitka." -ForegroundColor Yellow
  $nuitkaArgs = @("--mingw64") + $nuitkaArgs
} elseif (-not $hasCl) {
  Write-Host "MSVC not in PATH; Nuitka will try to locate Visual Studio." -ForegroundColor Yellow
}

& $python -m nuitka @nuitkaArgs

function Resolve-NuitkaOutputDir {
  $repo = Get-Location
  $candidates = @(
    (Join-Path $repo "dist\MediaManager.dist"),
    (Join-Path $repo "dist\main.dist")
  )
  foreach ($dir in $candidates) {
    if ((Test-Path $dir) -and (Test-Path (Join-Path $dir "MediaManager.exe"))) {
      return (Resolve-Path $dir).Path
    }
    if ((Test-Path $dir) -and (Test-Path (Join-Path $dir "main.exe"))) {
      return (Resolve-Path $dir).Path
    }
  }
  return $null
}

if ($Mode -eq "onefile") {
  $onefile = Join-Path (Get-Location) "dist\MediaManager.exe"
  if (-not (Test-Path $onefile)) {
    throw "Nuitka onefile build failed: dist\MediaManager.exe not found."
  }
  Write-Host ""
  Write-Host "Build complete." -ForegroundColor Green
  Write-Host "Output: dist\MediaManager.exe"
  exit 0
}

$builtDir = Resolve-NuitkaOutputDir
if (-not $builtDir) {
  throw "Nuitka standalone build failed: could not find MediaManager.dist or main.dist."
}

$stageDir = Join-Path (Get-Location) "dist\MediaManager"
if (Test-Path $stageDir) {
  Remove-Item $stageDir -Recurse -Force
}
Copy-Item $builtDir $stageDir -Recurse

$exe = Join-Path $stageDir "MediaManager.exe"
if (-not (Test-Path $exe)) {
  $mainExe = Join-Path $stageDir "main.exe"
  if (Test-Path $mainExe) {
    Rename-Item $mainExe "MediaManager.exe"
  }
}

if (-not (Test-Path (Join-Path $stageDir "MediaManager.exe"))) {
  throw "Staged build is missing MediaManager.exe in dist\MediaManager"
}

Write-Host ""
Write-Host "Build complete." -ForegroundColor Green
Write-Host "Output: dist\MediaManager\MediaManager.exe"
