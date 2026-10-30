; Pyobliqua - instalador Inno Setup 6/7
; Compilar por scripts/gerar_instalador.py para injetar a versão oficial.
#ifndef AppVersion
  #define AppVersion "2026.1.0"
#endif
#define AppName "Pyobliqua"
#define AppExeName "Pyobliqua.exe"

[Setup]
; Mantenha este AppId nas próximas versões para permitir atualização.
AppId={{5FBE7BA4-91F2-49AD-B5A9-63C8503D8E2C}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher=Felipe Quevedo
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
OutputDir=..\dist\installer
OutputBaseFilename=Pyobliqua_Setup_{#AppVersion}
Compression=lzma
SolidCompression=yes
WizardStyle=modern
SetupIconFile=..\src\pyobliqua\assets\pyobliqua.ico
UninstallDisplayIcon={app}\pyobliqua.ico
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
UninstallDisplayName={#AppName} {#AppVersion}
; Sem assinatura digital configurada por enquanto.

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "Criar atalho na área de trabalho"; GroupDescription: "Atalhos adicionais:"; Flags: unchecked

[Files]
; O script de build garante que este executável exista antes da compilação.
Source: "..\dist\Pyobliqua.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\src\pyobliqua\assets\pyobliqua.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Pyobliqua"; Filename: "{app}\{#AppExeName}"; IconFilename: "{app}\pyobliqua.ico"; IconIndex: 0
Name: "{autodesktop}\Pyobliqua"; Filename: "{app}\{#AppExeName}"; IconFilename: "{app}\pyobliqua.ico"; IconIndex: 0; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExeName}"; Description: "Abrir Pyobliqua"; Flags: nowait postinstall skipifsilent
