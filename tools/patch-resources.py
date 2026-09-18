#!/usr/bin/env python3
"""
TobonVNC fork: patch the viewer resource scripts (UTF-16LE RC files).

Every replacement is asserted (count must match) so a silent miss is
impossible. Run from the repo root: python3 tools/patch-resources.py
"""
import re
import sys
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAIN = os.path.join(REPO, "tvnviewer", "tvnviewer.rc")
CHS = os.path.join(REPO, "tvnviewer", "tvnviewer_chs.rc")


def read_utf16(path):
    with open(path, "rb") as f:
        data = f.read()
    assert data[:2] == b"\xff\xfe", "no UTF-16LE BOM in %s" % path
    return data[2:].decode("utf-16-le")


def write_utf16(path, text):
    with open(path, "wb") as f:
        f.write(b"\xff\xfe" + text.encode("utf-16-le"))


def rep(text, old, new, count=1, tag=""):
    found = text.count(old)
    assert found == count, "%s: expected %d x %r, found %d" % (tag, count, old, found)
    return text.replace(old, new)


# --------------------------------------------------------------------------
# 1. New bitmap resource + configuration-dialog layout (both languages)
# --------------------------------------------------------------------------

BITMAP_OLD = 'IDB_TOOLBAR             BITMAP                  "res\\\\toolbar.bmp"\r\n'
BITMAP_NEW = (BITMAP_OLD +
              'IDB_TOOLBAR_INPUT       BITMAP                  "res\\toolbar_input.bmp"\r\n')

CONF_DIALOG_SHIFTS = [
    ("IDD_CONFIGURATION DIALOGEX 0, 0, 221, 216",
     "IDD_CONFIGURATION DIALOGEX 0, 0, 221, 230"),
    ("7,7,207,42,WS_GROUP", "7,7,207,56,WS_GROUP"),
    ("7,53,207,50,WS_GROUP", "7,67,207,50,WS_GROUP"),
    ("16,65,127,10", "16,79,127,10"),
    ("IDC_ENUMCON,151,63,43,12", "IDC_ENUMCON,151,77,43,12"),
    ("UDS_NOTHOUSANDS,203,61,11,14", "UDS_NOTHOUSANDS,203,75,11,14"),
    ("IDC_BCLEAR_LIST,51,81,119,14", "IDC_BCLEAR_LIST,51,95,119,14"),
    ("7,107,207,29,WS_GROUP", "7,121,207,29,WS_GROUP"),
    ("16,119,132,10", "16,133,132,10"),
    ("IDC_EREVCON,151,117,43,12", "IDC_EREVCON,151,131,43,12"),
    ("UDS_NOTHOUSANDS,203,115,11,14", "UDS_NOTHOUSANDS,203,129,11,14"),
    ("7,141,207,48", "7,155,207,48"),
    ("16,154,131,10", "16,168,131,10"),
    ("IDC_EVERBLVL,151,151,33,13", "IDC_EVERBLVL,151,165,33,13"),
    ("UDS_NOTHOUSANDS,203,150,11,14", "UDS_NOTHOUSANDS,203,164,11,14"),
    ("IDC_STATIC,16,171,27,10", "IDC_STATIC,16,185,27,10"),
    ("IDC_ELOGGING,50,169,117,12", "IDC_ELOGGING,50,183,117,12"),
    ("IDC_OPEN_LOG_FOLDER_BUTTON,173,168,34,14", "IDC_OPEN_LOG_FOLDER_BUTTON,173,182,34,14"),
    ("IDOK,56,195,50,14", "IDOK,56,209,50,14"),
    ("IDCANCEL,116,195,50,14", "IDCANCEL,116,209,50,14"),
]

NEW_CHECKBOX = ('    CONTROL         "Start connections in view-only mode",'
                'IDC_CSTARTVIEWONLY,"Button",'
                'BS_AUTOCHECKBOX | WS_GROUP | WS_TABSTOP,16,47,150,10\r\n')


def patch_configuration_dialog(text, tag):
    """Shift the layout below the User Interface group and add the new check box."""
    start = text.index("IDD_CONFIGURATION DIALOGEX")
    end = text.index("\r\nEND\r\n", start) + len("\r\nEND\r\n")
    block = text[start:end]

    anchor = '"Button",BS_AUTOCHECKBOX | WS_TABSTOP,16,33,160,10\r\n'
    assert block.count(anchor) == 1, "%s: warn-at-switch anchor not found" % tag
    block = block.replace(anchor, anchor + NEW_CHECKBOX)

    for old, new in CONF_DIALOG_SHIFTS:
        assert block.count(old) == 1, "%s: layout anchor %r not unique/found" % (tag, old)
        block = block.replace(old, new)

    return text[:start] + block + text[end:]


# --------------------------------------------------------------------------
# 2. Strings, accelerators, version info (English resource only)
# --------------------------------------------------------------------------

