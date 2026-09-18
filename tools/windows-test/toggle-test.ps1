# Regression test after the re-entrancy fix: several padlock clicks, checking the
# toolbar state, the window title and whether clicks/keys reach the server.
Add-Type @"
using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;
using System.Text;
public class Q {
  public delegate bool EnumProc(IntPtr h, IntPtr l);
  [DllImport("user32.dll")] public static extern bool EnumWindows(EnumProc cb, IntPtr l);
  [DllImport("user32.dll")] public static extern bool EnumChildWindows(IntPtr parent, EnumProc cb, IntPtr l);
  [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr h, out uint pid);
  [DllImport("user32.dll", CharSet = CharSet.Unicode)] public static extern int GetWindowTextW(IntPtr h, StringBuilder s, int n);
  [DllImport("user32.dll", CharSet = CharSet.Unicode)] public static extern int GetClassNameW(IntPtr h, StringBuilder s, int n);
  [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h, out RECT r);
  [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h, int c);
  [DllImport("user32.dll", EntryPoint="SendMessageW")] public static extern IntPtr Send(IntPtr h, int msg, IntPtr wp, IntPtr lp);
  [StructLayout(LayoutKind.Sequential)] public struct RECT { public int Left, Top, Right, Bottom; }
  public static IntPtr TopLevel(uint pid, string cls) {
    IntPtr found = IntPtr.Zero;
    EnumWindows(delegate(IntPtr h, IntPtr l) {
      uint p; GetWindowThreadProcessId(h, out p);
      if (p == pid) {
        StringBuilder c = new StringBuilder(256); GetClassNameW(h, c, 256);
        if (c.ToString() == cls) { found = h; return false; }
      }
      return true;
    }, IntPtr.Zero);
    return found;
  }
  public static List<IntPtr> Children(IntPtr parent, string cls) {
    List<IntPtr> found = new List<IntPtr>();
    EnumChildWindows(parent, delegate(IntPtr h, IntPtr l) {
      StringBuilder c = new StringBuilder(256); GetClassNameW(h, c, 256);
      if (cls == null || c.ToString() == cls) found.Add(h);
      return true;
    }, IntPtr.Zero);
    return found;
  }
  public static int LParam(int lo, int hi) { return (hi << 16) | (lo & 0xFFFF); }
}
"@

$WM_MOUSEMOVE = 0x0200; $WM_LBUTTONDOWN = 0x0201; $WM_LBUTTONUP = 0x0202
$WM_KEYDOWN = 0x0100; $WM_KEYUP = 0x0101
$TB_GETSTATE = 0x0412; $TB_GETBITMAP = 0x042C

$log = New-Object System.Collections.Generic.List[string]
function Note($t) { $script:log.Add(((Get-Date).ToString('HH:mm:ss.fff') + "  " + $t)) }

$proc = Get-Process TobonVNCViewer -ErrorAction SilentlyContinue | Where-Object { $_.SessionId -ne 0 } | Select-Object -First 1
if (-not $proc) { "ERROR no viewer process" | Out-File -Encoding ascii C:\temp\test7.txt; exit 1 }
$viewer = [Q]::TopLevel([uint32]$proc.Id, 'TvnWindowClass')
[Q]::ShowWindow($viewer, 9) | Out-Null
Start-Sleep -Milliseconds 900
$toolbars = [Q]::Children($viewer, 'ToolbarWindow32')
$tb = $toolbars[0]
$desk = [IntPtr]::Zero
foreach ($h in [Q]::Children($viewer, 'TvnWindowClass')) { $desk = $h; break }
$dr = New-Object Q+RECT; [Q]::GetWindowRect($desk, [ref]$dr) | Out-Null

"pid=$($proc.Id) viewer=$viewer toolbar=$tb desktop=$desk" | Out-File -Encoding ascii C:\temp\test7.txt
function Title() { $sb = New-Object System.Text.StringBuilder 512; [Q]::GetWindowTextW($viewer, $sb, 512) | Out-Null; $sb.ToString() }
function Alive() { return [bool](Get-Process -Id $proc.Id -ErrorAction SilentlyContinue) }
function State($label) {
  if (-not (Alive)) { Note "$label : PROCESS IS GONE"; return }
  $state = [int64][Q]::Send($tb, $TB_GETSTATE, [IntPtr]217, [IntPtr]::Zero)
  $bmp = [int64][Q]::Send($tb, $TB_GETBITMAP, [IntPtr]217, [IntPtr]::Zero)
  Note ("{0}: state=0x{1:X} image={2} | {3}" -f $label, $state, $bmp, (Title))
}
function ClickPadlock() {
  $x = 424; $y = 11
  [Q]::Send($tb, $WM_MOUSEMOVE, [IntPtr]::Zero, [IntPtr][Q]::LParam($x, $y)) | Out-Null
  Start-Sleep -Milliseconds 60
  [Q]::Send($tb, $WM_LBUTTONDOWN, [IntPtr]1, [IntPtr][Q]::LParam($x, $y)) | Out-Null
  Start-Sleep -Milliseconds 80
  [Q]::Send($tb, $WM_LBUTTONUP, [IntPtr]::Zero, [IntPtr][Q]::LParam($x, $y)) | Out-Null
  Start-Sleep -Milliseconds 450
}
function DeskVoice($label) {
  $cx = [int](($dr.Right - $dr.Left) / 2); $cy = [int](($dr.Bottom - $dr.Top) / 2)
  [Q]::Send($desk, $WM_MOUSEMOVE, [IntPtr]::Zero, [IntPtr][Q]::LParam($cx, $cy)) | Out-Null
  Start-Sleep -Milliseconds 90
  [Q]::Send($desk, $WM_LBUTTONDOWN, [IntPtr]1, [IntPtr][Q]::LParam($cx, $cy)) | Out-Null
  Start-Sleep -Milliseconds 70
  [Q]::Send($desk, $WM_LBUTTONUP, [IntPtr]::Zero, [IntPtr][Q]::LParam($cx, $cy)) | Out-Null
  Start-Sleep -Milliseconds 90
  [Q]::Send($desk, $WM_KEYDOWN, [IntPtr]0x41, [IntPtr]0x001E0001) | Out-Null
  Start-Sleep -Milliseconds 70
  [Q]::Send($desk, $WM_KEYUP, [IntPtr]0x41, [IntPtr]0xC01E0001) | Out-Null
  Note "$label : click + key sent to the remote desktop"
}

if ((Title) -notlike '*VIEW ONLY*') { ClickPadlock; Note 'normalised to view only' }
State 'START'
DeskVoice 'PHASE-A-VIEWONLY'
Start-Sleep -Milliseconds 400

for ($round = 1; $round -le 4; $round++) {
  ClickPadlock
  State "AFTER-PADLOCK-CLICK-$round"
  if (-not (Alive)) { break }
  if ($round -eq 1 -or $round -eq 3) {
    DeskVoice "PHASE-B$round-ENABLED"
    Start-Sleep -Milliseconds 400
  }
}

State 'FINAL'
DeskVoice 'PHASE-C-VIEWONLY'
Start-Sleep -Milliseconds 400
State 'END'
Note ("viewer alive at the end: " + (Alive))
Note 'TEST COMPLETE'
$log | Out-File -Encoding ascii -Append C:\temp\test7.txt
