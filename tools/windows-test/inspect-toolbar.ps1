# Reads toolbar button geometry/text through a buffer allocated IN the viewer
# process (VirtualAllocEx + WriteProcessMemory + SendMessage + ReadProcessMemory).
# That is the safe way to use toolbar messages that take pointers: the message
# handler writes into its own address space.
Add-Type @"
using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;
using System.Text;
public class W {
  public delegate bool EnumProc(IntPtr h, IntPtr l);
  [DllImport("user32.dll")] public static extern bool EnumWindows(EnumProc cb, IntPtr l);
  [DllImport("user32.dll")] public static extern bool EnumChildWindows(IntPtr parent, EnumProc cb, IntPtr l);
  [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr h, out uint pid);
  [DllImport("user32.dll", CharSet = CharSet.Unicode)] public static extern int GetWindowTextW(IntPtr h, StringBuilder s, int n);
  [DllImport("user32.dll", CharSet = CharSet.Unicode)] public static extern int GetClassNameW(IntPtr h, StringBuilder s, int n);
  [DllImport("user32.dll")] public static extern bool ClientToScreen(IntPtr h, IntPtr pt);
  [DllImport("user32.dll")] public static extern bool GetClientRect(IntPtr h, out RECT r);
  [DllImport("user32.dll", EntryPoint="SendMessageW")] public static extern IntPtr Send(IntPtr h, int msg, IntPtr wp, IntPtr lp);
  [DllImport("kernel32.dll")] public static extern IntPtr OpenProcess(int access, bool inherit, int pid);
  [DllImport("kernel32.dll")] public static extern IntPtr VirtualAllocEx(IntPtr h, IntPtr addr, IntPtr size, int type, int protect);
  [DllImport("kernel32.dll")] public static extern bool VirtualFreeEx(IntPtr h, IntPtr addr, IntPtr size, int type);
  [DllImport("kernel32.dll")] public static extern bool WriteProcessMemory(IntPtr h, IntPtr addr, byte[] buf, IntPtr size, out IntPtr written);
  [DllImport("kernel32.dll")] public static extern bool ReadProcessMemory(IntPtr h, IntPtr addr, byte[] buf, IntPtr size, out IntPtr read);
  [DllImport("kernel32.dll")] public static extern bool CloseHandle(IntPtr h);
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
}
"@

$TB_GETBUTTON      = 0x0417
$TB_BUTTONCOUNT    = 0x0418
$TB_COMMANDTOINDEX = 0x0419
$TB_GETITEMRECT    = 0x041D
$TB_GETBUTTONTEXT  = 0x042D
$TB_GETSTATE       = 0x0412
$TB_GETBITMAP      = 0x042C
$PROCESS_VM = 0x0008 -bor 0x0010 -bor 0x0020 -bor 0x0400
$MEM_COMMIT_RESERVE = 0x1000 -bor 0x2000
$PAGE_RW = 0x04

$lines = New-Object System.Collections.Generic.List[string]
$proc = Get-Process TobonVNCViewer -ErrorAction SilentlyContinue | Where-Object { $_.SessionId -ne 0 } | Select-Object -First 1
if (-not $proc) { "ERROR no viewer process" | Out-File -Encoding ascii C:\temp\toolbar2.txt; exit 1 }
$pid32 = [uint32]$proc.Id
$viewer = [W]::TopLevel($pid32, 'TvnWindowClass')
$toolbars = [W]::Children($viewer, 'ToolbarWindow32')
$tb = $toolbars[0]
$cr = New-Object W+RECT; [W]::GetClientRect($tb, [ref]$cr) | Out-Null
$sb = New-Object System.Text.StringBuilder 512
[W]::GetWindowTextW($viewer, $sb, 512) | Out-Null
$lines.Add("pid=$($proc.Id)")
$lines.Add("title=$($sb.ToString())")
$lines.Add("toolbar_client=$($cr.Right)x$($cr.Bottom)")

$hProc = [W]::OpenProcess($PROCESS_VM, $false, $proc.Id)
if ($hProc -eq [IntPtr]::Zero) { $lines.Add('ERROR OpenProcess failed'); $lines | Out-File -Encoding ascii C:\temp\toolbar2.txt; exit 2 }
$remote = [W]::VirtualAllocEx($hProc, [IntPtr]::Zero, [IntPtr]4096, $MEM_COMMIT_RESERVE, $PAGE_RW)
if ($remote -eq [IntPtr]::Zero) { $lines.Add('ERROR VirtualAllocEx failed'); $lines | Out-File -Encoding ascii C:\temp\toolbar2.txt; exit 3 }

