; installer.nsi
!include "MUI2.nsh"
Name "AI Desktop Detector"
OutFile "ai_desktop_detector_setup.exe"
InstallDir "$PROGRAMFILES\AI Desktop Detector"
RequestExecutionLevel admin
Page directory
Page instfiles

Section "Install"
  SetOutPath "$INSTDIR"
  File /r "dist\ai_desktop_detector\*"
  CreateShortcut "$DESKTOP\AI Desktop Detector.lnk" "$INSTDIR\ai_desktop_detector.exe"
SectionEnd

Section "Uninstall"
  Delete "$INSTDIR\ai_desktop_detector.exe"
  RMDir /r "$INSTDIR"
  Delete "$DESKTOP\AI Desktop Detector.lnk"
SectionEnd
