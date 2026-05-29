param(
  [Parameter(Mandatory = $false)]
  [string]$RepoUrl = "",
  [Parameter(Mandatory = $false)]
  [string]$RepoName = "MediaManager",
  [switch]$Private,
  [switch]$SkipPush
)

$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

function Find-Git {
  $candidates = @(
    "git",
    "${env:ProgramFiles}\Git\cmd\git.exe",
    "${env:ProgramFiles(x86)}\Git\cmd\git.exe"
  )
  foreach ($c in $candidates) {
    if ($c -eq "git") {
      $cmd = Get-Command git -ErrorAction SilentlyContinue
      if ($cmd) { return $cmd.Source }
      continue
    }
    if (Test-Path $c) { return $c }
  }
  throw "Git is not installed. Install from https://git-scm.com/download/win then re-run this script."
}

function Find-Gh {
  $candidates = @(
    "gh",
    "${env:ProgramFiles}\GitHub CLI\gh.exe",
    "$env:LOCALAPPDATA\Programs\GitHub CLI\gh.exe"
  )
  foreach ($c in $candidates) {
    if ($c -eq "gh") {
      $cmd = Get-Command gh -ErrorAction SilentlyContinue
      if ($cmd) { return $cmd.Source }
      continue
    }
    if (Test-Path $c) { return $c }
  }
  return $null
}

$git = Find-Git
Write-Host "Using git: $git" -ForegroundColor Cyan

$authorName = "Dong, Zhexi"
$authorEmail = "HFDWKJ@users.noreply.github.com"
$versionFile = Join-Path $PWD "src\version.py"
if (Test-Path $versionFile) {
  $v = Get-Content $versionFile -Raw
  if ($v -match 'DEVELOPER\s*=\s*"([^"]+)"') { $authorName = $Matches[1] }
}
function Invoke-Git {
  param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Args)
  & $git -c "user.name=$authorName" -c "user.email=$authorEmail" @Args
}

if (-not (Test-Path ".git")) {
  Invoke-Git init
  Invoke-Git branch -M main
}

Invoke-Git add -A
$status = Invoke-Git status --porcelain
if (-not $status) {
  Write-Host "Nothing to commit - working tree clean." -ForegroundColor Yellow
} else {
  $msg = "Media Manager v0.0.1 - initial GitHub sync"
  Invoke-Git commit -m $msg
  Write-Host "Committed changes." -ForegroundColor Green
}

$remote = ""
try { $remote = (& $git remote get-url origin 2>$null) } catch { }

if (-not $remote) {
  if (-not $RepoUrl) {
    $gh = Find-Gh
    if ($gh) {
      Write-Host "No remote. Creating GitHub repo with gh..." -ForegroundColor Cyan
      $createArgs = @("repo", "create", $RepoName, "--source=.", "--remote=origin", "--push")
      if ($Private) { $createArgs += "--private" } else { $createArgs += "--public" }
      & $gh @createArgs
      Write-Host "Repository created and pushed." -ForegroundColor Green
      exit 0
    }
    throw "No remote configured. Pass -RepoUrl https://github.com/USER/REPO.git"
  }
  Invoke-Git remote add origin $RepoUrl
  $remote = $RepoUrl
  Write-Host "Added remote origin: $remote" -ForegroundColor Cyan
}

if ($SkipPush) {
  Write-Host "SkipPush set - commit only, no push." -ForegroundColor Yellow
  exit 0
}

& $git push -u origin main 2>&1 | ForEach-Object { $_; if ($_ -match "could not read Username|Authentication failed|403|401") { $script:authFailed = $true } }
if ($LASTEXITCODE -ne 0) {
  Write-Host ""
  Write-Host "Push failed - GitHub authentication required." -ForegroundColor Red
  Write-Host "Option A: Install GitHub CLI and sign in:" -ForegroundColor Yellow
  Write-Host "  winget install GitHub.cli" -ForegroundColor Gray
  Write-Host "  gh auth login" -ForegroundColor Gray
  Write-Host "  git push -u origin main" -ForegroundColor Gray
  Write-Host "Option B: Use a Personal Access Token when prompted for password:" -ForegroundColor Yellow
  Write-Host "  https://github.com/settings/tokens" -ForegroundColor Gray
  exit $LASTEXITCODE
}
Write-Host ""
Write-Host "Pushed to: $remote" -ForegroundColor Green
