; Script generated by the Inno Setup Script Wizard.
; SEE THE DOCUMENTATION FOR DETAILS ON CREATING INNO SETUP SCRIPT FILES!

[Setup]
; NOTE: The value of AppId uniquely identifies this application.
; Do not use the same AppId value in installers for other applications.
; (To generate a new GUID, click Tools | Generate GUID inside the IDE.)
AppId={{F36E72B3-D31D-4808-8F85-A9506960E905}
AppName=DSPDemo
AppVersion=0.2.0
AppPublisher=ajaxsoundstudio.com
AppSupportURL=https://github.com/belangeo/dspdemo
DefaultDirName={pf}\DSPDemo
DisableDirPage=yes
DefaultGroupName=DSPDemo
AllowNoIcons=yes
LicenseFile=C:\Users\olivier\git\dspdemo\DSPDemo_Win\Resources\COPYING.txt
OutputBaseFilename=DSPDemo_0.2.0_setup
Compression=lzma
SolidCompression=yes
ChangesAssociations=yes
Uninstallable=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "C:\Users\olivier\git\dspdemo\DSPDemo_Win\DSPDemo.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\Users\olivier\git\dspdemo\DSPDemo_Win\Resources\*"; DestDir: "{app}\Resources"; Flags: ignoreversion recursesubdirs createallsubdirs
; NOTE: Don't use "Flags: ignoreversion" on any shared system files

[Icons]
Name: "{group}\DSPDemo"; Filename: "{app}\DSPDemo.exe"; WorkingDir: "{app}"
Name: "{commondesktop}\DSPDemo"; Filename: "{app}\DSPDemo.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\DSPDemo.exe"; Description: "{cm:LaunchProgram,DSPDemo}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: files; Name: "{app}\DSPDemo Uninstall"







