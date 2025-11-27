[Setup]
AppName=笔尖传奇下载器
AppVersion=1.0.0
AppPublisher=南城出品
DefaultDirName={localappdata}\bijianchuanqi
DisableDirPage=no
OutputBaseFilename=笔尖传奇下载器_安装包_v1.0.0
SetupIconFile=icon.ico
UninstallDisplayIcon={app}\笔尖传奇下载器.exe
Compression=lzma
SolidCompression=yes
OutputDir=dist_installer
PrivilegesRequired=admin
; 移除无效的 PrivilegesRequiredOverridesAllowed，采用默认行为（命令行允许）
UseSetupLdr=yes

[Files]
Source: "dist\笔尖传奇下载器\*"; DestDir: "{app}"; Flags: recursesubdirs

[Icons]
Name: "{group}\笔尖传奇下载器"; Filename: "{app}\笔尖传奇下载器.exe"
Name: "{commondesktop}\笔尖传奇下载器"; Filename: "{app}\笔尖传奇下载器.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "在桌面创建快捷方式"; GroupDescription: "快捷方式"

[Run]
Filename: "{app}\笔尖传奇下载器.exe"; Description: "运行 笔尖传奇下载器"; Flags: nowait postinstall skipifsilent

[Code]
function HasSuffixDir(Dir: string): Boolean;
var d: string;
begin
  d := Dir;
  while (Length(d) > 0) and (d[Length(d)] = '\\') do
    Delete(d, Length(d), 1);
  Result := (ExtractFileName(d) = 'bijianchuanqi');
end;

procedure EnsureSuffix();
begin
  if not HasSuffixDir(WizardForm.DirEdit.Text) then
    WizardForm.DirEdit.Text := AddBackslash(WizardForm.DirEdit.Text) + 'bijianchuanqi';
end;

procedure CurPageChanged(CurPageID: Integer);
begin
  if CurPageID = wpSelectDir then
    EnsureSuffix();
end;

function NextButtonClick(CurPageID: Integer): Boolean;
begin
  Result := True;
  if CurPageID = wpSelectDir then
    EnsureSuffix();
end;
