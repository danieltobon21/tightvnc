$ErrorActionPreference = 'Continue'

$src      = 'C:\working-files\tightvnc\Release\x64\TobonVNCViewer.exe'
$install  = 'C:\Program Files\TightVNC'
$backup   = 'C:\working-files\_backups\tightvnc-viewer-original'
$report   = New-Object System.Collections.Generic.List[string]
function Say($t) { $script:report.Add($t); Write-Output $t }

Say "=== TobonVNC Viewer deployment ==="
if (-not (Test-Path $src)) { Say "ERROR: $src not found"; $report | Out-File -Encoding ascii C:\temp\deploy.txt; exit 1 }

New-Item -ItemType Directory -Force -Path $backup | Out-Null

# 1. running instances
Get-Process tvnviewer, TobonVNCViewer -ErrorAction SilentlyContinue | ForEach-Object {
  Say "stopping $($_.ProcessName) (pid $($_.Id))"
  Stop-Process -Id $_.Id -Force
}
Start-Sleep -Milliseconds 700

# 2. backup the original binary and the file association
if (Test-Path "$install\tvnviewer.exe") {
  Copy-Item "$install\tvnviewer.exe" "$backup\tvnviewer.exe" -Force
  $orig = Get-Item "$backup\tvnviewer.exe"
  Say ("backup: {0} ({1} bytes, version {2})" -f $orig.FullName, $orig.Length,
       $orig.VersionInfo.FileVersion)
} else {
  Say "backup: no original tvnviewer.exe present"
}
& reg.exe export "HKCR\VncViewer.Config" "$backup\HKCR_VncViewer.Config.reg" /y *> $null
if (Test-Path "$backup\HKCR_VncViewer.Config.reg") { Say "backup: file association exported" }

# 3. install the new binary
Copy-Item $src "$install\TobonVNCViewer.exe" -Force
$new = Get-Item "$install\TobonVNCViewer.exe"
Say ("installed: {0} ({1} bytes, version {2}, sha256 {3})" -f $new.FullName, $new.Length,
     $new.VersionInfo.FileVersion, (Get-FileHash $new.FullName -Algorithm SHA256).Hash.Substring(0, 16))
Say ("source sha256 matches: " + ((Get-FileHash $src -Algorithm SHA256).Hash -eq (Get-FileHash $new.FullName -Algorithm SHA256).Hash))

# 4. Start menu shortcut
$menuDir = 'C:\ProgramData\Microsoft\Windows\Start Menu\Programs\TobonVNC'
New-Item -ItemType Directory -Force -Path $menuDir | Out-Null
$ws = New-Object -ComObject WScript.Shell
$lnkPath = Join-Path $menuDir 'TobonVNC Viewer.lnk'
$lnk = $ws.CreateShortcut($lnkPath)
$lnk.TargetPath = "$install\TobonVNCViewer.exe"
$lnk.WorkingDirectory = $install
$lnk.IconLocation = "$install\TobonVNCViewer.exe,0"
$lnk.Description = 'TobonVNC Viewer - TightVNC Viewer fork: sessions start in view-only mode'
$lnk.Save()
Say "start menu: $lnkPath -> $((New-Object -ComObject WScript.Shell).CreateShortcut($lnkPath).TargetPath)"

# 5. .vnc file association: the viewer ONLY reads a config file through
#    -optionsfile=<path>. With a bare "%1" it parses the path as a connection
#    string and fails with "Connection parameters (host, port, socket, gates)
#    is empty", so the switch is mandatory.
$exePath = "$install\TobonVNCViewer.exe"
$command = '"' + $exePath + '" -optionsfile="%1"'
$icon    = '"' + $exePath + '",0'
foreach ($root in @('HKCU:\Software\Classes', 'HKLM:\Software\Classes')) {
  foreach ($sub in @('VncViewer.Config\shell\open\command', 'VncViewer.Config\DefaultIcon', '.vnc')) {
    New-Item -Force -Path (Join-Path $root $sub) -ErrorAction SilentlyContinue | Out-Null
  }
  Set-ItemProperty -Path (Join-Path $root 'VncViewer.Config\shell\open\command') -Name '(Default)' -Value $command
  Set-ItemProperty -Path (Join-Path $root 'VncViewer.Config\DefaultIcon') -Name '(Default)' -Value $icon
  Set-ItemProperty -Path (Join-Path $root '.vnc') -Name '(Default)' -Value 'VncViewer.Config'
  Say ("association $root : open = " + (Get-ItemProperty (Join-Path $root 'VncViewer.Config\shell\open\command')).'(default)')
}

# 6. remove the old TightVNC start menu entries (backed up first)
$oldMenu = 'C:\ProgramData\Microsoft\Windows\Start Menu\Programs\TightVNC'
if (Test-Path $oldMenu) {
  Copy-Item $oldMenu "$backup\StartMenu-TightVNC" -Recurse -Force
  Say "backup: start menu folder copied"
}

$report | Out-File -Encoding ascii C:\temp\deploy.txt