def patch_main(text):
    tag = "main"

    text = rep(text, BITMAP_OLD, BITMAP_NEW, tag=tag)
    text = patch_configuration_dialog(text, tag)

    # New menu item / tooltip strings, next to IDS_TB_CONFIGURATION.
    old = '    IDS_TB_CONFIGURATION    "&Configuration..."\r\nEND\r\n'
    new = ('    IDS_TB_CONFIGURATION    "&Configuration..."\r\n'
           '    IDS_TB_REMOTEINPUT      "Allow remote &input (mouse && keyboard)\\tCtrl+Alt+Shift+K"\r\n'
           'END\r\n'
           '\r\n'
           'STRINGTABLE\r\n'
           'BEGIN\r\n'
           '    IDS_TB_REMOTEINPUT_TIP_BLOCKED "Remote input is BLOCKED (view only) - click to allow mouse and keyboard"\r\n'
           '    IDS_TB_REMOTEINPUT_TIP_ENABLED "Remote input is ENABLED - click to switch back to view only"\r\n'
           'END\r\n')
    text = rep(text, old, new, tag=tag)

    # Accelerator for the new command.
    old = '    "E",            ID_TRANSF_FILES,        VIRTKEY, SHIFT, CONTROL, ALT, NOINVERT\r\n'
    new = (old +
           '    "K",            ID_CONN_REMOTE_INPUT,   VIRTKEY, SHIFT, CONTROL, ALT, NOINVERT\r\n')
    text = rep(text, old, new, tag=tag)

    # Version info.
    text = rep(text, " FILEVERSION 2,8,81,0", " FILEVERSION 2,8,81,1", tag=tag)
    text = rep(text, " PRODUCTVERSION 2,8,81,0", " PRODUCTVERSION 2,8,81,1", tag=tag)
    text = rep(text, 'VALUE "FileVersion", "2, 8, 81, 0"',
               'VALUE "FileVersion", "2, 8, 81, 1"', tag=tag)
    text = rep(text, 'VALUE "ProductVersion", "2, 8, 81, 0"',
               'VALUE "ProductVersion", "2.8.81.1 (TobonVNC 1.0)"', tag=tag)
    text = rep(text, 'VALUE "InternalName", "tvnviewer"',
               'VALUE "InternalName", "TobonVNCViewer"', tag=tag)
    text = rep(text, 'VALUE "OriginalFilename", "tvnviewer.exe"',
               'VALUE "OriginalFilename", "TobonVNCViewer.exe"', tag=tag)
    text = rep(text, 'VALUE "LegalCopyright", "Copyright (C) 2023 GlavSoft LLC."',
               'VALUE "LegalCopyright", "Copyright (C) 2023 GlavSoft LLC. '
               'Modifications (C) 2026 Daniel Tobon. GNU GPL v2."', tag=tag)

    # About dialog: keep upstream credits, describe this build and the new
    # default. Coordinates of the text block are rearranged to fit 3+ lines.
    old = ('    LTEXT           "Copyright (C) 2023 GlavSoft LLC.\\nAll Rights Reserved.",'
           'IDC_STATIC,107,38,189,19\r\n'
           '    LTEXT           "",IDC_STATIC_LICENSING,107,64,189,10\r\n')
    new = ('    LTEXT           "Copyright (C) 2023 GlavSoft LLC.\\n'
           'TobonVNC modifications (C) 2026 Daniel Tobon.\\n'
           'Based on TightVNC, distributed under the GNU GPL v2.",'
           'IDC_STATIC,107,30,189,30\r\n'
           '    LTEXT           "",IDC_STATIC_LICENSING,107,60,189,10\r\n')
    text = rep(text, old, new, tag=tag)

    old_para = ('    LTEXT           "We provide technical support, development and '
                'customization services on TightVNC.\\nThe source code is available '
                'commercially as well, if the GPL license is not acceptable.\\n'
                'Please visit the Web site for more information on our products.",'
                'IDC_STATIC,13,81,283,26\r\n')
    new_para = ('    LTEXT           "TobonVNC Viewer is a modified build of the '
                'TightVNC Viewer (GNU GPL v2).\\nNew connections start in view-only '
                'mode: remote mouse and keyboard stay\\nblocked until you allow them '
                'with the lock button (Ctrl+Alt+Shift+K).\\n'
                'Source code: github.com/danieltobon21/tightvnc",'
                'IDC_STATIC,13,72,283,40\r\n')
    text = rep(text, old_para, new_para, tag=tag)

    text = rep(text, '"Visit the Web Site",IDC_VISIT_WEB_SITE_BUTTON',
               '"TightVNC Web Site",IDC_VISIT_WEB_SITE_BUTTON', tag=tag)
    text = rep(text, '"Commercial Licensing",IDC_ORDER_SUPPORT_BUTTON',
               '"Source Code (Fork)",IDC_ORDER_SUPPORT_BUTTON', tag=tag)

    # Login dialog blurb.
    text = rep(text, '"TightVNC is cross-platform remote control software."',
               '"TobonVNC Viewer for Windows - free remote control software."',
               tag=tag)
    text = rep(text,
               '"Its source code is available to everyone, either freely\\n'
               '(GNU GPL license) or commercially (with no GPL restrictions)."',
               '"Modified build of the TightVNC Viewer (GNU GPL v2), by Daniel Tobon.\\n'
               'New sessions start in view-only mode: remote input is blocked."',
               tag=tag)

    # Command line help: program name plus a note about the start mode.
    n = text.count("  tvnviewer")
    assert n == 6, "%s: expected 6 occurrences of the program name, found %d" % (tag, n)
    text = text.replace("  tvnviewer", "  TobonVNCViewer")
    old = "  -viewonly\\tView only (input ignored).\\r\\n"
    new = ("  -viewonly\\tView only (input ignored).\\r\\n"
           "\\r\\n"
           "This build starts every connection in view-only mode (remote input\\r\\n"
           "blocked). Use the lock button of the toolbar, the View menu item or\\r\\n"
           "Ctrl+Alt+Shift+K to allow remote mouse and keyboard input.\\r\\n")
    text = rep(text, old, new, tag=tag)

    # URLs: keep crediting upstream, point licensing to the GPL and the fork.
    text = rep(text, '"http://www.tightvnc.com/?f=va"', '"https://www.tightvnc.com/"', tag=tag)
    text = rep(text, '"http://www.tightvnc.com/licensing/?f=va"',
               '"https://github.com/danieltobon21/tightvnc"', tag=tag)
    text = rep(text, '"http://www.tightvnc.com/licensing/?f=vc"',
               '"https://www.gnu.org/licenses/old-licenses/gpl-2.0.html"', tag=tag)

    return text


