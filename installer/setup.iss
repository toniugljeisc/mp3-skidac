; Inno Setup skripta — klasična Windows instalacija za MP3 Skidač
#ifdef Big
  #define AppName "MP3 Skidač - velika slova"
  #define AppExe "MP3 Skidac Veliki.exe"
  #define AppDirName "MP3 Skidac Veliki"
  #define OutName "MP3-Skidac-Veliki-Setup"
#else
  #define AppName "MP3 Skidač"
  #define AppExe "MP3 Skidac.exe"
  #define AppDirName "MP3 Skidac"
  #define OutName "MP3-Skidac-Setup"
#endif
#ifndef AppVersion
  #define AppVersion "1.1.0"
#endif

[Setup]
#ifdef Big
AppId={{8D2C5E14-3A7B-4F21-B9C6-5E0A1D7F2B93}
#else
AppId={{6B1F3A52-8E0D-4C7B-9A21-3D5E7F90B4C1}
#endif
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher=Baron d.o.o.
DefaultDirName={localappdata}\Programs\{#AppDirName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=..\output
OutputBaseFilename={#OutName}
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
en.LaunchApp=Pokreni {#AppName}

[Tasks]
Name: "desktopicon"; Description: "{cm:DesktopIcon}"; Flags: checkedonce

[Files]
Source: "..\dist\{#AppDirName}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExe}"
Name: "{group}\Deinstaliraj {#AppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExe}"; Description: "{cm:LaunchApp}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: files; Name: "{app}\yt-dlp.exe"
