;My Installer for the GenerateHeader.py setup

; This was taken from the example page of fileread
#define FileHandle
#sub ProcessFileLine
  #define public _VERSION FileRead(FileHandle)
#endsub
#for {FileHandle = FileOpen("version.txt"); \
  FileHandle && !FileEof(FileHandle); ""} \
  ProcessFileLine
#if FileHandle
  #expr FileClose(FileHandle)
#endif
#pragma message "Displaying File Version"
#pragma message _VERSION


[Setup]
AppName="AMOG Check In"
AppVersion={#_VERSION}
DefaultDirName={userdesktop}\Check_In
DisableProgramGroupPage=yes
Compression=lzma2                                                                             
OutputBaseFilename=Check_In_v{#_VERSION}
SolidCompression=yes
Uninstallable=no
OutputDir="release"
SetupIconFile="src_client\img\icon.ico"

[Files]
Source: "build\*"; DestDir: "{app}\code"; Flags: recursesubdirs
Source: "lib\*"; DestDir: "{app}\lib"; Flags: recursesubdirs
Source: "src_client\img\*"; DestDir: "{app}\code\img"
; We will ship the version with this file, so we can test on the first running if we need to update
Source: "version.txt"; DestDir: "{app}"

[Icons]
Name: "{userdesktop}\AMOG Check In"; FileName: "{app}\code\client.exe"; WorkingDir: "{app}\code"; IconFilename: "{app}\code\img\icon.ico" 
; Name: "{userdesktop}\Music Folder"; Filename: "{app}\code\Music";
; Name: "{userdesktop}\Scripts Folder"; Filename: "{app}\code\Scripts";