# Removes every artefact this work created on DANIEL-WORK: the test RFB server,
# the scheduled tasks used to drive the tests, and the test files in C:\temp.
$out = New-Object System.Collections.Generic.List[string]
function Say($t) { $script:out.Add($t); Write-Output $t }

Say '=== stopping test processes ==='
Get-Process python, TobonVNCViewer -ErrorAction SilentlyContinue | ForEach-Object {
  Say "  stopping $($_.ProcessName) pid=$($_.Id)"
  Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
}

Say '=== removing scheduled tasks ==='
Get-ScheduledTask -TaskName 'TobonVNC*' -ErrorAction SilentlyContinue | ForEach-Object {
  Say "  removing task $($_.TaskName)"
  Unregister-ScheduledTask -TaskName $_.TaskName -Confirm:$false
}

Say '=== removing test files ==='
$keep = @()
Get-ChildItem 'C:\temp' -File -ErrorAction SilentlyContinue |
  Where-Object { $_.Name -match '^(tvn|tobonvnc|test\d|probe|hover|click|geo|acc|inspect|toolbar|windows|smoke|deploy|diag|assoc|uninstall|shot|rfb)' } |
  ForEach-Object {
    Say "  deleting $($_.Name)"
    Remove-Item $_.FullName -Force -ErrorAction SilentlyContinue
  }

Say '=== remaining C:\temp content ==='
Get-ChildItem 'C:\temp' -ErrorAction SilentlyContinue | Select-Object Name | Format-Table -AutoSize | Out-String | ForEach-Object { Say $_ }

Say '=== installed viewer check ==='
Say ('  TobonVNCViewer.exe present: ' + (Test-Path 'C:\Program Files\TightVNC\TobonVNCViewer.exe'))
Say ('  old tvnviewer.exe present : ' + (Test-Path 'C:\Program Files\TightVNC\tvnviewer.exe'))

$out | Out-File -Encoding ascii C:\temp-1.txt
