#!/usr/bin/env python3
"""
TobonVNC fork: drop project entries that point to files which do not exist.

The upstream snapshot this fork is based on removed the "extended desktop
size" / "set desktop size" implementation but left the corresponding entries
in the Visual Studio project files, so viewer-core (and the server projects)
fail with C1083 "Cannot open source file". Nothing in the sources references
those files, so removing the stale entries is the minimal fix.

Usage: python3 tools/clean-stale-project-entries.py [--check]
"""
import glob
import os
import re
import sys


def normalise(project_dir, include):
    return os.path.normpath(os.path.join(project_dir, include.replace("\\", "/")))


def clean_project(path, check_only=False):
    project_dir = os.path.dirname(path)
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        text = f.read()

    removed = []

    def repl_self_closing(match):
        kind, include = match.group(1), match.group(2)
        if not os.path.exists(normalise(project_dir, include)):
            removed.append(include)
            return ""
        return match.group(0)

    text = re.sub(r'\s*<(ClCompile|ClInclude|ResourceCompile|None)\s+Include="([^"]+)"\s*/>',
                  repl_self_closing, text)

    def repl_block(match):
        kind, include = match.group(1), match.group(2)
        if not os.path.exists(normalise(project_dir, include)):
            removed.append(include)
            return ""
        return match.group(0)

    text = re.sub(r'\s*<(ClCompile|ClInclude|ResourceCompile|None)\s+Include="([^"]+)">\s*'
                  r'<Filter>[^<]*</Filter>\s*</\1>',
                  repl_block, text)

    if removed and not check_only:
        with open(path, "w", encoding="utf-8-sig", newline="") as f:
            f.write(text)
    return removed


def main():
    check_only = "--check" in sys.argv
    total = 0
    for path in sorted(glob.glob("*/*.vcxproj") + glob.glob("*/*.vcxproj.filters")):
        removed = clean_project(path, check_only)
        if removed:
            total += len(removed)
            print("%-45s removed: %s" % (path, ", ".join(sorted(removed))))
    print("%s %d stale entries" % ("would remove" if check_only else "removed", total))


if __name__ == "__main__":
    main()