function ReadRemote($size) {
  $buf = New-Object byte[] $size
  $read = [IntPtr]::Zero
  [W]::ReadProcessMemory($hProc, $remote, $buf, [IntPtr]$size, [ref]$read) | Out-Null
  return $buf
}

try {
  $count = [int][W]::Send($tb, $TB_BUTTONCOUNT, [IntPtr]::Zero, [IntPtr]::Zero)
  $lines.Add("buttons=$count")
  for ($i = 0; $i -lt $count; $i++) {
    $zero = New-Object byte[] 64
    $w = [IntPtr]::Zero
    [W]::WriteProcessMemory($hProc, $remote, $zero, [IntPtr]64, [ref]$w) | Out-Null
    $ok = [W]::Send($tb, $TB_GETBUTTON, [IntPtr]$i, $remote)
    if ($ok -eq [IntPtr]::Zero) { $lines.Add("button[$i] GETBUTTON failed"); continue }
    $b = ReadRemote 32
    $iBitmap = [BitConverter]::ToInt32($b, 0)
    $idCommand = [BitConverter]::ToInt32($b, 4)
    $fsState = $b[8]; $fsStyle = $b[9]
    $state = [int64][W]::Send($tb, $TB_GETSTATE, [IntPtr]$idCommand, [IntPtr]::Zero)
    $image = [int64][W]::Send($tb, $TB_GETBITMAP, [IntPtr]$idCommand, [IntPtr]::Zero)
    $lines.Add(("button[{0}] cmd={1} iBitmap={2} style=0x{3:X2} state=0x{4:X} image={5}" -f `
      $i, $idCommand, $iBitmap, $fsStyle, $state, $image))
  }

  # geometry + text of the remote-input button
  $idx = [int][W]::Send($tb, $TB_COMMANDTOINDEX, [IntPtr]217, [IntPtr]::Zero)
  $lines.Add("remoteinput_index=$idx")
  if ($idx -ge 0) {
    $zero = New-Object byte[] 64
    $w = [IntPtr]::Zero
    [W]::WriteProcessMemory($hProc, $remote, $zero, [IntPtr]64, [ref]$w) | Out-Null
    $ok = [W]::Send($tb, $TB_GETITEMRECT, [IntPtr]$idx, $remote)
    $b = ReadRemote 16
    $l = [BitConverter]::ToInt32($b, 0); $t = [BitConverter]::ToInt32($b, 4)
    $r = [BitConverter]::ToInt32($b, 8); $bt = [BitConverter]::ToInt32($b, 12)
    $pt = New-Object byte[] 8
    [BitConverter]::GetBytes($l).CopyTo($pt, 0)
    [BitConverter]::GetBytes($t).CopyTo($pt, 4)
    $wp = [IntPtr]::Zero
    [W]::WriteProcessMemory($hProc, $remote, $pt, [IntPtr]8, [ref]$wp) | Out-Null
    [W]::ClientToScreen($tb, $remote) | Out-Null
    $screen = ReadRemote 8
    $sx = [BitConverter]::ToInt32($screen, 0); $sy = [BitConverter]::ToInt32($screen, 4)
    $lines.Add("remoteinput_client_rect=$l,$t,$r,$bt (raw=$ok)")
    $lines.Add("remoteinput_screen_topleft=$sx,$sy size=$($r-$l)x$($bt-$t)")
    $lines.Add("remoteinput_click=$([int]($sx + ($r-$l)/2)),$([int]($sy + ($bt-$t)/2))")

    $zero = New-Object byte[] 1024
    $w = [IntPtr]::Zero
    [W]::WriteProcessMemory($hProc, $remote, $zero, [IntPtr]1024, [ref]$w) | Out-Null
    $len = [int][W]::Send($tb, $TB_GETBUTTONTEXT, [IntPtr]217, $remote)
    if ($len -gt 0) {
      $txt = ReadRemote ([Math]::Min($len * 2 + 2, 1024))
      $lines.Add("remoteinput_text='" + [Text.Encoding]::Unicode.GetString($txt).TrimEnd([char]0) + "'")
    } else {
      $lines.Add("remoteinput_text=<none, len=$len>")
    }
  }
} finally {
  [W]::VirtualFreeEx($hProc, $remote, [IntPtr]::Zero, 0x8000) | Out-Null
  [W]::CloseHandle($hProc) | Out-Null
}

$lines | Out-File -Encoding ascii C:\temp\toolbar2.txt
