; Inno Setup script for Media Manager
; Build the .exe first (see README), then compile this script with Inno Setup.

#define AppName "Media Manager"
#define AppPublisher "Dong, Zhexi"

; BuildSourceDir and BuildOutputDir are passed by scripts/build_installer.ps1.
#ifndef BuildSourceDir
  #error BuildSourceDir is not defined. Use scripts/build_installer.ps1 to compile.
#endif

#ifndef BuildOutputDir
  #define BuildOutputDir AddBackslash(ExtractFileDir(SourcePath)) + "..\\dist_installer"
#endif

#ifndef AppVersion
  #define AppVersion "0.0.1"
#endif

[Setup]
AppId={{6E04C6A3-7F7C-4B76-AF4E-4B0E0C7B0B01}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
AppCopyright=Copyright (C) 2026 {#AppPublisher}
DefaultDirName={autopf}\\{#AppName}
DefaultGroupName={#AppName}
DisableDirPage=no
DisableProgramGroupPage=no
OutputBaseFilename=MediaManagerSetup_{#AppVersion}
OutputDir={#BuildOutputDir}
Compression=lzma
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64

; Optional: if you bundle VC++ redistributable in the same folder as this script
; copy vcredist_x64.exe next to the .iss and uncomment the line in [Files] and [Run].

[Languages]
Name: "en"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop icon"; GroupDescription: "Additional icons:"; Flags: unchecked

[Files]
; Main application folder (Nuitka standalone build)
Source: "{#BuildSourceDir}\\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion

; Optional VC++ runtime (if provided manually)
; Source: "vcredist_x64.exe"; DestDir: "{tmp}"; Flags: deleteafterinstall; Tasks: 

[Icons]
Name: "{group}\\{#AppName}"; Filename: "{app}\\MediaManager.exe"
Name: "{userdesktop}\\{#AppName}"; Filename: "{app}\\MediaManager.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\\MediaManager.exe"; Description: "Launch {#AppName}"; Flags: nowait postinstall skipifsilent

; Optional VC++ runtime, silent install before app
; Filename: "{tmp}\\vcredist_x64.exe"; Parameters: "/install /quiet /norestart"; StatusMsg: "Installing Microsoft Visual C++ Runtime..."; Flags: waituntilterminated runhidden