def patch_chs(text):
    tag = "chs"

    # Note: bitmap and accelerator resources are declared only in the English
    # resource script (resources are looked up by id, so they are reachable
    # from any locale).
    text = patch_configuration_dialog(text, tag)

    # The new strings are not translated; keep them in English.
    found = re.search(r'[ ]+IDS_TB_CONFIGURATION[ ]+"[^"]*"\r\nEND\r\n', text)
    assert found, "%s: IDS_TB_CONFIGURATION block not found" % tag
    new = (found.group(0)[:-len("END\r\n")] +
           '    IDS_TB_REMOTEINPUT      "Allow remote &input (mouse && keyboard)\\tCtrl+Alt+Shift+K"\r\n'
           'END\r\n'
           '\r\n'
           'STRINGTABLE\r\n'
           'BEGIN\r\n'
           '    IDS_TB_REMOTEINPUT_TIP_BLOCKED "Remote input is BLOCKED (view only) - click to allow mouse and keyboard"\r\n'
           '    IDS_TB_REMOTEINPUT_TIP_ENABLED "Remote input is ENABLED - click to switch back to view only"\r\n'
           'END\r\n')
    text = text[:found.start()] + new + text[found.end():]

    n = text.count("  tvnviewer")
    assert n >= 1, "%s: program name in the help text not found" % tag
    text = text.replace("  tvnviewer", "  TobonVNCViewer")

    return text


# --------------------------------------------------------------------------
# 3. Rebranding of every user-visible string (both languages)
# --------------------------------------------------------------------------

def rebrand(text):
    # Protect the upstream URLs while renaming the product.
    text = text.replace("tightvnc.com", "\x00UPSTREAM\x00")
    assert "TightVNC" in text
    text = text.replace("TightVNC", "TobonVNC")
    text = text.replace("\x00UPSTREAM\x00", "tightvnc.com")
    return text


# References to the upstream project that must keep its name after rebranding.
UPSTREAM_FIXUPS = [
    ("of the TobonVNC Viewer (GNU GPL v2)", "of the TightVNC Viewer (GNU GPL v2)"),
    ("Based on TobonVNC, distributed", "Based on TightVNC, distributed"),
    ("a modified TobonVNC Viewer", "a modified TightVNC Viewer"),
    ("where TobonVNC Server or compatible", "where TightVNC Server or compatible"),
]


def apply_fixups(text, tag):
    for old, new in UPSTREAM_FIXUPS:
        if old in text:
            text = text.replace(old, new)
    return text


def main():
    for path, patch in ((MAIN, patch_main), (CHS, patch_chs)):
        text = read_utf16(path)
        before = text
        text = patch(text)
        text = rebrand(text)
        text = apply_fixups(text, path)
        assert text != before
        write_utf16(path, text)
        print("patched %s (%d chars)" % (os.path.relpath(path, REPO), len(text)))


if __name__ == "__main__":
    main()
