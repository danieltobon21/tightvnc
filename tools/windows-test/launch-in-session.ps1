# Launches the installed viewer in the interactive session, using the
# ScheduledTasks cmdlets (they quote the executable path correctly).
$exe = 'C:\Program Files\TightVNC\TobonVNCViewer.exe'
$taskName = 'TobonVNCViewerInstalled'

Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue

$action = New-ScheduledTaskAction -Execute $exe -Argument '127.0.0.1::5901 -showcontrols=yes'
$principal = New-ScheduledTaskPrincipal -UserId "$env:COMPUTERNAME\$env:USERNAME" -LogonType Interactive
Register-ScheduledTask -TaskName $taskName -Action $action -Principal $principal -Force | Out-Null

$info = Get-ScheduledTask -TaskName $taskName | Select-Object -ExpandProperty Actions
"task action: $($info.Execute) $($info.Arguments)"

Start-ScheduledTask -TaskName $taskName
Start-Sleep -Seconds 7
Get-Process TobonVNCViewer -ErrorAction SilentlyContinue |
  Select-Object Id, Path, SessionId | Format-List | Out-String
