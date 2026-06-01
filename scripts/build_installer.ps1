param(
  [ValidateSet("standalone", "onefile")]
  [string]$InstallerMode = "standalone"
)

$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

& ".\scripts\build_nuitka_installer.ps1" -InstallerMode $InstallerMode
