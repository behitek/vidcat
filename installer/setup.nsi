!include "MUI2.nsh"

Name "VidCat"
OutFile "VidCat_Installer.exe"
InstallDir "$PROGRAMFILES64\VidCat"
RequestExecutionLevel admin

!define MUI_ABORTWARNING
!define MUI_ICON "..\assets\icon.ico"
!define MUI_UNICON "..\assets\icon.ico"

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_WELCOME
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH

!insertmacro MUI_LANGUAGE "Vietnamese"

Section "VidCat (required)" SecCore
  SetOutPath "$INSTDIR"
  
  # Copy all files from the PyInstaller dist directory
  File /r "..\dist\VidCat\*.*"
  
  # Create Uninstaller
  WriteUninstaller "$INSTDIR\uninstall.exe"
  
  # Start Menu shortcut
  CreateDirectory "$SMPROGRAMS\VidCat"
  CreateShortcut "$SMPROGRAMS\VidCat\VidCat.lnk" "$INSTDIR\VidCat.exe" "" "$INSTDIR\VidCat.exe" 0
  
  # Desktop shortcut
  CreateShortcut "$DESKTOP\VidCat.lnk" "$INSTDIR\VidCat.exe" "" "$INSTDIR\VidCat.exe" 0
  
  # Registry keys for Add/Remove Programs
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\VidCat" "DisplayName" "VidCat 1.0.0"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\VidCat" "UninstallString" '"$INSTDIR\uninstall.exe"'
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\VidCat" "DisplayIcon" "$INSTDIR\VidCat.exe"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\VidCat" "Publisher" "Hieu Nguyen | behitek.com"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\VidCat" "DisplayVersion" "1.0.0"
SectionEnd

Section "Uninstall"
  Delete "$DESKTOP\VidCat.lnk"
  Delete "$SMPROGRAMS\VidCat\VidCat.lnk"
  RMDir "$SMPROGRAMS\VidCat"
  
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\VidCat"
  
  RMDir /r "$INSTDIR"
SectionEnd
