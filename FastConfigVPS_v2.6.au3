#AutoIt3Wrapper_Icon=icon.ico
#AutoIt3Wrapper_Outfile=FastConfigVPS.exe
#AutoIt3Wrapper_Compression=4
#AutoIt3Wrapper_Res_Description=FastConfig VPS Configuration Tool
#AutoIt3Wrapper_Res_Productname=FastConfig VPS
#AutoIt3Wrapper_Res_ProductVersion=2.6.0.0
#AutoIt3Wrapper_Res_FileVersion=2.6.0.0
#AutoIt3Wrapper_Res_CompanyName=FastConfig Solutions
#AutoIt3Wrapper_Res_LegalCopyright=Copyright © 2025 FastConfig Solutions
#AutoIt3Wrapper_Res_Language=1033
#AutoIt3Wrapper_Res_requestedExecutionLevel=asInvoker
#AutoIt3Wrapper_Res_SaveSource=y
#AutoIt3Wrapper_Run_Tidy=y
#AutoIt3Wrapper_Run_Au3Stripper=y

; #RequireAdmin  ; Commented out to avoid UAC prompt - uncomment if admin rights needed
#NoTrayIcon

; FastConfigVPS v3.1 - Enhanced Version with Updated RDP Login Detection
; Author: Enhanced by AI Assistant
; Date: 2025-01-06
; Status: Optimized code, enhanced RDP login functionality

#include <InetConstants.au3>
#include <GuiConstantsEx.au3>
#include <EditConstants.au3>
#include <AutoItConstants.au3>
#include <Inet.au3>
#include <File.au3>
#include <ListViewConstants.au3>
#include <ProgressConstants.au3>
#include <StaticConstants.au3>
#include <WindowsConstants.au3>
#include <Array.au3>
#include <Date.au3>
#include <GUIEdit.au3>
#include <ScrollBarsConstants.au3>
#include <ComboConstants.au3>
#include <ButtonConstants.au3>
#include <MsgBoxConstants.au3>

; Global Constants
Global Const $APP_VERSION = "3.1"
Global Const $LOG_FILE = @ScriptDir & "\FastConfig.log"
Global Const $CONFIG_FILE = @ScriptDir & "\FastConfig.ini"
Global Const $BACKUP_DIR = @ScriptDir & "\Backups"
Global Const $RDP_LOG_FILE = "C:\ProgramData\rdp_logons.json"
Global Const $DEFAULT_RDP_DAYS = 7

; Global Variables
Global $g_hGUI, $g_hProgress, $g_hStatus, $g_hLog
Global $g_bCancelOperation = False
Global $g_iCurrentStep = 0
Global $g_iTotalSteps = 0
Global $g_sWindowsVersion = ""
Global $g_bProcessingMode = False
Global $g_iProcessingAnimationStep = 0
Global $g_sLastRDPCache = "" ; Cache for RDP data to improve performance
Global $g_iLastRDPCacheTime = 0 ; Timestamp of last RDP cache
Global $g_bRDPHistoryLoaded = False ; Track if RDP history has been loaded
Global $g_hTabMain ; Tab control handle for tab change detection

; Software URLs - Enhanced with version-specific URLs and fallbacks
; Structure: [Name, Win6.3_URL, Win10.0_URL, Default_URL, Fallback_URL, Filename]
Global $g_aSoftwareURLs[14][6] = [ _
    ["Chrome", "https://archive.org/download/browser_02.05.2022/Browser/ChromeSetup.exe", "https://dl.google.com/dl/chrome/install/googlechromestandaloneenterprise64.msi", "https://dl.google.com/dl/chrome/install/googlechromestandaloneenterprise64.msi", "https://files.cloudmini.net/ChromeSetup.exe", "chrome_installer.exe"], _
    ["Firefox", "https://download.mozilla.org/?product=firefox-esr115-latest-ssl&os=win64&lang=en-US", "https://download.mozilla.org/?product=firefox-latest&os=win64&lang=en-US", "https://download.mozilla.org/?product=firefox-latest&os=win64&lang=en-US", "https://files.cloudmini.net/FirefoxSetup.exe", "firefox_installer.exe"], _
    ["Edge", "https://files.cloudmini.net/MicrosoftEdgeSetup.exe", "https://c2rsetup.officeapps.live.com/c2r/downloadEdge.aspx?ProductreleaseID=Edge&platform=Default&version=Edge&source=EdgeStablePage&Channel=Stable&language=en", "https://c2rsetup.officeapps.live.com/c2r/downloadEdge.aspx?ProductreleaseID=Edge&platform=Default&version=Edge&source=EdgeStablePage&Channel=Stable&language=en", "https://files.cloudmini.net/MicrosoftEdgeSetup.exe", "edge_installer.exe"], _
    ["Opera", "https://get.geo.opera.com/pub/opera/desktop/88.0.4412.74/win/Opera_88.0.4412.74_Setup_x64.exe", "https://download.opera.com/download/get/?id=42784&location=413&nothanks=yes&sub=marine", "https://download.opera.com/download/get/?id=42784&location=413&nothanks=yes&sub=marine", "https://files.cloudmini.net/OperaSetup.exe", "opera_installer.exe"], _
    ["Brave", "https://github.com/brave/brave-browser/releases/download/v1.43.93/BraveBrowserStandaloneSilentSetup.exe", "https://laptop-updates.brave.com/latest/winx64", "https://referrals.brave.com/latest/BraveBrowserSetup.exe", "https://files.cloudmini.net/BraveBrowserSetup.exe", "brave_installer.exe"], _
    ["Centbrowser", "https://static.centbrowser.com/win_stable/5.2.1168.83/centbrowser_5.2.1168.83_x64.exe", "https://static.centbrowser.com/win_stable/5.2.1168.83/centbrowser_5.2.1168.83_x64.exe", "https://static.centbrowser.com/win_stable/5.2.1168.83/centbrowser_5.2.1168.83_x64.exe", "https://files.cloudmini.net/CentbrowserSetup.exe", "centbrowser.exe"], _
    ["Bitvise SSH", "https://dl.bitvise.com/BvSshClient-Inst.exe", "https://dl.bitvise.com/BvSshClient-Inst.exe", "https://dl.bitvise.com/BvSshClient-Inst.exe", "https://files.cloudmini.net/BvSshClient-Inst.exe", "BvSshClient-Inst.exe"], _
    ["Proxifier", "https://www.proxifier.com/download/ProxifierSetup.exe", "https://www.proxifier.com/download/ProxifierSetup.exe", "https://www.proxifier.com/download/ProxifierSetup.exe", "https://files.cloudmini.net/ProxifierSetup.exe", "ProxifierSetup.exe"], _
    ["WinRAR", "https://www.rarlab.com/rar/winrar-x64-621.exe", "https://www.rarlab.com/rar/winrar-x64-621.exe", "https://www.rarlab.com/rar/winrar-x64-621.exe", "https://files.cloudmini.net/winrar-x64.exe", "winrar.exe"], _
    ["7-Zip", "https://www.7-zip.org/a/7z2201-x64.exe", "https://www.7-zip.org/a/7z2201-x64.exe", "https://www.7-zip.org/a/7z2201-x64.exe", "https://files.cloudmini.net/7z-x64.exe", "7zip.exe"], _
    ["Notepad++", "https://github.com/notepad-plus-plus/notepad-plus-plus/releases/download/v8.5.4/npp.8.5.4.Installer.x64.exe", "https://github.com/notepad-plus-plus/notepad-plus-plus/releases/download/v8.5.4/npp.8.5.4.Installer.x64.exe", "https://github.com/notepad-plus-plus/notepad-plus-plus/releases/download/v8.5.4/npp.8.5.4.Installer.x64.exe", "https://files.cloudmini.net/npp.Installer.x64.exe", "notepadpp.exe"], _
    ["VLC", "https://get.videolan.org/vlc/3.0.18/win64/vlc-3.0.18-win64.exe", "https://get.videolan.org/vlc/3.0.18/win64/vlc-3.0.18-win64.exe", "https://get.videolan.org/vlc/3.0.18/win64/vlc-3.0.18-win64.exe", "https://files.cloudmini.net/vlc-win64.exe", "vlc.exe"] _
]

; Initialize application
_InitializeApp()

; Detect Windows version
$g_sWindowsVersion = _GetWindowsVersion()

; Hotkeys
HotKeySet("{ESC}", "_ExitApp")
HotKeySet("{F1}", "_ShowHelp")
HotKeySet("{F5}", "_RefreshStatus")

; Helper function to repeat strings (for compatibility)
Func _StringRepeat($sChar, $iCount)
    Local $sResult = ""
    For $i = 1 To $iCount
        $sResult &= $sChar
    Next
    Return $sResult
EndFunc

; Toggle password visibility
Func _TogglePasswordVisibility()
    Local $sCurrentPassword = GUICtrlRead($WPASSWORD)
    Local $aPos = ControlGetPos($g_hGUI, "", $WPASSWORD)

    ; Delete old control
    GUICtrlDelete($WPASSWORD)

    ; Create new control with appropriate style
    If _IsChecked($WPASSSHOW) Then
        ; Show password - normal input
        Global $WPASSWORD = GUICtrlCreateInput($sCurrentPassword, $aPos[0], $aPos[1], $aPos[2], $aPos[3])
    Else
        ; Hide password - password input
        Global $WPASSWORD = GUICtrlCreateInput($sCurrentPassword, $aPos[0], $aPos[1], $aPos[2], $aPos[3], $ES_PASSWORD)
    EndIf

    GUICtrlSetFont($WPASSWORD, 9)
    GUICtrlSetTip($WPASSWORD, "Strong password should have:" & @CRLF & "• At least 8 characters" & @CRLF & "• Mix of upper and lowercase" & @CRLF & "• Numbers and special characters")

    ; Validate the password after toggle
    _ValidatePassword()
EndFunc

