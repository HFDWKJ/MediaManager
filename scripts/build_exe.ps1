param(
  [ValidateSet("standalone", "onefile", "onedir")]
  [string]$Mode = "standalone"
)

$ErrorActionPreference = "Stop"

# Legacy alias: PyInstaller used "onedir"; Nuitka uses "standalone".
if ($Mode -eq "onedir") {
  $Mode = "standalone"
}

& (Join-Path $PSScriptRoot "build_nuitka.ps1") -Mode $Mode
