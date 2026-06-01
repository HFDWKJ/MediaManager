param(
  [ValidateSet("standalone", "onefile", "onedir")]
  [string]$BuildMode = "standalone"
)

$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

& ".\scripts\build_nuitka_installer.ps1" -BuildMode $BuildMode