; Validate password strength and provide feedback
Func _ValidatePassword()
    Local $sPassword = GUICtrlRead($WPASSWORD)
    Local $sStrength = ""
    Local $iColor = 0xFF0000 ; Red by default

    If $sPassword = "" Then
        $sStrength = ""
        GUICtrlSetData($WPASS_STRENGTH, "")
        Return
    ElseIf StringLen($sPassword) < 4 Then
        $sStrength = "Too Short"
        $iColor = 0xFF0000 ; Red
    ElseIf StringLen($sPassword) < 6 Then
        $sStrength = "Weak"
        $iColor = 0xFF8000 ; Orange
    ElseIf StringLen($sPassword) < 8 Then
        If _HasMixedCase($sPassword) Or _HasNumbers($sPassword) Then
            $sStrength = "Medium"
            $iColor = 0xFFFF00 ; Yellow
        Else
            $sStrength = "Weak"
            $iColor = 0xFF8000 ; Orange
        EndIf
    Else
        Local $iScore = 0
        If _HasMixedCase($sPassword) Then $iScore += 1
        If _HasNumbers($sPassword) Then $iScore += 1
        If _HasSpecialChars($sPassword) Then $iScore += 1

        Switch $iScore
            Case 0, 1
                $sStrength = "Medium"
                $iColor = 0xFFFF00 ; Yellow
            Case 2
                $sStrength = "Strong"
                $iColor = 0x80FF00 ; Light Green
            Case 3
                $sStrength = "Very Strong"
                $iColor = 0x00FF00 ; Green
        EndSwitch
    EndIf

    ; Update password strength indicator (we'll add this label)
    If $sStrength <> "" Then
        _UpdatePasswordStrengthIndicator($sStrength, $iColor)
    EndIf
EndFunc

; Helper functions for password validation
Func _HasMixedCase($sPassword)
    Return StringRegExp($sPassword, "[a-z]") And StringRegExp($sPassword, "[A-Z]")
EndFunc

Func _HasNumbers($sPassword)
    Return StringRegExp($sPassword, "[0-9]")
EndFunc

Func _HasSpecialChars($sPassword)
    Return StringRegExp($sPassword, "[!@#$%^&*()_+=\[\]{};':,.<>/?-]")
EndFunc

; Update password strength indicator
Func _UpdatePasswordStrengthIndicator($sStrength, $iColor)
    GUICtrlSetData($WPASS_STRENGTH, "Strength: " & $sStrength)
    GUICtrlSetColor($WPASS_STRENGTH, $iColor)
EndFunc

; Global variable to track last password for change detection
Global $g_sLastPassword = ""

; Check for password changes (called by timer)
Func _CheckPasswordChange()
    Local $sCurrentPassword = GUICtrlRead($WPASSWORD)
    If $sCurrentPassword <> $g_sLastPassword Then
        $g_sLastPassword = $sCurrentPassword
        _ValidatePassword()
    EndIf
EndFunc
; Create main GUI with improved design - Title will be updated after Windows version detection
$g_hGUI = GUICreate("FastConfigVPS v" & $APP_VERSION, 500, 620, -1, -1, $WS_SIZEBOX + $WS_MAXIMIZEBOX)

; Create menu
Local $hMenu = GUICtrlCreateMenu("&File")
GUICtrlCreateMenuItem("E&xit", $hMenu)

Local $hHelpMenu = GUICtrlCreateMenu("&Help")
GUICtrlCreateMenuItem("&About", $hHelpMenu)
GUICtrlCreateMenuItem("&Check Updates", $hHelpMenu)

; Create main tab control
Local $hTabMain = GUICtrlCreateTab(5, 5, 490, 450)
$g_hTabMain = $hTabMain ; Store for tab change detection

; Tab 1: Software Installation (moved to first position)
Local $hTab1 = GUICtrlCreateTabItem("Software Installation")

; Browser section
GUICtrlCreateGroup("Web Browsers", 15, 40, 460, 115)
Global $CHROME = GUICtrlCreateCheckbox("Google Chrome (Latest)", 25, 60, 200, 22)
Global $FF = GUICtrlCreateCheckbox("Mozilla Firefox (Latest)", 25, 85, 200, 22)
Global $OPERA = GUICtrlCreateCheckbox("Opera Browser", 25, 110, 200, 22)
Global $EDGE = GUICtrlCreateCheckbox("Microsoft Edge", 250, 60, 200, 22)
Global $BRAVE = GUICtrlCreateCheckbox("Brave Browser", 250, 85, 200, 22)
Global $CENTBROWSER = GUICtrlCreateCheckbox("Centbrowser", 250, 110, 200, 22)

; Development & Utilities section
GUICtrlCreateGroup("Development & Utilities", 15, 165, 460, 95)
Global $BIT = GUICtrlCreateCheckbox("Bitvise SSH Client", 25, 185, 200, 22)
Global $NOTEPADPP = GUICtrlCreateCheckbox("Notepad++", 25, 210, 200, 22)
Global $WINRAR = GUICtrlCreateCheckbox("WinRAR", 25, 235, 200, 22)
Global $PROXIFIER = GUICtrlCreateCheckbox("Proxifier", 250, 185, 200, 22)
Global $SEVENZIP = GUICtrlCreateCheckbox("7-Zip", 250, 210, 200, 22)
Global $VLC = GUICtrlCreateCheckbox("VLC Media Player", 250, 235, 200, 22)

; Installation Options
GUICtrlCreateGroup("Installation Options", 15, 270, 460, 65)
Global $SILENT_INSTALL = GUICtrlCreateCheckbox("Silent Installation (No User Interaction)", 25, 290, 300, 22)
GUICtrlSetState(-1, $GUI_CHECKED)
Global $DOWNLOAD_ONLY = GUICtrlCreateCheckbox("Download Only (Don't Install)", 25, 315, 300, 22)

; Tab 2: System Configuration
Local $hTab2 = GUICtrlCreateTabItem("System Config")
Global $UAC = GUICtrlCreateCheckbox("Disable UAC", 15, 40, 200, 25)
GUICtrlSetState(-1, $GUI_CHECKED)
Global $IEESC = GUICtrlCreateCheckbox("Turn Off IE Enhanced Security", 15, 70, 200, 25)
GUICtrlSetState(-1, $GUI_CHECKED)
Global $WINUPDATE = GUICtrlCreateCheckbox("Disable Windows Update", 15, 100, 200, 25)
GUICtrlSetState(-1, $GUI_CHECKED)
Global $TRAYICON = GUICtrlCreateCheckbox("Show All System Tray Icons", 15, 130, 200, 25)
GUICtrlSetState(-1, $GUI_CHECKED)
Global $SMALLICON = GUICtrlCreateCheckbox("Taskbar Small Icons", 15, 160, 200, 25)
; GUICtrlSetState(-1, $GUI_CHECKED) ; Unchecked by default
Global $FIREWALL = GUICtrlCreateCheckbox("Turn Off Windows Firewall", 15, 190, 200, 25)
; GUICtrlSetState(-1, $GUI_CHECKED) ; Unchecked by default

; Password section with improved layout
GUICtrlCreateGroup("Windows Password", 15, 220, 460, 80)
Global $WPASSCHANGE = GUICtrlCreateCheckbox("Change Windows Password", 25, 245, 200, 25)
; GUICtrlSetState(-1, $GUI_CHECKED) ; Unchecked by default - user decides when to change password
GUICtrlCreateLabel("New Password:", 25, 275, 100, 20)
Global $WPASSWORD = GUICtrlCreateInput("", 130, 270, 200, 25, $ES_PASSWORD)
GUICtrlSetTip($WPASSWORD, "Strong password should have:" & @CRLF & "• At least 8 characters" & @CRLF & "• Mix of upper and lowercase" & @CRLF & "• Numbers and special characters")
Global $WPASSSHOW = GUICtrlCreateCheckbox("Show Password", 340, 275, 100, 20)
Global $WPASS_STRENGTH = GUICtrlCreateLabel("", 130, 295, 200, 15)
GUICtrlSetFont($WPASS_STRENGTH, 8, 600) ; Bold, smaller font

; Additional system options
GUICtrlCreateGroup("Performance & Optimization", 15, 310, 460, 90)
Global $DEFRAG = GUICtrlCreateCheckbox("Schedule Disk Defragmentation", 25, 330, 200, 20)
Global $CLEANUP = GUICtrlCreateCheckbox("Run Disk Cleanup", 25, 355, 200, 20)
Global $SERVICES = GUICtrlCreateCheckbox("Optimize Services", 25, 380, 200, 20)
Global $STARTUP = GUICtrlCreateCheckbox("Optimize Startup Programs", 250, 330, 200, 20)
Global $VISUAL = GUICtrlCreateCheckbox("Optimize Visual Effects", 250, 355, 200, 20)
Global $POWER = GUICtrlCreateCheckbox("Set High Performance Power Plan", 250, 380, 200, 20)


; Tab 3: Network & Advanced
Local $hTab3 = GUICtrlCreateTabItem("Network & Advanced")

; Network Configuration
GUICtrlCreateGroup("Network Configuration", 15, 40, 460, 180)
Global $SETIP_DNS = GUICtrlCreateCheckbox("Configure Static IP & DNS", 25, 65, 200, 25)
; GUICtrlSetState(-1, $GUI_CHECKED) ; Unchecked by default

GUICtrlCreateLabel("IP Address | Subnet | Gateway:", 25, 95, 200, 20)
Global $SETIP_DNS_IP = GUICtrlCreateInput("Detecting...", 25, 115, 300, 25)
GUICtrlSetTip(-1, "Format: IP|Subnet|Gateway (e.g., 192.168.1.100|255.255.255.0|192.168.1.1)")

GUICtrlCreateLabel("DNS Servers:", 25, 145, 100, 20)
Global $SETIP_DNS_DNS_LIST = GUICtrlCreateCombo("", 130, 142, 150, 25, $CBS_DROPDOWNLIST)
GUICtrlSetData(-1, "Google DNS (8.8.8.8)|Cloudflare DNS (1.1.1.1)|OpenDNS (208.67.222.222)|Quad9 DNS (9.9.9.9)", "Google DNS (8.8.8.8)")

Global $DNS_CUSTOM = GUICtrlCreateCheckbox("Custom DNS:", 25, 175, 80, 20)
Global $DNS_CUSTOM_INPUT = GUICtrlCreateInput("", 110, 172, 200, 25)
GUICtrlSetState($DNS_CUSTOM_INPUT, $GUI_DISABLE)
GUICtrlSetTip($DNS_CUSTOM_INPUT, "Enter custom DNS servers separated by comma (e.g., 1.1.1.1,1.0.0.1)")

; System Activation & Maintenance
GUICtrlCreateGroup("System Activation & Maintenance", 15, 230, 460, 80)
Global $ACTIVE = GUICtrlCreateCheckbox("Activate Windows (180 days)", 25, 255, 200, 25)
; GUICtrlSetState(-1, $GUI_CHECKED) ; Unchecked by default
Global $HDD = GUICtrlCreateCheckbox("Extend System Drive", 250, 255, 200, 25)
GUICtrlSetState(-1, $GUI_CHECKED)

Global $BACKUP_REGISTRY = GUICtrlCreateCheckbox("Create Registry Backup", 25, 285, 200, 25)
; GUICtrlSetState(-1, $GUI_CHECKED) ; Unchecked by default
Global $UPDATE_DRIVERS = GUICtrlCreateCheckbox("Update System Drivers", 250, 285, 200, 25)

; Windows Edition Conversion
GUICtrlCreateGroup("Windows Edition Conversion (Evaluation to Standard)", 15, 320, 460, 110)
GUICtrlCreateLabel("Convert Windows Evaluation to Standard Edition:", 25, 345, 300, 20)
Global $CONVERT_2012 = GUICtrlCreateCheckbox("Windows Server 2012", 25, 365, 150, 25)
Global $CONVERT_2016 = GUICtrlCreateCheckbox("Windows Server 2016", 200, 365, 150, 25)
Global $CONVERT_2019 = GUICtrlCreateCheckbox("Windows Server 2019", 25, 395, 150, 25)
Global $CONVERT_2022 = GUICtrlCreateCheckbox("Windows Server 2022", 200, 395, 150, 25)
GUICtrlCreateLabel("Note: Only select the version that matches your current Windows installation", 25, 415, 400, 15)
GUICtrlSetFont(-1, 8, 400, 2) ; Italic text

; Tab 4: Logs & Logon
Local $hTab4 = GUICtrlCreateTabItem("Logs & Logon")

; Login History viewer
GUICtrlCreateLabel("Windows VPS Login History:", 15, 40, 200, 20)
$g_hLog = GUICtrlCreateEdit("", 15, 65, 460, 250, $ES_READONLY + $ES_MULTILINE + $WS_VSCROLL)
GUICtrlSetFont(-1, 9, 400, 0, "Consolas")

; Login controls
Global $LOG_CLEAR = GUICtrlCreateButton("Clear History", 15, 325, 80, 30)
Global $LOG_SAVE = GUICtrlCreateButton("Export History", 105, 325, 80, 30)
Global $LOG_REFRESH = GUICtrlCreateButton("Get IP Logon", 195, 325, 120, 30)

; Application Logs section
GUICtrlCreateGroup("Application Logs", 15, 365, 460, 65)
Global $g_hAppLog = GUICtrlCreateEdit("", 25, 385, 440, 35, $ES_READONLY + $ES_MULTILINE + $WS_VSCROLL)
GUICtrlSetFont(-1, 8, 400, 0, "Consolas")

; Settings
GUICtrlCreateGroup("Settings", 325, 325, 150, 35)
Global $VERBOSE_LOG = GUICtrlCreateCheckbox("Verbose Log", 335, 340, 100, 15)

GUICtrlCreateTabItem("") ; End tabs
; Progress bar and status
$g_hProgress = GUICtrlCreateProgress(5, 460, 490, 25)
$g_hStatus = GUICtrlCreateLabel("Ready to configure system...", 5, 490, 350, 20, $SS_SUNKEN)

; Windows version display
Global $g_hVersionLabel = GUICtrlCreateLabel("Detecting Windows version...", 360, 490, 135, 20, $SS_SUNKEN)

; Control buttons - Single main button for fast config (with proper spacing)
Global $BUTTONRUN = GUICtrlCreateButton("🚀 Start Configuration", 100, 520, 300, 40)
GUICtrlSetFont(-1, 11, 600)
GUICtrlSetColor(-1, 0xFFFFFF) ; White text
GUICtrlSetBkColor(-1, 0x0078D4) ; Blue background

; Footer removed

; Update GUI title with Windows version
Local $sWindowsDisplayName = _GetWindowsDisplayName($g_sWindowsVersion)
WinSetTitle($g_hGUI, "", "FastConfigVPS v" & $APP_VERSION & " - " & $sWindowsDisplayName)

; Show GUI
GUISetState(@SW_SHOW, $g_hGUI)

; Update version label in status bar
GUICtrlSetData($g_hVersionLabel, $g_sWindowsVersion & " detected")
GUICtrlSetTip($g_hVersionLabel, $sWindowsDisplayName)

; Initialize logging
_WriteLog("FastConfigVPS v" & $APP_VERSION & " started")
_WriteLog("Detected Windows version: " & $g_sWindowsVersion & " (" & $sWindowsDisplayName & ")")
_UpdateStatus("Application ready - " & $sWindowsDisplayName)

; Initialize login history display (manual loading only)
GUICtrlSetData($g_hLog, "Windows VPS RDP Login History" & @CRLF & _StringRepeat("=", 30) & @CRLF & @CRLF & "Click 'Get IP Logon' button to view recent RDP login IP addresses." & @CRLF & @CRLF & "This will show you which IP addresses have logged into this server via RDP.")

; Auto-detect current network configuration (silent)
Local $sDetectedNetwork = _DetectCurrentNetworkConfig()
GUICtrlSetData($SETIP_DNS_IP, $sDetectedNetwork)

; Set up password validation timer
AdlibRegister("_CheckPasswordChange", 500) ; Check every 500ms

; Optional: Start background RDP refresh after 60 seconds (uncomment to enable)
; AdlibRegister("_BackgroundRDPRefresh", 60000) ; Refresh every 60 seconds

; Main event loop
While 1
    Local $nMsg = GUIGetMsg()
    Switch $nMsg
        Case $GUI_EVENT_CLOSE
            _ExitApp()

        Case $BUTTONRUN
            ; Ignore clicks when processing to prevent multiple runs
            If $g_bProcessingMode Then
                _WriteLog("BUTTON CLICK: Ignored click during processing mode")
                ContinueLoop
            EndIf
            _StartConfiguration()

        Case $LOG_CLEAR
            GUICtrlSetData($g_hLog, "")
            _WriteLog("Login history cleared by user")

        Case $LOG_SAVE
            _SaveLoginHistoryToFile()

        Case $LOG_REFRESH
            _RefreshLoginHistory()

        Case $WPASSSHOW
            _TogglePasswordVisibility()

        Case $WPASSWORD
            _ValidatePassword()

        Case $DNS_CUSTOM
            If _IsChecked($DNS_CUSTOM) Then
                GUICtrlSetState($DNS_CUSTOM_INPUT, $GUI_ENABLE)
                GUICtrlSetState($SETIP_DNS_DNS_LIST, $GUI_DISABLE)
            Else
                GUICtrlSetState($DNS_CUSTOM_INPUT, $GUI_DISABLE)
                GUICtrlSetState($SETIP_DNS_DNS_LIST, $GUI_ENABLE)
            EndIf
            


    EndSwitch
WEnd
; ===============================================================================================================
; MAIN FUNCTIONS
; ===============================================================================================================

; Initialize application
Func _InitializeApp()
    ; Create directories if they don't exist
    If Not FileExists($BACKUP_DIR) Then DirCreate($BACKUP_DIR)

    ; Initialize log file
    If Not FileExists($LOG_FILE) Then
        FileWrite($LOG_FILE, "FastConfigVPS v" & $APP_VERSION & " Log File" & @CRLF)
        FileWrite($LOG_FILE, "Created: " & @YEAR & "/" & @MON & "/" & @MDAY & " " & @HOUR & ":" & @MIN & ":" & @SEC & @CRLF)
        FileWrite($LOG_FILE, _StringRepeat("=", 50) & @CRLF)
    EndIf
EndFunc

; Start main configuration process
Func _StartConfiguration()
    _WriteLog("Starting configuration process...")
    _UpdateStatus("Preparing configuration...")

    ; Reset progress
    $g_iCurrentStep = 0
    $g_iTotalSteps = _CountSelectedOptions()

    If $g_iTotalSteps = 0 Then
        MsgBox($MB_ICONWARNING, "Warning", "No options selected for configuration!")
        Return
    EndIf

    ; Backup functionality removed for cleaner interface

    ; Update button to show processing state
    _SetProcessingMode(True)

    ; Start configuration
    _ProcessSystemConfiguration()
    _ProcessSoftwareInstallation()
    _ProcessNetworkConfiguration()
    _ProcessAdvancedOptions()

    ; Restore button to normal state
    _SetProcessingMode(False)

    ; Complete with success animation
    _UpdateProgress(100)
    _UpdateStatus("Configuration completed successfully!")
    _WriteLog("Configuration process completed successfully")
    
    ; Show success state briefly before restoring
    _SetSuccessMode()

    ; Restart explorer
    _RestartExplorer()

    MsgBox($MB_ICONINFORMATION, "Success", "Configuration completed successfully!" & @CRLF & @CRLF & "Some changes may require a system restart to take effect.", 10)
EndFunc
; Process system configuration
Func _ProcessSystemConfiguration()
    _UpdateStatus("Configuring system settings...")

    ; UAC Configuration
    If _IsChecked($UAC) Then
        If _SafeRegWrite("HKLM64\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System", "EnableLUA", "REG_DWORD", 0) Then
            _WriteLog("UAC disabled successfully")
            _IncrementProgress("Disable UAC")
        EndIf
    EndIf

    ; IE Enhanced Security Configuration
    If _IsChecked($IEESC) Then
        If _SafeRegWrite("HKLM64\SOFTWARE\Microsoft\Active Setup\Installed Components\{A509B1A7-37EF-4b3f-8CFC-4F3A74704073}", "IsInstalled", "REG_DWORD", 0) And _
           _SafeRegWrite("HKLM64\SOFTWARE\Microsoft\Active Setup\Installed Components\{A509B1A8-37EF-4b3f-8CFC-4F3A74704073}", "IsInstalled", "REG_DWORD", 0) Then
            _WriteLog("IE Enhanced Security disabled successfully")
            _IncrementProgress("Turn Off IE Enhanced Security")
        EndIf
    EndIf

    ; Windows Update Configuration
    If _IsChecked($WINUPDATE) Then
        If _SafeRegWrite("HKLM64\SOFTWARE\Microsoft\Windows\CurrentVersion\WindowsUpdate\Auto Update", "AUOptions", "REG_DWORD", 1) Then
            _WriteLog("Windows Update disabled successfully")
            _IncrementProgress("Disable Windows Update")
        EndIf
    EndIf

    ; System Tray Icons
    If _IsChecked($TRAYICON) Then
        If _SafeRegWrite("HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Explorer", "EnableAutoTray", "REG_DWORD", 0) Then
            _WriteLog("System tray icons configured to show all")
            _IncrementProgress("Show All System Tray Icons")
        EndIf
    EndIf

    ; Taskbar Small Icons
    If _IsChecked($SMALLICON) Then
        If _SafeRegWrite("HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced", "TaskbarSmallIcons", "REG_DWORD", 1) Then
            _WriteLog("Taskbar configured to use small icons")
            _IncrementProgress("Taskbar Small Icons")
        EndIf
    EndIf

    ; Windows Firewall
    If _IsChecked($FIREWALL) Then
        Local $iResult = RunWait(@ComSpec & " /C NetSh Advfirewall set allprofiles state off", "", @SW_HIDE)
        If $iResult = 0 Then
            _WriteLog("Windows Firewall disabled successfully")
            _IncrementProgress("Turn Off Windows Firewall")
        Else
            _WriteLog("Failed to disable Windows Firewall (Exit code: " & $iResult & ")")
        EndIf
    EndIf

    ; Windows Password Change
    If _IsChecked($WPASSCHANGE) Then
        Local $sPassword = GUICtrlRead($WPASSWORD)
        If $sPassword <> "" Then
            If _ChangeWindowsPassword($sPassword) Then
                _WriteLog("Windows password changed successfully")
                _IncrementProgress("Change Windows Password")
            Else
                _WriteLog("Failed to change Windows password")
            EndIf
        Else
            _WriteLog("Password change skipped - no password provided")
        EndIf
    EndIf

EndFunc
; Process software installation
Func _ProcessSoftwareInstallation()
    _UpdateStatus("Installing selected software...")

    Local $bSilentInstall = _IsChecked($SILENT_INSTALL)
    Local $bDownloadOnly = _IsChecked($DOWNLOAD_ONLY)

    ; Google Chrome
    If _IsChecked($CHROME) Then
        _InstallSoftware("Chrome", $bSilentInstall, $bDownloadOnly)
    EndIf

    ; Mozilla Firefox
    If _IsChecked($FF) Then
        _InstallSoftware("Firefox", $bSilentInstall, $bDownloadOnly)
    EndIf

    ; Microsoft Edge
    If _IsChecked($EDGE) Then
        _InstallSoftware("Edge", $bSilentInstall, $bDownloadOnly)
    EndIf

    ; Opera Browser
    If _IsChecked($OPERA) Then
        _InstallSoftware("Opera", $bSilentInstall, $bDownloadOnly)
    EndIf

    ; Brave Browser
    If _IsChecked($BRAVE) Then
        _InstallSoftware("Brave", $bSilentInstall, $bDownloadOnly)
    EndIf

    ; Centbrowser
    If _IsChecked($CENTBROWSER) Then
        _InstallSoftware("Centbrowser", $bSilentInstall, $bDownloadOnly)
    EndIf

    ; Bitvise SSH Client
    If _IsChecked($BIT) Then
        _InstallSoftware("Bitvise SSH", $bSilentInstall, $bDownloadOnly)
    EndIf

    ; Proxifier
    If _IsChecked($PROXIFIER) Then
        _InstallSoftware("Proxifier", $bSilentInstall, $bDownloadOnly)
    EndIf

    ; Notepad++
    If _IsChecked($NOTEPADPP) Then
        _InstallSoftware("Notepad++", $bSilentInstall, $bDownloadOnly)
    EndIf

    ; 7-Zip
    If _IsChecked($SEVENZIP) Then
        _InstallSoftware("7-Zip", $bSilentInstall, $bDownloadOnly)
    EndIf

    ; WinRAR
    If _IsChecked($WINRAR) Then
        _InstallSoftware("WinRAR", $bSilentInstall, $bDownloadOnly)
    EndIf

    ; VLC Media Player
    If _IsChecked($VLC) Then
        _InstallSoftware("VLC", $bSilentInstall, $bDownloadOnly)
    EndIf
EndFunc
; Install software with enhanced error handling and fallback URLs
Func _InstallSoftware($sSoftwareName, $bSilentInstall = True, $bDownloadOnly = False)

    ; Get URLs for this software
    Local $aURLs = _GetDownloadURL($sSoftwareName)
    If Not IsArray($aURLs) Or $aURLs[0] = "" Then
        _WriteLog("No download URL available for: " & $sSoftwareName)
        Return
    EndIf

    Local $sURL = $aURLs[0]
    Local $sFallbackURL = $aURLs[1]
    
    ; Find software in array to get filename
    Local $iIndex = -1
    For $i = 0 To UBound($g_aSoftwareURLs) - 1
        If $g_aSoftwareURLs[$i][0] = $sSoftwareName Then
            $iIndex = $i
            ExitLoop
        EndIf
    Next

    If $iIndex = -1 Then
        _WriteLog("Software not found in database: " & $sSoftwareName)
        Return
    EndIf

    Local $sFileName = $g_aSoftwareURLs[$iIndex][5]
    Local $sFilePath = @TempDir & "\" & $sFileName

    _UpdateStatus("Downloading " & $sSoftwareName & "...")
    _WriteLog("Starting download: " & $sSoftwareName & " from " & $sURL)

    ; Try primary URL first
    Local $bDownloadSuccess = _DownloadWithFallback($sURL, $sFallbackURL, $sFilePath, $sSoftwareName)
    
    If Not $bDownloadSuccess Then
        _WriteLog("All download attempts failed for " & $sSoftwareName)
        
        ; Special handling for known problematic browsers on Windows 2012 R2
        If $g_sWindowsVersion = "6.3" And ($sSoftwareName = "Edge" Or $sSoftwareName = "Brave" Or $sSoftwareName = "Opera") Then
            _WriteLog("COMPATIBILITY NOTE: " & $sSoftwareName & " may have limited compatibility with Windows Server 2012 R2")
            MsgBox($MB_ICONWARNING, "Browser Compatibility Warning", _
                $sSoftwareName & " download failed on Windows Server 2012 R2." & @CRLF & @CRLF & _
                "This browser may have limited or no official support for Server 2012 R2." & @CRLF & @CRLF & _
                "Recommendation: Use Chrome or Firefox for better compatibility." & @CRLF & @CRLF & _
                "Check the log for detailed download error information.", 10)
        EndIf
        
        Return
    EndIf

    If $bDownloadOnly Then
        _WriteLog("Download only mode - skipping installation of " & $sSoftwareName)
        _IncrementProgress("Downloaded " & $sSoftwareName)
        Return
    EndIf

    ; Install software
    _UpdateStatus("Installing " & $sSoftwareName & "...")
    Local $bInstallSuccess = False

    Switch $sSoftwareName
        Case "Chrome"
            $bInstallSuccess = _InstallChrome($sFilePath, $bSilentInstall)
        Case "Firefox"
            $bInstallSuccess = _InstallFirefox($sFilePath, $bSilentInstall)
        Case "Edge"
            $bInstallSuccess = _InstallEdge($sFilePath, $bSilentInstall)
        Case "Brave"
            $bInstallSuccess = _InstallBrave($sFilePath, $bSilentInstall)
        Case "Bitvise SSH"
            $bInstallSuccess = _InstallBitvise($sFilePath, $bSilentInstall)
        Case "Centbrowser"
            $bInstallSuccess = _InstallGeneric($sFilePath, $sSoftwareName, $bSilentInstall)
        Case Else
            $bInstallSuccess = _InstallGeneric($sFilePath, $sSoftwareName, $bSilentInstall)
    EndSwitch

    If $bInstallSuccess Then
        _WriteLog("Installation completed: " & $sSoftwareName)
        _IncrementProgress("Installed " & $sSoftwareName)
    Else
        _WriteLog("Installation failed: " & $sSoftwareName)
    EndIf

    ; Cleanup
    FileDelete($sFilePath)
EndFunc

; Download with fallback URL support
Func _DownloadWithFallback($sPrimaryURL, $sFallbackURL, $sFilePath, $sSoftwareName)
    Local $aURLsToTry[2] = [$sPrimaryURL, $sFallbackURL]
    
    _WriteLog("DOWNLOAD DEBUG: Starting download process for " & $sSoftwareName)
    _WriteLog("DOWNLOAD DEBUG: Target file path: " & $sFilePath)
    
    For $i = 0 To 1
        Local $sCurrentURL = $aURLsToTry[$i]
        If $sCurrentURL = "" Then 
            _WriteLog("DOWNLOAD DEBUG: Skipping empty URL (attempt " & ($i + 1) & "/2)")
            ContinueLoop
        EndIf
        
        Local $sURLType = "fallback"
        If $i = 0 Then $sURLType = "primary"
        _WriteLog("DOWNLOAD ATTEMPT " & ($i + 1) & "/2: Trying " & $sURLType & " URL")
        _WriteLog("DOWNLOAD URL: " & $sCurrentURL)
        
        ; Clean up any existing file before download
        If FileExists($sFilePath) Then
            FileDelete($sFilePath)
            _WriteLog("DOWNLOAD DEBUG: Cleaned up existing file before download")
        EndIf
        
        ; Download with progress monitoring
        _WriteLog("DOWNLOAD DEBUG: Starting InetGet for " & $sSoftwareName)
        Local $hDownload = InetGet($sCurrentURL, $sFilePath, $INET_FORCERELOAD, $INET_DOWNLOADBACKGROUND)
        
        If $hDownload = 0 Then
            _WriteLog("DOWNLOAD ERROR: InetGet failed to start for " & $sURLType & " URL")
            ContinueLoop
        EndIf
        
        _WriteLog("DOWNLOAD DEBUG: Download handle created, monitoring progress...")

        ; Monitor download progress with detailed logging
        Local $iTimeout = 300000 ; 5 minutes timeout
        Local $iStartTime = TimerInit()
        Local $iLastSize = 0
        Local $iProgressCounter = 0

        While Not InetGetInfo($hDownload, $INET_DOWNLOADCOMPLETE)
            $iProgressCounter += 1
            Local $iCurrentSize = InetGetInfo($hDownload, $INET_DOWNLOADREAD)
            
            ; Log progress every 50 iterations (approximately every 5 seconds)
            If $iProgressCounter = 50 Or $iProgressCounter = 100 Or $iProgressCounter = 150 Or $iProgressCounter = 200 Then
                _WriteLog("DOWNLOAD PROGRESS: " & $sSoftwareName & " - Downloaded " & $iCurrentSize & " bytes (" & $sURLType & " URL)")
            EndIf
            
            ; Check for timeout
            If TimerDiff($iStartTime) > $iTimeout Then
                InetClose($hDownload)
                _WriteLog("DOWNLOAD TIMEOUT: " & $sSoftwareName & " download timed out after 5 minutes (" & $sURLType & " URL)")
                _WriteLog("DOWNLOAD TIMEOUT: Last downloaded size: " & $iCurrentSize & " bytes")
                ExitLoop ; Try next URL
            EndIf
            
            $iLastSize = $iCurrentSize
            Sleep(100)
        WEnd

        ; Check download completion status
        Local $iBytesRead = InetGetInfo($hDownload, $INET_DOWNLOADREAD)
        Local $iDownloadError = InetGetInfo($hDownload, $INET_DOWNLOADERROR)
        InetClose($hDownload)
        
        _WriteLog("DOWNLOAD STATUS: " & $sSoftwareName & " - Bytes read: " & $iBytesRead & ", Error code: " & $iDownloadError)
        _WriteLog("DOWNLOAD STATUS: File exists: " & FileExists($sFilePath) & ", File size: " & FileGetSize($sFilePath))

        If $iBytesRead > 0 And FileExists($sFilePath) And FileGetSize($sFilePath) > 0 Then
            _WriteLog("DOWNLOAD SUCCESS: " & $sSoftwareName & " downloaded successfully!")
            _WriteLog("DOWNLOAD SUCCESS: Final size: " & $iBytesRead & " bytes from " & $sURLType & " URL")
            _WriteLog("DOWNLOAD SUCCESS: File saved to: " & $sFilePath)
            Return True
        Else
            _WriteLog("DOWNLOAD FAILED: " & $sSoftwareName & " download failed from " & $sURLType & " URL")
            _WriteLog("DOWNLOAD ERROR: URL was: " & $sCurrentURL)
            _WriteLog("DOWNLOAD ERROR: Bytes read: " & $iBytesRead & ", File exists: " & FileExists($sFilePath))
            If FileExists($sFilePath) Then
                _WriteLog("DOWNLOAD ERROR: File size on disk: " & FileGetSize($sFilePath) & " bytes")
            EndIf
            FileDelete($sFilePath) ; Clean up failed download
        EndIf
    Next
    
    _WriteLog("DOWNLOAD FAILURE: All download attempts failed for " & $sSoftwareName)
    Return False
EndFunc
; Specific installation functions
Func _InstallChrome($sFilePath, $bSilent = True)
    Local $sParams = ""
    If $bSilent Then $sParams = "/silent /install"
    Local $iResult = RunWait('"' & $sFilePath & '" ' & $sParams, "", @SW_HIDE)
    Return $iResult = 0
EndFunc

Func _InstallFirefox($sFilePath, $bSilent = True)
    Local $sParams = ""
    If $bSilent Then $sParams = "-ms"
    Local $iResult = RunWait('"' & $sFilePath & '" ' & $sParams, "", @SW_HIDE)
    Return $iResult = 0
EndFunc

Func _InstallEdge($sFilePath, $bSilent = True)
    _WriteLog("EDGE INSTALL: Starting Edge installation process")
    _WriteLog("EDGE INSTALL: Windows Version: " & $g_sWindowsVersion)
    _WriteLog("EDGE INSTALL: File path: " & $sFilePath)
    _WriteLog("EDGE INSTALL: Silent mode requested: " & $bSilent)
    
    ; Special handling for Windows Server 2012 R2 (version 6.3)
    If $g_sWindowsVersion = "6.3" Then
        _WriteLog("EDGE INSTALL: Windows Server 2012 R2 detected - using non-silent installation")
        _WriteLog("EDGE INSTALL: Edge may not support silent installation on Server 2012 R2")
        
        ; Run Edge installer without silent parameters for Server 2012 R2
        ; This allows the installer to handle compatibility issues internally
        _WriteLog("EDGE INSTALL: Launching Edge installer in interactive mode")
        Local $iPID = Run('"' & $sFilePath & '"', "", @SW_SHOW)
        
        If $iPID = 0 Then
            _WriteLog("EDGE INSTALL ERROR: Failed to start Edge installer")
            Return False
        EndIf
        
        _WriteLog("EDGE INSTALL: Edge installer started with PID: " & $iPID)
        _WriteLog("EDGE INSTALL: Waiting for installation to complete (max 10 minutes)")
        
        ; Wait for process to complete with timeout
        Local $bCompleted = ProcessWaitClose($iPID, 600000) ; 10 minutes timeout
        
        If $bCompleted Then
            _WriteLog("EDGE INSTALL: Edge installer process completed")
            
            ; Check for Edge executable in multiple possible locations
            Local $sEdgePath64 = @ProgramFilesDir & "\Microsoft\Edge\Application\msedge.exe"
            Local $sEdgePath32 = @ProgramFilesDir & " (x86)\Microsoft\Edge\Application\msedge.exe"
            Local $sActualEdgePath = ""
            
            If FileExists($sEdgePath64) Then
                $sActualEdgePath = $sEdgePath64
                _WriteLog("EDGE INSTALL SUCCESS: Edge executable found at: " & $sEdgePath64)
            ElseIf FileExists($sEdgePath32) Then
                $sActualEdgePath = $sEdgePath32
                _WriteLog("EDGE INSTALL SUCCESS: Edge executable found at: " & $sEdgePath32)
            Else
                _WriteLog("EDGE INSTALL WARNING: Edge executable not found, but installer completed")
                _WriteLog("EDGE INSTALL WARNING: This may be normal for Server 2012 R2 - Edge might not be compatible")
                Return True ; Return true since installer completed without error
            EndIf
            
            ; Create Desktop shortcut for Windows Server 2012 R2
            If $sActualEdgePath <> "" Then
                _WriteLog("EDGE INSTALL: Creating Desktop shortcut for Windows Server 2012 R2")
                Local $bShortcutCreated = _CreateEdgeDesktopShortcut($sActualEdgePath)
                If $bShortcutCreated Then
                    _WriteLog("EDGE INSTALL SUCCESS: Desktop shortcut created successfully")
                Else
                    _WriteLog("EDGE INSTALL WARNING: Failed to create Desktop shortcut")
                EndIf
            EndIf
            
            Return True
        Else
            _WriteLog("EDGE INSTALL TIMEOUT: Edge installation timed out after 10 minutes")
            ProcessClose($iPID) ; Force close if still running
            Return False
        EndIf
    Else
        ; For Windows 10+ versions, use standard silent installation
        _WriteLog("EDGE INSTALL: Windows 10+ detected - using standard installation method")
        Local $sParams = ""
        If $bSilent Then
            $sParams = "/silent /install"
            _WriteLog("EDGE INSTALL: Using silent parameters: " & $sParams)
        EndIf
        
        _WriteLog("EDGE INSTALL: Running Edge installer with parameters")
        Local $iResult = RunWait('"' & $sFilePath & '" ' & $sParams, "", @SW_HIDE, 600000) ; 10 minutes timeout
        
        _WriteLog("EDGE INSTALL: Edge installer finished with exit code: " & $iResult)
        
        If $iResult = 0 Then
            _WriteLog("EDGE INSTALL SUCCESS: Edge installation completed successfully")
            Return True
        Else
            _WriteLog("EDGE INSTALL ERROR: Edge installation failed with exit code: " & $iResult)
            Return False
        EndIf
    EndIf
EndFunc

; Create Edge Desktop shortcut for Windows Server 2012 R2
Func _CreateEdgeDesktopShortcut($sEdgeExePath)
    _WriteLog("SHORTCUT: Creating Microsoft Edge desktop shortcut")
    _WriteLog("SHORTCUT: Edge executable path: " & $sEdgeExePath)
    
    ; Get Desktop path
    Local $sDesktopPath = @DesktopDir
    Local $sShortcutPath = $sDesktopPath & "\Microsoft Edge.lnk"
    
    _WriteLog("SHORTCUT: Desktop path: " & $sDesktopPath)
    _WriteLog("SHORTCUT: Shortcut will be created at: " & $sShortcutPath)
    
    ; PowerShell command to create shortcut
    Local $sPowerShellCmd = '$WshShell = New-Object -ComObject WScript.Shell; ' & _
                           '$Shortcut = $WshShell.CreateShortcut("' & $sShortcutPath & '"); ' & _
                           '$Shortcut.TargetPath = "' & $sEdgeExePath & '"; ' & _
                           '$Shortcut.IconLocation = "' & $sEdgeExePath & ',0"; ' & _
                           '$Shortcut.Save()'
    
    _WriteLog("SHORTCUT: PowerShell command: " & $sPowerShellCmd)
    
    ; Execute PowerShell command
    Local $iResult = RunWait('powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "' & $sPowerShellCmd & '"', "", @SW_HIDE, 30000)
    
    _WriteLog("SHORTCUT: PowerShell command executed with exit code: " & $iResult)
    
    ; Verify shortcut was created
    If FileExists($sShortcutPath) Then
        _WriteLog("SHORTCUT SUCCESS: Microsoft Edge shortcut created on Desktop")
        _WriteLog("SHORTCUT SUCCESS: Shortcut location: " & $sShortcutPath)
        Return True
    Else
        _WriteLog("SHORTCUT ERROR: Failed to create Microsoft Edge shortcut")
        _WriteLog("SHORTCUT ERROR: Expected location: " & $sShortcutPath)
        Return False
    EndIf
EndFunc

Func _InstallBrave($sFilePath, $bSilent = True)
    _WriteLog("BRAVE INSTALL: Starting Brave installation process")
    _WriteLog("BRAVE INSTALL: Windows Version: " & $g_sWindowsVersion)
    _WriteLog("BRAVE INSTALL: File path: " & $sFilePath)
    _WriteLog("BRAVE INSTALL: Silent mode requested: " & $bSilent)
    
    ; Special handling for Windows Server 2012 R2 (version 6.3)
    If $g_sWindowsVersion = "6.3" Then
        _WriteLog("BRAVE INSTALL: Windows Server 2012 R2 detected - using non-silent installation")
        _WriteLog("BRAVE INSTALL: Brave may not support silent installation on Server 2012 R2")
        
        ; For Server 2012 R2, try running without silent parameters first
        ; But first check if the downloaded file is the "Silent" version which should work
        Local $sFileName = StringLower(_GetFileNameFromPath($sFilePath))
        If StringInStr($sFileName, "silent") Then
            _WriteLog("BRAVE INSTALL: Silent installer detected, attempting silent installation")
            Local $iResult = RunWait('"' & $sFilePath & '" /S', "", @SW_HIDE, 600000) ; 10 minutes timeout
            _WriteLog("BRAVE INSTALL: Silent installer finished with exit code: " & $iResult)
            
            If $iResult = 0 Then
            ; Verify installation
                Local $sBravePath64 = @ProgramFilesDir & "\BraveSoftware\Brave-Browser\Application\brave.exe"
                Local $sBravePath32 = @ProgramFilesDir & " (x86)\BraveSoftware\Brave-Browser\Application\brave.exe"
                
                If FileExists($sBravePath64) Or FileExists($sBravePath32) Then
                    _WriteLog("BRAVE INSTALL SUCCESS: Brave installation completed successfully")
                    Return True
                Else
                    _WriteLog("BRAVE INSTALL WARNING: Silent installation completed but executable not found")
                EndIf
            EndIf
        EndIf
        
        ; If silent method failed or not available, try interactive installation
        _WriteLog("BRAVE INSTALL: Attempting interactive installation for Server 2012 R2")
        Local $iPID = Run('"' & $sFilePath & '"', "", @SW_SHOW)
        
        If $iPID = 0 Then
            _WriteLog("BRAVE INSTALL ERROR: Failed to start Brave installer")
            Return False
        EndIf
        
        _WriteLog("BRAVE INSTALL: Brave installer started with PID: " & $iPID)
        _WriteLog("BRAVE INSTALL: Waiting for installation to complete (max 10 minutes)")
        
        ; Wait for process to complete with timeout
        Local $bCompleted = ProcessWaitClose($iPID, 600000) ; 10 minutes timeout
        
        If $bCompleted Then
            _WriteLog("BRAVE INSTALL: Brave installer process completed")
            
            ; Check for Brave executable in multiple possible locations
            Local $sBravePath64 = @ProgramFilesDir & "\BraveSoftware\Brave-Browser\Application\brave.exe"
            Local $sBravePath32 = @ProgramFilesDir & " (x86)\BraveSoftware\Brave-Browser\Application\brave.exe"
            Local $sActualBravePath = ""
            
            If FileExists($sBravePath64) Then
                $sActualBravePath = $sBravePath64
                _WriteLog("BRAVE INSTALL SUCCESS: Brave executable found at: " & $sBravePath64)
            ElseIf FileExists($sBravePath32) Then
                $sActualBravePath = $sBravePath32
                _WriteLog("BRAVE INSTALL SUCCESS: Brave executable found at: " & $sBravePath32)
            Else
                _WriteLog("BRAVE INSTALL WARNING: Brave executable not found, but installer completed")
                _WriteLog("BRAVE INSTALL WARNING: This may be normal for Server 2012 R2 - Brave might not be compatible")
                Return True ; Return true since installer completed without error
            EndIf
            
            ; Brave installation completed successfully
            
            Return True
        Else
            _WriteLog("BRAVE INSTALL TIMEOUT: Brave installation timed out after 10 minutes")
            ProcessClose($iPID) ; Force close if still running
            Return False
        EndIf
    Else
        ; For Windows 10+ versions, use standard silent installation
        _WriteLog("BRAVE INSTALL: Windows 10+ detected - using standard installation method")
        Local $sParams = ""
        If $bSilent Then
            $sParams = "/S"
            _WriteLog("BRAVE INSTALL: Using silent parameters: " & $sParams)
        EndIf
        
        _WriteLog("BRAVE INSTALL: Running Brave installer with parameters")
        Local $iResult = RunWait('"' & $sFilePath & '" ' & $sParams, "", @SW_HIDE, 600000) ; 10 minutes timeout
        
        _WriteLog("BRAVE INSTALL: Brave installer finished with exit code: " & $iResult)
        
        If $iResult = 0 Then
            _WriteLog("BRAVE INSTALL SUCCESS: Brave installation completed successfully")
            Return True
        Else
            _WriteLog("BRAVE INSTALL ERROR: Brave installation failed with exit code: " & $iResult)
            Return False
        EndIf
    EndIf
EndFunc

; Brave shortcut creation removed per user request

; Helper function to get filename from path
Func _GetFileNameFromPath($sPath)
    Local $aPathParts = StringSplit($sPath, "\")
    If $aPathParts[0] > 0 Then
        Return $aPathParts[$aPathParts[0]]
    EndIf
    Return $sPath
EndFunc

Func _InstallBitvise($sFilePath, $bSilent = True)
    If $bSilent Then
        ; Try silent installation first
        Local $iResult = RunWait('"' & $sFilePath & '" /S', "", @SW_HIDE)
        Return $iResult = 0
    Else
        ; Interactive installation with automation
        Local $iPID = Run('"' & $sFilePath & '"')
        If $iPID = 0 Then Return False

        ; Wait for installer window with timeout
        If Not WinWait("Bitvise SSH Client", "", 30) Then
            ProcessClose($iPID)
            Return False
        EndIf

        ; Automate installation steps
        Local $hWnd = WinGetHandle("Bitvise SSH Client")
        If $hWnd Then
            ; Accept license
            ControlClick($hWnd, "", "[CLASS:Button; TEXT:I agree]")
            Sleep(500)

            ; Click Install
            ControlClick($hWnd, "", "[CLASS:Button; TEXT:Install]")

            ; Wait for completion
            WinWait("Installation Completed", "", 60)
            ControlClick("Installation Completed", "", "[CLASS:Button; TEXT:OK]")

            ; Close any remaining processes
            ProcessClose("BvSsh.exe")
            Return True
        EndIf
    EndIf
    Return False
EndFunc

Func _InstallGeneric($sFilePath, $sSoftwareName, $bSilent = True)
    Local $sParams = ""

    ; Common silent installation parameters
    If $bSilent Then
        Switch $sSoftwareName
            Case "WinRAR"
                $sParams = "/S"
            Case "7-Zip"
                $sParams = "/S"
            Case "VLC"
                $sParams = "/L=1033 /S"
            Case ".NET Framework"
                $sParams = "/q /norestart"
            Case "Flash Player"
                $sParams = "-install"
            Case "Notepad++"
                $sParams = "/S"
            Case "Centbrowser"
                $sParams = "/S"
            Case "Opera"
                $sParams = "/S"
            Case "Brave"
                $sParams = "/S"
            Case Else
                $sParams = "/S" ; Default silent parameter
        EndSwitch
    EndIf

    Local $iResult = RunWait('"' & $sFilePath & '" ' & $sParams, "", @SW_HIDE, 300000) ; 5 minute timeout
    Return $iResult = 0
EndFunc
; ===============================================================================================================
; NETWORK DETECTION FUNCTIONS
; ===============================================================================================================

; Detect current network configuration
Func _DetectCurrentNetworkConfig()
    
    ; Run ipconfig command to get current network info
    Local $iPID = Run(@ComSpec & " /c ipconfig /all", "", @SW_HIDE, $STDOUT_CHILD)
    ProcessWaitClose($iPID)
    Local $sOutput = StdoutRead($iPID)
    
    If @error Or $sOutput = "" Then
        Return "192.168.1.100|255.255.255.0|192.168.1.1" ; Default fallback
    EndIf
    
    ; Parse the output to find the first active network adapter with IPv4
    Local $aLines = StringSplit($sOutput, @CRLF)
    Local $sCurrentIP = "", $sCurrentSubnet = "", $sCurrentGateway = ""
    Local $bFoundAdapter = False
    
    For $i = 1 To $aLines[0]
        Local $sLine = StringStripWS($aLines[$i], 3)
        
        ; Look for IPv4 Address
        If StringInStr($sLine, "IPv4 Address") And StringInStr($sLine, ":") Then
            Local $aIPParts = StringSplit($sLine, ":")
            If $aIPParts[0] >= 2 Then
                $sCurrentIP = StringStripWS($aIPParts[2], 3)
                ; Remove (Preferred) or other suffixes
                $sCurrentIP = StringRegExpReplace($sCurrentIP, "\s*\([^)]*\)", "")
                ; Skip loopback and APIPA addresses
                If Not StringInStr($sCurrentIP, "127.") And Not StringInStr($sCurrentIP, "169.254.") Then
                    $bFoundAdapter = True
                EndIf
            EndIf
        EndIf
        
        ; Look for Subnet Mask (only if we found a valid IP)
        If $bFoundAdapter And StringInStr($sLine, "Subnet Mask") And StringInStr($sLine, ":") Then
            Local $aSubnetParts = StringSplit($sLine, ":")
            If $aSubnetParts[0] >= 2 Then
                $sCurrentSubnet = StringStripWS($aSubnetParts[2], 3)
            EndIf
        EndIf
        
        ; Look for Default Gateway (only if we found a valid IP)
        If $bFoundAdapter And StringInStr($sLine, "Default Gateway") And StringInStr($sLine, ":") Then
            Local $aGatewayParts = StringSplit($sLine, ":")
            If $aGatewayParts[0] >= 2 Then
                $sCurrentGateway = StringStripWS($aGatewayParts[2], 3)
                ; Skip empty gateways
                If $sCurrentGateway <> "" Then
                    ; We have all info, break out
                    ExitLoop
                EndIf
            EndIf
        EndIf
    Next
    
    ; Build result string
    Local $sDetectedConfig = ""
    If $sCurrentIP <> "" And $sCurrentSubnet <> "" And $sCurrentGateway <> "" Then
        $sDetectedConfig = $sCurrentIP & "|" & $sCurrentSubnet & "|" & $sCurrentGateway
    Else
        $sDetectedConfig = "192.168.1.100|255.255.255.0|192.168.1.1" ; Fallback to default
    EndIf
    
    Return $sDetectedConfig
EndFunc

; ===============================================================================================================
; UTILITY FUNCTIONS
; ===============================================================================================================

; Detect Windows version
Func _GetWindowsVersion()
    Local $sVersion = @OSVersion
    Local $sBuild = @OSBuild
    
    ; Get version number from registry for more accurate detection
    Local $sVersionFromReg = RegRead("HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion", "CurrentVersion")
    Local $sProductName = RegRead("HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion", "ProductName")
    
    _WriteLog("Detected OS: " & $sVersion & " (Build: " & $sBuild & ", Version: " & $sVersionFromReg & ", Product: " & $sProductName & ")")
    
    ; Map to version numbers used in batch files
    Switch $sVersionFromReg
        Case "6.3"
            _WriteLog("Windows version mapped to: 6.3 (Windows 8.1/Server 2012 R2)")
            Return "6.3"
        Case "10.0"
            _WriteLog("Windows version mapped to: 10.0 (Windows 10/11/Server 2016/2019/2022)")
            Return "10.0"
        Case Else
            _WriteLog("Unknown Windows version, defaulting to: 10.0")
            Return "10.0" ; Default to latest
    EndSwitch
EndFunc

; Get Windows display name for GUI
Func _GetWindowsDisplayName($sVersionCode)
    Local $sProductName = RegRead("HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion", "ProductName")
    Local $sBuild = @OSBuild
    
    If $sProductName <> "" Then
        Return $sProductName & " (Build " & $sBuild & ")"
    Else
        Switch $sVersionCode
            Case "6.3"
                Return "Windows Server 2012 R2 (Build " & $sBuild & ")"
            Case "10.0"
                Return "Windows 10/11/Server 2016+ (Build " & $sBuild & ")"
            Case Else
                Return "Windows (Build " & $sBuild & ")"
        EndSwitch
    EndIf
EndFunc

; Get appropriate download URL based on Windows version
Func _GetDownloadURL($sSoftwareName)
    ; Find software in array
    Local $iIndex = -1
    For $i = 0 To UBound($g_aSoftwareURLs) - 1
        If $g_aSoftwareURLs[$i][0] = $sSoftwareName Then
            $iIndex = $i
            ExitLoop
        EndIf
    Next
    
    If $iIndex = -1 Then
        _WriteLog("ERROR: Software not found in database: " & $sSoftwareName)
        Return ""
    EndIf
    
    Local $sURL = ""
    Local $sFallbackURL = $g_aSoftwareURLs[$iIndex][4]
    
    ; Debug: Log all available URLs for this software
    _WriteLog("DEBUG: URL Configuration for " & $sSoftwareName & ":")
    _WriteLog("  Windows 6.3 URL: " & $g_aSoftwareURLs[$iIndex][1])
    _WriteLog("  Windows 10.0 URL: " & $g_aSoftwareURLs[$iIndex][2])
    _WriteLog("  Default URL: " & $g_aSoftwareURLs[$iIndex][3])
    _WriteLog("  Fallback URL: " & $sFallbackURL)
    _WriteLog("  Target Filename: " & $g_aSoftwareURLs[$iIndex][5])
    
    ; Select URL based on Windows version
    Switch $g_sWindowsVersion
        Case "6.3"
            $sURL = $g_aSoftwareURLs[$iIndex][1] ; Win6.3_URL
            _WriteLog("SELECTED: Windows 6.3 (2012 R2) URL for " & $sSoftwareName & ": " & $sURL)
        Case "10.0"
            $sURL = $g_aSoftwareURLs[$iIndex][2] ; Win10.0_URL
            _WriteLog("SELECTED: Windows 10.0+ URL for " & $sSoftwareName & ": " & $sURL)
        Case Else
            $sURL = $g_aSoftwareURLs[$iIndex][3] ; Default_URL
            _WriteLog("SELECTED: Default URL for " & $sSoftwareName & ": " & $sURL)
    EndSwitch
    
    ; If URL is empty, use default
    If $sURL = "" Then
        $sURL = $g_aSoftwareURLs[$iIndex][3]
        _WriteLog("WARNING: Empty URL detected, falling back to default URL: " & $sURL)
    EndIf
    
    ; Final URL verification
    _WriteLog("FINAL: Primary URL for " & $sSoftwareName & ": " & $sURL)
    _WriteLog("FINAL: Fallback URL for " & $sSoftwareName & ": " & $sFallbackURL)
    
    ; Return URL and fallback URL as array
    Local $aURLs[2] = [$sURL, $sFallbackURL]
    Return $aURLs
EndFunc

; Safe registry write with error handling
Func _SafeRegWrite($sKeyName, $sValueName, $sType, $vValue)
    Local $iResult = RegWrite($sKeyName, $sValueName, $sType, $vValue)
    If @error Then
        _WriteLog("Failed to write registry: " & $sKeyName & "\" & $sValueName & " (Error: " & @error & ")")
        Return False
    EndIf
    _WriteLog("Registry updated: " & $sKeyName & "\" & $sValueName & " = " & $vValue)
    Return True
EndFunc

; Enhanced checkbox checking
Func _IsChecked($iControlID)
    Return BitAND(GUICtrlRead($iControlID), $GUI_CHECKED) = $GUI_CHECKED
EndFunc

; Write to log file and display
Func _WriteLog($sMessage)
    Local $sTimestamp = @YEAR & "/" & @MON & "/" & @MDAY & " " & @HOUR & ":" & @MIN & ":" & @SEC
    Local $sLogEntry = $sTimestamp & " - " & $sMessage & @CRLF

    ; Write to file
    FileWrite($LOG_FILE, $sLogEntry)

    ; Update log display
    Local $sCurrentLog = GUICtrlRead($g_hLog)
    GUICtrlSetData($g_hLog, $sCurrentLog & $sLogEntry)

    ; Auto-scroll to bottom
    GUICtrlSendMsg($g_hLog, 0x00B6, 0, 0) ; EM_SCROLLCARET

    ; Limit log display to last 100 lines
    Local $aLines = StringSplit($sCurrentLog & $sLogEntry, @CRLF)
    If $aLines[0] > 100 Then
        Local $sNewLog = ""
        For $i = $aLines[0] - 99 To $aLines[0]
            $sNewLog &= $aLines[$i] & @CRLF
        Next
        GUICtrlSetData($g_hLog, $sNewLog)
    EndIf
EndFunc

; Update status bar
Func _UpdateStatus($sMessage)
    GUICtrlSetData($g_hStatus, $sMessage)
EndFunc

; Update progress bar
Func _UpdateProgress($iPercent)
    GUICtrlSetData($g_hProgress, $iPercent)
EndFunc

; Increment progress with message
Func _IncrementProgress($sMessage)
    $g_iCurrentStep += 1
    Local $iPercent = Round(($g_iCurrentStep / $g_iTotalSteps) * 100)
    _UpdateProgress($iPercent)
    _UpdateStatus($sMessage & " (" & $g_iCurrentStep & "/" & $g_iTotalSteps & ")")
EndFunc

; Count selected options
Func _CountSelectedOptions()
    Local $iCount = 0

    ; System configuration options
    If _IsChecked($UAC) Then $iCount += 1
    If _IsChecked($IEESC) Then $iCount += 1
    If _IsChecked($WINUPDATE) Then $iCount += 1
    If _IsChecked($TRAYICON) Then $iCount += 1
    If _IsChecked($SMALLICON) Then $iCount += 1
    If _IsChecked($FIREWALL) Then $iCount += 1
    If _IsChecked($WPASSCHANGE) Then $iCount += 1

    ; Software installation options
    If _IsChecked($CHROME) Then $iCount += 1
    If _IsChecked($FF) Then $iCount += 1
    If _IsChecked($EDGE) Then $iCount += 1
    If _IsChecked($OPERA) Then $iCount += 1
    If _IsChecked($BRAVE) Then $iCount += 1
    If _IsChecked($CENTBROWSER) Then $iCount += 1
    If _IsChecked($BIT) Then $iCount += 1
    If _IsChecked($PROXIFIER) Then $iCount += 1
    If _IsChecked($NOTEPADPP) Then $iCount += 1
    If _IsChecked($SEVENZIP) Then $iCount += 1
    If _IsChecked($WINRAR) Then $iCount += 1
    If _IsChecked($VLC) Then $iCount += 1

    ; Network and advanced options
    If _IsChecked($SETIP_DNS) Then $iCount += 1
    If _IsChecked($ACTIVE) Then $iCount += 1
    If _IsChecked($HDD) Then $iCount += 1
    If _IsChecked($BACKUP_REGISTRY) Then $iCount += 1
    If _IsChecked($UPDATE_DRIVERS) Then $iCount += 1

    ; Windows Edition Conversion
    If _IsChecked($CONVERT_2012) Then $iCount += 1
    If _IsChecked($CONVERT_2016) Then $iCount += 1
    If _IsChecked($CONVERT_2019) Then $iCount += 1
    If _IsChecked($CONVERT_2022) Then $iCount += 1

    Return $iCount
EndFunc
; Process network configuration
Func _ProcessNetworkConfiguration()
    If Not _IsChecked($SETIP_DNS) Then Return

    _UpdateStatus("Configuring network settings...")

    ; Get IP configuration
    Local $sIPConfig = GUICtrlRead($SETIP_DNS_IP)
    Local $aIPData = StringSplit($sIPConfig, "|")

    If @error Or $aIPData[0] < 3 Then
        _WriteLog("Invalid IP configuration format: " & $sIPConfig)
        MsgBox($MB_ICONERROR, "Error", "Invalid IP configuration format!" & @CRLF & "Expected: IP|Subnet|Gateway")
        Return
    EndIf

    ; Check for default IP configuration
    If $sIPConfig = "192.168.1.100|255.255.255.0|192.168.1.1" Then
        _WriteLog("Default IP configuration detected: " & $sIPConfig)
        Local $iResponse = MsgBox($MB_ICONWARNING + $MB_YESNO, "Cảnh báo - Default IP Configuration", _
            "Phát hiện bạn đang sử dụng thông tin IP mặc định của phần mềm!" & @CRLF & @CRLF & _
            "IP: 192.168.1.100" & @CRLF & _
            "Subnet: 255.255.255.0" & @CRLF & _
            "Gateway: 192.168.1.1" & @CRLF & @CRLF & _
            "Việc sử dụng IP mặc định có thể gây xung đột mạng hoặc không phù hợp với hệ thống của bạn." & @CRLF & @CRLF & _
            "Bạn có chắc chắn muốn tiếp tục với cấu hình IP này không?" & @CRLF & @CRLF & _
            "• Nhấn YES để tiếp tục với IP mặc định" & @CRLF & _
            "• Nhấn NO để hủy và thay đổi IP")

        If $iResponse = $IDNO Then
            _WriteLog("User cancelled network configuration due to default IP warning")
            MsgBox($MB_ICONINFORMATION, "Thông báo", "Cấu hình mạng đã bị hủy." & @CRLF & @CRLF & _
                "Vui lòng thay đổi thông tin IP trong tab 'Network & Advanced' trước khi chạy lại.")
            Return
        Else
            _WriteLog("User confirmed to proceed with default IP configuration")
        EndIf
    EndIf

    ; Get DNS configuration
    Local $sDNS1, $sDNS2
    If _IsChecked($DNS_CUSTOM) Then
        Local $sCustomDNS = GUICtrlRead($DNS_CUSTOM_INPUT)
        Local $aDNS = StringSplit($sCustomDNS, ",")
        $sDNS1 = StringStripWS($aDNS[1], 3)
        $sDNS2 = "8.8.4.4"
        If $aDNS[0] > 1 Then $sDNS2 = StringStripWS($aDNS[2], 3)
    Else
        Local $sDNSSelection = GUICtrlRead($SETIP_DNS_DNS_LIST)
        Switch $sDNSSelection
            Case "Google DNS (8.8.8.8)"
                $sDNS1 = "8.8.8.8"
                $sDNS2 = "8.8.4.4"
            Case "Cloudflare DNS (1.1.1.1)"
                $sDNS1 = "1.1.1.1"
                $sDNS2 = "1.0.0.1"
            Case "OpenDNS (208.67.222.222)"
                $sDNS1 = "208.67.222.222"
                $sDNS2 = "208.67.220.220"
            Case "Quad9 DNS (9.9.9.9)"
                $sDNS1 = "9.9.9.9"
                $sDNS2 = "149.112.112.112"
            Case Else
                $sDNS1 = "8.8.8.8"
                $sDNS2 = "8.8.4.4"
        EndSwitch
    EndIf

    ; Configure network
    If _SetIPAddress($aIPData[1], $aIPData[2], $aIPData[3], $sDNS1 & "," & $sDNS2) Then
        _WriteLog("Network configuration completed successfully")
        _IncrementProgress("Configure Network Settings")
    Else
        _WriteLog("Network configuration failed")
    EndIf
EndFunc

; Process advanced options
Func _ProcessAdvancedOptions()
    _UpdateStatus("Processing advanced options...")

    ; Windows Activation
    If _IsChecked($ACTIVE) Then
        _UpdateStatus("Activating Windows...")
        Local $iResult = RunWait(@ComSpec & " /c cscript " & @WindowsDir & "\system32\slmgr.vbs /ato", "", @SW_HIDE)
        If $iResult = 0 Then
            _WriteLog("Windows activation completed")
            _IncrementProgress("Activate Windows")
        Else
            _WriteLog("Windows activation failed (Exit code: " & $iResult & ")")
        EndIf
    EndIf

    ; Extend HDD
    If _IsChecked($HDD) Then
        _UpdateStatus("Extending system drive...")
        If _ExtendSystemDrive() Then
            _WriteLog("System drive extension completed")
            _IncrementProgress("Extend System Drive")
        Else
            _WriteLog("System drive extension failed")
        EndIf
    EndIf

    ; Create Registry Backup
    If _IsChecked($BACKUP_REGISTRY) Then
        _UpdateStatus("Creating registry backup...")
        If _CreateRegistryBackupSimple() Then
            _WriteLog("Registry backup created successfully")
            _IncrementProgress("Create Registry Backup")
        Else
            _WriteLog("Registry backup failed or was skipped")
        EndIf
    EndIf

    ; Windows Edition Conversion
    If _IsChecked($CONVERT_2012) Then
        _ConvertWindowsEdition("2012")
    EndIf
    If _IsChecked($CONVERT_2016) Then
        _ConvertWindowsEdition("2016")
    EndIf
    If _IsChecked($CONVERT_2019) Then
        _ConvertWindowsEdition("2019")
    EndIf
    If _IsChecked($CONVERT_2022) Then
        _ConvertWindowsEdition("2022")
    EndIf
EndFunc

; Convert Windows Edition from Evaluation to Standard
Func _ConvertWindowsEdition($sVersion)
    _UpdateStatus("Converting Windows " & $sVersion & " Edition...")
    _WriteLog("Starting Windows " & $sVersion & " edition conversion...")

    Local $sProductKey = ""
    Switch $sVersion
        Case "2012"
            $sProductKey = "D2N9P-3P6X9-2R39C-7RTCD-MDVJX"
        Case "2016"
            $sProductKey = "WC2BQ-8NRM3-FDDYY-2BFGV-KHKQY"
        Case "2019"
            $sProductKey = "N69G4-B89J2-4G8F4-WWYCC-J464C"
        Case "2022"
            $sProductKey = "VDYBN-27WPP-V4HQT-9VMD4-VMK7H"
        Case Else
            _WriteLog("Unknown Windows version: " & $sVersion)
            Return False
    EndSwitch

    ; First, get current edition
    _WriteLog("Getting current Windows edition...")
    Local $iResult = RunWait(@ComSpec & " /c DISM /online /Get-CurrentEdition", "", @SW_HIDE)
    If $iResult <> 0 Then
        _WriteLog("Failed to get current edition (Exit code: " & $iResult & ")")
    EndIf

    ; Convert to Standard edition
    _WriteLog("Converting to ServerStandard edition with product key...")
    $iResult = RunWait(@ComSpec & " /c DISM /online /Set-Edition:ServerStandard /ProductKey:" & $sProductKey & " /AcceptEula", "", @SW_HIDE)

    If $iResult = 0 Then
        _WriteLog("Windows " & $sVersion & " edition conversion completed successfully")
        _IncrementProgress("Convert Windows " & $sVersion & " Edition")
        MsgBox($MB_ICONINFORMATION, "Success", "Windows " & $sVersion & " edition conversion completed!" & @CRLF & @CRLF & "A system restart may be required to complete the conversion.")
        Return True
    Else
        _WriteLog("Windows " & $sVersion & " edition conversion failed (Exit code: " & $iResult & ")")
        MsgBox($MB_ICONERROR, "Error", "Windows " & $sVersion & " edition conversion failed!" & @CRLF & "Please check the logs for more details.")
        Return False
    EndIf
EndFunc

; Change Windows password with enhanced error handling
Func _ChangeWindowsPassword($sNewPassword)
    ; Method 1: Try WMI approach
    Local $strComputer = "."
    Local $objWMIService = ObjGet("winmgmts:\\" & $strComputer & "\root\cimv2")
    If IsObj($objWMIService) Then
        Local $colAccounts = $objWMIService.ExecQuery("SELECT * FROM Win32_UserAccount WHERE Name = '" & @UserName & "'")
        If IsObj($colAccounts) Then
            For $objAccount In $colAccounts
                Local $iResult = $objAccount.SetPassword($sNewPassword)
                If $iResult = 0 Then Return True
            Next
        EndIf
    EndIf

    ; Method 2: Try ADSI approach
    Local $objUser = ObjGet("WinNT://" & $strComputer & "/" & @UserName & ",user")
    If IsObj($objUser) Then
        $objUser.SetPassword($sNewPassword)
        $objUser.SetInfo()
        If Not @error Then Return True
    EndIf

    ; Method 3: Fallback to net user command
    _WriteLog("Failed to change password using WMI/ADSI, trying net user command...")
    Local $iResult = RunWait(@ComSpec & ' /c net user "' & @UserName & '" "' & $sNewPassword & '"', "", @SW_HIDE)
    Return $iResult = 0
EndFunc

; Extend system drive (simplified - no temp file needed)
Func _ExtendSystemDrive()
    ; Run diskpart commands directly via pipe
    Local $sCommand = 'echo select volume C && echo extend | diskpart'
    Local $iResult = RunWait(@ComSpec & " /c " & $sCommand, "", @SW_HIDE)

    Return $iResult = 0
EndFunc

; Backup functions removed for cleaner codebase

; Restart Windows Explorer
Func _RestartExplorer()
    _WriteLog("Restarting Windows Explorer...")
    ProcessClose("explorer.exe")
    Sleep(1000)
    Run("explorer.exe")
    _WriteLog("Windows Explorer restarted")
EndFunc

; Set processing mode for better visual feedback
Func _SetProcessingMode($bProcessing = True)
    Global $g_bProcessingMode, $g_iProcessingAnimationStep, $BUTTONRUN
    
    If $bProcessing Then
        ; Change button to processing state
        $g_bProcessingMode = True
        $g_iProcessingAnimationStep = 0
        
        ; Method 1: Try forcing colors without disable
        GUICtrlSetData($BUTTONRUN, "🔄 Processing...")
        GUICtrlSetBkColor($BUTTONRUN, 0xFF6600) ; Orange background
        
        ; Force white text with multiple attempts
        For $i = 1 To 3
            GUICtrlSetColor($BUTTONRUN, 0xFFFFFF)
            Sleep(10)
        Next
        
        GUICtrlSetFont($BUTTONRUN, 11, 600, 0, "Segoe UI")
        
        ; Force white again after font change
        For $i = 1 To 3
            GUICtrlSetColor($BUTTONRUN, 0xFFFFFF)
            Sleep(10)
        Next
        
        _WriteLog("GUI: Button set to processing mode")
        
        ; Start processing animation timer
        AdlibRegister("_UpdateProcessingAnimation", 800) ; Update every 800ms
    Else
        ; Stop processing mode
        $g_bProcessingMode = False
        AdlibUnRegister("_UpdateProcessingAnimation")
        
        ; Restore button to normal state
        GUICtrlSetData($BUTTONRUN, "🚀 Start Configuration")
        GUICtrlSetBkColor($BUTTONRUN, 0x0078D4) ; Blue background
        GUICtrlSetColor($BUTTONRUN, 0xFFFFFF) ; White text
        GUICtrlSetFont($BUTTONRUN, 11, 600, 0, "Segoe UI")
        GUICtrlSetColor($BUTTONRUN, 0xFFFFFF) ; Set again after font
        _WriteLog("GUI: Button restored to normal mode")
    EndIf
EndFunc

; Update processing animation
Func _UpdateProcessingAnimation()
    Global $g_bProcessingMode, $g_iProcessingAnimationStep
    
    If Not $g_bProcessingMode Then Return
    
    ; Cycle through different processing messages
    Local $aMessages[4] = ["🔄 Processing...", "🔄 Processing", "🔄 Processing.", "🔄 Processing.."]
    
    $g_iProcessingAnimationStep = Mod($g_iProcessingAnimationStep + 1, 4)
    GUICtrlSetData($BUTTONRUN, $aMessages[$g_iProcessingAnimationStep])
    ; Ensure white text color is maintained during animation - set multiple times
    GUICtrlSetColor($BUTTONRUN, 0xFFFFFF)
    GUICtrlSetFont($BUTTONRUN, 11, 600, 0, "Segoe UI")
    GUICtrlSetColor($BUTTONRUN, 0xFFFFFF) ; Set again after font to override system
EndFunc

; Set success mode briefly before restoring normal state
Func _SetSuccessMode()
    ; Show success state
    GUICtrlSetData($BUTTONRUN, "✅ Completed Successfully!")
    GUICtrlSetColor($BUTTONRUN, 0xFFFFFF) ; White text
    GUICtrlSetBkColor($BUTTONRUN, 0x00AA00) ; Green background for success
    _WriteLog("GUI: Button set to success mode")
    
    ; Wait 2 seconds then restore to normal
    Sleep(2000)
    
    ; Restore to normal state
    GUICtrlSetData($BUTTONRUN, "🚀 Start Configuration")
    GUICtrlSetColor($BUTTONRUN, 0xFFFFFF) ; White text  
    GUICtrlSetBkColor($BUTTONRUN, 0x0078D4) ; Blue background
    GUICtrlSetState($BUTTONRUN, $GUI_ENABLE) ; Re-enable clicking
    _WriteLog("GUI: Button restored to normal state after success")
EndFunc

; Legacy function for compatibility
Func _SetControlsState($iState)
    ; This function is kept for compatibility but now uses _SetProcessingMode
    If $iState = $GUI_DISABLE Then
        _SetProcessingMode(True)
    Else
        _SetProcessingMode(False)
    EndIf
EndFunc
; Enhanced IP address configuration
Func _SetIPAddress($sIP = "", $sSubnet = "", $sGateway = "", $sDNS = "")
    Local $iPID = Run(@ComSpec & " /c netsh.exe int show int", "", @SW_HIDE, $STDOUT_CHILD)
    ProcessWaitClose($iPID)
    Local $sOutput = StdoutRead($iPID)
    Local $aLANs = StringSplit(StringTrimRight(StringStripCR($sOutput), StringLen(@CRLF)), @CRLF)

    For $i = 1 To UBound($aLANs) - 1
        If StringInStr($aLANs[$i], "Dedicated") Then
            Local $iPos = StringInStr($aLANs[$i], "  ", 0, -1)
            Local $sConn = StringTrimLeft($aLANs[$i], $iPos + 1)

            $iPID = Run(@ComSpec & ' /c wmic.exe nic where(NetConnectionID="' & $sConn & '") get PNPDeviceID', "", @SW_HIDE, $STDOUT_CHILD)
            ProcessWaitClose($iPID)
            $sOutput = StdoutRead($iPID)
            Local $aDevice = StringSplit(StringTrimRight(StringStripCR($sOutput), StringLen(@CRLF)), @CRLF)

            If UBound($aDevice) > 1 And StringInStr($aDevice[2], "PCI\") Then
                _WriteLog("Configuring connection '" & $sConn & "' on device " & $aDevice[2])

                If StringInStr($sIP, "dhcp") Or $sIP = "" Then
                    RunWait(@ComSpec & ' /c netsh.exe int ip set address "' & $sConn & '" dhcp', "", @SW_HIDE)
                    RunWait(@ComSpec & ' /c netsh.exe int ip set dns "' & $sConn & '" dhcp', "", @SW_HIDE)
                    _WriteLog("Set DHCP IP & DNS for " & $sConn)
                Else
                    ; Set static IP
                    Local $iResult = RunWait(@ComSpec & ' /c netsh.exe int ip set address "' & $sConn & '" static ' & $sIP & " " & $sSubnet & " " & $sGateway & " 1", "", @SW_HIDE)
                    If $iResult = 0 Then
                        _WriteLog("Set static IP: " & $sIP & "/" & $sSubnet & " Gateway: " & $sGateway)

                        ; Set DNS servers
                        Local $aDNS = StringSplit($sDNS, ",")
                        If UBound($aDNS) > 1 And $aDNS[1] <> "" Then
                            $iResult = RunWait(@ComSpec & ' /c netsh.exe int ip set dns name="' & $sConn & '" static ' & StringStripWS($aDNS[1], 3) & " validate=no", "", @SW_HIDE)
                            If $iResult = 0 Then
                                _WriteLog("Set primary DNS: " & StringStripWS($aDNS[1], 3))

                                If UBound($aDNS) > 2 And StringStripWS($aDNS[2], 3) <> "" Then
                                    $iResult = RunWait(@ComSpec & ' /c netsh.exe int ip add dns name="' & $sConn & '" ' & StringStripWS($aDNS[2], 3) & " index=2 validate=no", "", @SW_HIDE)
                                    If $iResult = 0 Then
                                        _WriteLog("Set secondary DNS: " & StringStripWS($aDNS[2], 3))
                                    EndIf
                                EndIf
                            EndIf
                        EndIf
                        Return True
                    Else
                        _WriteLog("Failed to set static IP (Exit code: " & $iResult & ")")
                    EndIf
                EndIf
            EndIf
        EndIf
    Next
    Return False
EndFunc



; Preview changes function
Func _PreviewChanges()
    Local $sPreview = "Configuration Preview:" & @CRLF & _StringRepeat("=", 30) & @CRLF & @CRLF

    $sPreview &= "SYSTEM CONFIGURATION:" & @CRLF
    If _IsChecked($UAC) Then $sPreview &= "• Disable UAC" & @CRLF
    If _IsChecked($IEESC) Then $sPreview &= "• Turn Off IE Enhanced Security" & @CRLF
    If _IsChecked($WINUPDATE) Then $sPreview &= "• Disable Windows Update" & @CRLF
    If _IsChecked($FIREWALL) Then $sPreview &= "• Turn Off Windows Firewall" & @CRLF
    If _IsChecked($WPASSCHANGE) Then $sPreview &= "• Change Windows Password" & @CRLF

    $sPreview &= @CRLF & "SOFTWARE INSTALLATION:" & @CRLF
    If _IsChecked($CHROME) Then $sPreview &= "• Google Chrome" & @CRLF
    If _IsChecked($FF) Then $sPreview &= "• Mozilla Firefox" & @CRLF
    If _IsChecked($BIT) Then $sPreview &= "• Bitvise SSH Client" & @CRLF
    If _IsChecked($WINRAR) Then $sPreview &= "• WinRAR" & @CRLF

    $sPreview &= @CRLF & "NETWORK & ADVANCED:" & @CRLF
    If _IsChecked($SETIP_DNS) Then $sPreview &= "• Configure Static IP & DNS" & @CRLF
    If _IsChecked($ACTIVE) Then $sPreview &= "• Activate Windows" & @CRLF
    If _IsChecked($HDD) Then $sPreview &= "• Extend System Drive" & @CRLF

    MsgBox($MB_ICONINFORMATION, "Configuration Preview", $sPreview)
EndFunc

; Background RDP refresh (only refreshes if tab is active and data already loaded)
Func _BackgroundRDPRefresh()
    ; Only refresh if RDP history tab is active and already loaded
    If GUICtrlRead($g_hTabMain) = 3 And $g_bRDPHistoryLoaded Then
        ; Only refresh if cache is older than 10 minutes
        Local $iCurrentTime = @HOUR * 3600 + @MIN * 60 + @SEC
        If ($iCurrentTime - $g_iLastRDPCacheTime) > 600 Then
            _WriteLog("BACKGROUND REFRESH: Updating RDP history (cache expired)")
            Local $sLoginHistory = _GetLoginHistory()
            GUICtrlSetData($g_hLog, $sLoginHistory)
        EndIf
    EndIf
EndFunc

; Application exit function
Func _ExitApp()
    _WriteLog("FastConfigVPS v" & $APP_VERSION & " exiting...")
    AdlibUnRegister("_CheckPasswordChange") ; Clean up password validation timer
    AdlibUnRegister("_UpdateProcessingAnimation") ; Clean up processing animation timer
    AdlibUnRegister("_BackgroundRDPRefresh") ; Clean up background refresh timer
    Exit
EndFunc

; Help function
Func _ShowHelp()
    Local $sHelp = "FastConfigVPS v" & $APP_VERSION & " - Help" & @CRLF & _StringRepeat("=", 40) & @CRLF & @CRLF
    $sHelp &= "HOTKEYS:" & @CRLF
    $sHelp &= "ESC - Exit application" & @CRLF
    $sHelp &= "F1 - Show this help" & @CRLF
    $sHelp &= "F5 - Refresh status" & @CRLF & @CRLF
    $sHelp &= "FEATURES:" & @CRLF
    $sHelp &= "• Enhanced GUI with progress tracking" & @CRLF
    $sHelp &= "• Comprehensive logging system" & @CRLF
    $sHelp &= "• Configuration save/load" & @CRLF
    $sHelp &= "• Automatic system backup" & @CRLF
    $sHelp &= "• Updated software URLs" & @CRLF
    $sHelp &= "• Improved error handling" & @CRLF

    MsgBox($MB_ICONINFORMATION, "Help", $sHelp)
EndFunc

; Refresh status function
Func _RefreshStatus()
    _UpdateStatus("Status refreshed at " & @HOUR & ":" & @MIN & ":" & @SEC)
    _RefreshLogDisplay()
EndFunc

; Refresh log display
Func _RefreshLogDisplay()
    If FileExists($LOG_FILE) Then
        Local $sLogContent = FileRead($LOG_FILE)
        GUICtrlSetData($g_hLog, $sLogContent)
    EndIf
EndFunc

; Save log to file
Func _SaveLogToFile()
    Local $sLogFile = FileSaveDialog("Save Log File", @DesktopDir, "Text Files (*.txt)|Log Files (*.log)", 0, "FastConfig_Log_" & @YEAR & @MON & @MDAY & ".txt")
    If $sLogFile <> "" Then
        FileCopy($LOG_FILE, $sLogFile, 1)
        MsgBox($MB_ICONINFORMATION, "Success", "Log saved to: " & $sLogFile)
    EndIf
EndFunc

; Lazy load RDP history when tab is first accessed
Func _LoadRDPHistoryLazy()
    If $g_bRDPHistoryLoaded Then Return ; Already loaded
    
    _UpdateStatus("Loading RDP login history...")
    _WriteLog("LAZY LOAD: Loading RDP history for first time")
    
    ; Show loading message
    GUICtrlSetData($g_hLog, "Loading RDP Login History..." & @CRLF & "Please wait...")
    
    ; Load the history (uses cache if available)
    Local $sLoginHistory = _GetLoginHistory()
    GUICtrlSetData($g_hLog, $sLoginHistory)
    
    ; Mark as loaded so we don't load again
    $g_bRDPHistoryLoaded = True
    _WriteLog("LAZY LOAD: RDP history loaded successfully")
    _UpdateStatus("RDP login history loaded")
EndFunc

; Refresh login history display with cache clearing
Func _RefreshLoginHistory()
    _UpdateStatus("Refreshing login history...")
    
    ; Clear cache to force fresh data
    $g_sLastRDPCache = ""
    $g_iLastRDPCacheTime = 0
    _WriteLog("LOGIN HISTORY: Cache cleared, forcing fresh data retrieval")
    
    Local $sLoginHistory = _GetLoginHistory()
    GUICtrlSetData($g_hLog, $sLoginHistory)
    $g_bRDPHistoryLoaded = True ; Mark as loaded
    _WriteLog("Login history refreshed")
    _UpdateStatus("Login history updated")
EndFunc

; Enhanced RDP login history retrieval with improved PowerShell logic and caching
Func _GetLoginHistory()
    ; Check cache first (cache valid for 5 minutes)
    Local $iCurrentTime = @HOUR * 3600 + @MIN * 60 + @SEC
    If $g_sLastRDPCache <> "" And (($iCurrentTime - $g_iLastRDPCacheTime) < 300) Then
        _WriteLog("LOGIN HISTORY: Using cached data (" & ($iCurrentTime - $g_iLastRDPCacheTime) & "s old)")
        Return $g_sLastRDPCache
    EndIf
    
    _WriteLog("Getting RDP login history for the last " & $DEFAULT_RDP_DAYS & " days...")
    Local $sHistory = "Windows VPS RDP Login History (Last " & $DEFAULT_RDP_DAYS & " days)" & @CRLF
    $sHistory &= _StringRepeat("=", 60) & @CRLF & @CRLF

    ; Create enhanced PowerShell script based on new logic
    Local $sPSScript = @TempDir & "\GetRDPLoginsEnhanced.ps1"
    Local $sPSContent = _CreateEnhancedRDPScript($DEFAULT_RDP_DAYS)
    
    FileWrite($sPSScript, $sPSContent)
    _WriteLog("LOGIN HISTORY: Created enhanced PowerShell script: " & $sPSScript)
    
    ; Execute PowerShell script with proper error handling
    Local $sCommand = 'powershell.exe -NoProfile -ExecutionPolicy Bypass -File "' & $sPSScript & '" -Days ' & $DEFAULT_RDP_DAYS
    _WriteLog("LOGIN HISTORY: Executing command: " & $sCommand)
    
    Local $iPID = Run($sCommand, "", @SW_HIDE, $STDOUT_CHILD + $STDERR_CHILD)
    Local $sOutput = "", $sError = ""
    
    ; Read output with timeout
    Local $iTimeout = 30000 ; 30 seconds
    Local $iTimer = TimerInit()
    
    While ProcessExists($iPID) And TimerDiff($iTimer) < $iTimeout
        $sOutput &= StdoutRead($iPID)
        $sError &= StderrRead($iPID)
        Sleep(100)
    WEnd
    
    ; Final read
    $sOutput &= StdoutRead($iPID)
    $sError &= StderrRead($iPID)
    
    ProcessClose($iPID)
    FileDelete($sPSScript)
    
    _WriteLog("LOGIN HISTORY: PowerShell output length: " & StringLen($sOutput))
    If StringLen($sError) > 0 Then _WriteLog("LOGIN HISTORY: PowerShell errors: " & $sError)
    
    ; Parse and format output
    Local $iValidEntries = _ParseRDPOutput($sOutput, $sHistory)
    
    ; Add final summary
    If $iValidEntries > 0 Then
        $sHistory &= @CRLF & "✅ Summary: Found " & $iValidEntries & " RDP login sessions in the last " & $DEFAULT_RDP_DAYS & " days." & @CRLF
        $sHistory &= "📂 Data saved to: " & $RDP_LOG_FILE & @CRLF
        _WriteLog("LOGIN HISTORY: Successfully found " & $iValidEntries & " RDP login entries")
    Else
        ; Handle no results found
        $sHistory &= @CRLF & "⚠️  No RDP login events found in the last " & $DEFAULT_RDP_DAYS & " days." & @CRLF & @CRLF
        $sHistory &= "Possible reasons:" & @CRLF
        $sHistory &= "• No remote RDP connections occurred" & @CRLF
        $sHistory &= "• Security audit policy not enabled" & @CRLF
        $sHistory &= "• Insufficient permissions to read Event Log" & @CRLF
        $sHistory &= "• Need Administrator privileges" & @CRLF & @CRLF
        $sHistory &= "🔧 To enable audit policy:" & @CRLF
        $sHistory &= "AuditPol.exe /set /subcategory:'Logon' /success:enable" & @CRLF
        _WriteLog("LOGIN HISTORY: No RDP login entries found")
    EndIf
    
    ; Cache the result for better performance
    $g_sLastRDPCache = $sHistory
    $g_iLastRDPCacheTime = $iCurrentTime
    _WriteLog("LOGIN HISTORY: Result cached for future requests")
    
    Return $sHistory
EndFunc

; Create simplified PowerShell script for RDP detection
Func _CreateEnhancedRDPScript($iDays)
    ; Use a simplified approach to avoid encoding issues
    Local $sPSContent = '#' & @CRLF & _
        '# RDP Login Detection Script - Compatible with PowerShell 5.1+' & @CRLF & _
        '#' & @CRLF & _
        'param([int]$Days = ' & $iDays & ')' & @CRLF & @CRLF & _
        'Write-Host "Getting RDP login history for the last $Days days..." -ForegroundColor Cyan' & @CRLF & @CRLF & _
        '# Check admin privileges' & @CRLF & _
        '$id = [System.Security.Principal.WindowsIdentity]::GetCurrent()' & @CRLF & _
        '$principal = New-Object System.Security.Principal.WindowsPrincipal($id)' & @CRLF & _
        'if (-not $principal.IsInRole([System.Security.Principal.WindowsBuiltInRole]::Administrator)) {' & @CRLF & _
        '    Write-Host "WARNING: Please run PowerShell with Administrator privileges." -ForegroundColor Yellow' & @CRLF & _
        '    Write-Host "ADMIN_CHECK_FAILED"' & @CRLF & _
        '    exit 1' & @CRLF & _
        '}' & @CRLF & @CRLF & _
        '# Check audit policy' & @CRLF & _
        'try {' & @CRLF & _
        '    $audit = (auditpol /get /subcategory:"Logon" 2>$null)' & @CRLF & _
        '    if ($audit -and ($audit -notmatch "Success\\s*:\\s*Enabled")) {' & @CRLF & _
        '        Write-Host "WARNING: Audit Logon Success is not enabled. Results may be empty." -ForegroundColor Yellow' & @CRLF & _
        '        Write-Host "Enable with: AuditPol.exe /set /subcategory:Logon /success:enable"' & @CRLF & _
        '    }' & @CRLF & _
        '} catch { }' & @CRLF & @CRLF & _
        '# Filter RDP events (LogonType=10, Event ID 4624)' & @CRLF & _
        '$startTime = (Get-Date).AddDays(-1 * $Days)' & @CRLF & _
        'try {' & @CRLF & _
        '    Write-Host "Scanning Security Event Log from $($startTime.ToString(' & "'yyyy-MM-dd HH:mm:ss'" & '))..." -ForegroundColor Gray' & @CRLF & _
        '    $events = Get-WinEvent -FilterHashtable @{LogName=' & "'Security'" & '; Id=4624; StartTime=$startTime} -ErrorAction Stop' & @CRLF & _
        '    Write-Host "Found $($events.Count) total event ID 4624 entries." -ForegroundColor Gray' & @CRLF & _
        '} catch {' & @CRLF & _
        '    Write-Host "ERROR: Cannot read Security log. Need admin privileges." -ForegroundColor Red' & @CRLF & _
        '    Write-Host "SECURITY_LOG_ACCESS_DENIED"' & @CRLF & _
        '    exit 1' & @CRLF & _
        '}' & @CRLF & @CRLF & _
        '# Process events and extract RDP logins' & @CRLF & _
        '$results = @()' & @CRLF & _
        '$rdpCount = 0' & @CRLF & _
        'foreach ($event in $events) {' & @CRLF & _
        '    $xml = [xml]$event.ToXml()' & @CRLF & _
        '    $data = @{}' & @CRLF & _
        '    foreach ($d in $xml.Event.EventData.Data) {' & @CRLF & _
        '        $data[$d.Name] = $d.' & "'#text'" & @CRLF & _
        '    }' & @CRLF & @CRLF & _
        '    if ($data.LogonType -eq "10") {' & @CRLF & _
        '        $rdpCount++' & @CRLF & _
        '        $obj = New-Object PSObject' & @CRLF & _
        '        $obj | Add-Member -NotePropertyName "TimeLocal" -NotePropertyValue $event.TimeCreated' & @CRLF & _
        '        $obj | Add-Member -NotePropertyName "Account" -NotePropertyValue ($data.TargetUserName)' & @CRLF & _
        '        $obj | Add-Member -NotePropertyName "Domain" -NotePropertyValue ($data.TargetDomainName)' & @CRLF & _
        '        $obj | Add-Member -NotePropertyName "IpAddress" -NotePropertyValue ($data.IpAddress)' & @CRLF & _
        '        $obj | Add-Member -NotePropertyName "Workstation" -NotePropertyValue ($data.WorkstationName)' & @CRLF & _
        '        $results += $obj' & @CRLF & _
        '    }' & @CRLF & _
        '}' & @CRLF & @CRLF & _
        'Write-Host "Filtered $rdpCount RDP events (LogonType=10) from $($events.Count) total events." -ForegroundColor Gray' & @CRLF & @CRLF & _
        'if ($results.Count -eq 0) {' & @CRLF & _
        '    Write-Host "NO_RDP_EVENTS_FOUND"' & @CRLF & _
        '    exit 0' & @CRLF & _
        '}' & @CRLF & @CRLF & _
        '# Display clean results for AutoIt parsing' & @CRLF & _
        '$results | Sort-Object TimeLocal -Descending | Select-Object -First 20 | ForEach-Object {' & @CRLF & _
        '    Write-Host "$($_.TimeLocal.ToString("MM/dd/yyyy HH:mm:ss")) $($_.Account) $($_.IpAddress) $($_.Workstation)"' & @CRLF & _
        '}' & @CRLF & @CRLF & _
        '# Save to JSON file' & @CRLF & _
        '$path = "C:\\ProgramData\\rdp_logons.json"' & @CRLF & _
        'try {' & @CRLF & _
        '    $parentDir = Split-Path -Parent $path' & @CRLF & _
        '    if (-not (Test-Path $parentDir)) {' & @CRLF & _
        '        New-Item -ItemType Directory -Path $parentDir -Force | Out-Null' & @CRLF & _
        '    }' & @CRLF & _
        '    $results | ConvertTo-Json -Depth 4 | Out-File -Encoding UTF8 $path' & @CRLF & _
        '} catch {' & @CRLF & _
        '    Write-Host "WARNING: Cannot save JSON file: $($_.Exception.Message)" -ForegroundColor Yellow' & @CRLF & _
        '}' & @CRLF & _
        'Write-Host "RDP_EVENTS_FOUND:$($results.Count)"'
    
    Return $sPSContent
EndFunc

; Enhanced RDP output parsing with clean formatting
Func _ParseRDPOutput($sOutput, ByRef $sHistory)
    Local $aLines = StringSplit($sOutput, @CRLF)
    Local $iValidEntries = 0
    Local $bInTable = False
    Local $bFoundResults = False
    
    ; Add key information first
    For $i = 1 To UBound($aLines) - 1
        Local $sLine = StringStripWS($aLines[$i], 3)
        
        ; Skip empty lines
        If $sLine = "" Then ContinueLoop
        
        ; Check for critical errors first
        If StringInStr($sLine, "ADMIN_CHECK_FAILED") Then
            $sHistory &= "❌ ERROR: Need Administrator privileges to access Security Event Log!" & @CRLF
            $sHistory &= "Please right-click FastConfig → 'Run as Administrator'" & @CRLF
            _WriteLog("LOGIN HISTORY: Admin check failed")
            Return 0
        EndIf
        
        If StringInStr($sLine, "SECURITY_LOG_ACCESS_DENIED") Then
            $sHistory &= "❌ ERROR: Cannot access Security Event Log!" & @CRLF
            $sHistory &= "Please run FastConfig as Administrator." & @CRLF
            _WriteLog("LOGIN HISTORY: Security log access denied")
            Return 0
        EndIf
        
        ; Look for event count and filtering info
        If StringInStr($sLine, "Filtered") And StringInStr($sLine, "RDP events") Then
            $sHistory &= "🔍 " & $sLine & @CRLF
            _WriteLog("LOGIN HISTORY: " & $sLine)
        EndIf
        
        If StringInStr($sLine, "WARNING:") And StringInStr($sLine, "Audit") Then
            $sHistory &= "⚠️  " & $sLine & @CRLF
            $sHistory &= "💡 Enable with: AuditPol.exe /set /subcategory:'Logon' /success:enable" & @CRLF & @CRLF
        EndIf
        
        ; Skip "Results saved to" messages to avoid duplication
        If StringInStr($sLine, "Results saved to:") Then ContinueLoop
        
        ; Extract final count
        If StringInStr($sLine, "RDP_EVENTS_FOUND:") Then
            Local $aCount = StringSplit($sLine, ":")
            If $aCount[0] >= 2 Then $iValidEntries = Number($aCount[2])
            _WriteLog("LOGIN HISTORY: Found " & $iValidEntries & " RDP events")
            $bFoundResults = True
            ContinueLoop
        EndIf
    Next
    
    ; Now parse the actual RDP login data from PowerShell table output
    If $bFoundResults And $iValidEntries > 0 Then
        $sHistory &= "📋 Recent RDP Login Sessions:" & @CRLF
        $sHistory &= _StringRepeat("=", 85) & @CRLF
        $sHistory &= "Date/Time            Account          IP Address        Workstation" & @CRLF
        $sHistory &= _StringRepeat("-", 85) & @CRLF
        
        ; Parse table data more carefully
        For $i = 1 To UBound($aLines) - 1
            Local $sLine = StringStripWS($aLines[$i], 3)
            
            ; Look for actual data lines (date pattern)
            If StringRegExp($sLine, "^\d{1,2}/\d{1,2}/\d{4}\s+\d{1,2}:\d{2}:\d{2}") Then
                ; This looks like a data line, parse it more carefully
                Local $aFields = StringRegExp($sLine, "\S+", 3) ; Split by whitespace
                If IsArray($aFields) And UBound($aFields) >= 4 Then
                    Local $sDate = $aFields[0]
                    Local $sTime = $aFields[1] & " " & $aFields[2] ; Include AM/PM
                    Local $sDateTime = StringLeft($sDate & " " & $sTime & _StringRepeat(" ", 21), 21)
                    
                    Local $sAccount = "Unknown"
                    Local $sIP = "Unknown"
                    Local $sWorkstation = ""
                    
                    ; Try to identify Account and IP from remaining fields
                    For $j = 3 To UBound($aFields) - 1
                        Local $sField = $aFields[$j]
                        ; If it looks like an IP address
                        If StringRegExp($sField, "^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$") Then
                            $sIP = $sField
                        ElseIf $sAccount = "Unknown" And $sField <> "" And Not StringIsDigit($sField) Then
                            $sAccount = $sField
                        ElseIf $sWorkstation = "" And $sField <> $sAccount And $sField <> $sIP Then
                            $sWorkstation = $sField
                        EndIf
                    Next
                    
                    $sHistory &= $sDateTime & StringLeft($sAccount & _StringRepeat(" ", 17), 17) & StringLeft($sIP & _StringRepeat(" ", 18), 18) & $sWorkstation & @CRLF
                EndIf
            EndIf
        Next
        
        $sHistory &= _StringRepeat("=", 85) & @CRLF
    EndIf
    
    Return $iValidEntries
EndFunc

; Simple registry backup function
Func _CreateRegistryBackupSimple()
    Local $sBackupFile = $BACKUP_DIR & "\Registry_" & @YEAR & @MON & @MDAY & "_" & @HOUR & @MIN & ".reg"
    Local $sCommand = 'regedit /e "' & $sBackupFile & '" "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion"'
    Local $iResult = RunWait($sCommand, "", @SW_HIDE)
    
    If $iResult = 0 And FileExists($sBackupFile) Then
        _WriteLog("Registry backup created: " & $sBackupFile)
        Return True
    Else
        _WriteLog("Registry backup failed or user cancelled")
        Return False
    EndIf
EndFunc

; Save login history to file
Func _SaveLoginHistoryToFile()
    Local $sHistoryFile = FileSaveDialog("Export Login History", @DesktopDir, "Text Files (*.txt)", 0, "Login_History_" & @YEAR & @MON & @MDAY & ".txt")
    If $sHistoryFile <> "" Then
        Local $sHistory = GUICtrlRead($g_hLog)
        FileWrite($sHistoryFile, $sHistory)
        MsgBox($MB_ICONINFORMATION, "Success", "Login history exported to: " & $sHistoryFile)
    EndIf
EndFunc