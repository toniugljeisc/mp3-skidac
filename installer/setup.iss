; Inno Setup skripta — klasična Windows instalacija za MP3 Skidač
#define AppName "MP3 Skidač"
#define AppExe "MP3 Skidac.exe"
#ifndef AppVersion
  #define AppVersion "1.1.0"
#endif

[Setup]
AppId={{6B1F3A52-8E0D-4C7B-9A21-3D5E7F90B4C1}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher=Baron d.o.o.
DefaultDirName={localappdata}\Programs\MP3 Skidac
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=..\output
OutputBaseFilename=MP3-Skidac-Setup
SetupIconFile=..\app\icon.ico
UninstallDisplayIcon={app}\{#AppExe}
UninstallDisplayName={#AppName}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "en"; MessagesFile: "compiler:Default.isl"

[CustomMessages]
en.DesktopIcon=Napravi ikonu na radnoj površini
en.LaunchApp=Pokreni MP3 Skidač

[Tasks]
Name: "desktopicon"; Description: "{cm:DesktopIcon}"; Flags: checkedonce

[Files]
Source: "..\dist\MP3 Skidac\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExe}"
Name: "{group}\Deinstaliraj {#AppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExe}"; Description: "{cm:LaunchApp}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: files; Name: "{app}\yt-dlp.exe"
