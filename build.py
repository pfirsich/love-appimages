import argparse
import os
from os import path
import sys
import subprocess
import re
import shutil
from urllib.request import urlretrieve

ldd_regex = re.compile(r"^.* => (.*) \(0x[a-fA-F0-9]+\)$")

wrapper = """#!/bin/sh
cd "$OWD"
love_files=$(find $APPDIR/usr/bin -type f -name "*.love")
if [ -z "$love_files" ]; then
	$APPDIR/usr/bin/love "$@"
else
	$APPDIR/usr/bin/love --fused "$love_files" "$@"
fi
"""


def get_libs(binary_path):
    libs = []
    res = subprocess.run(["ldd", binary_path], capture_output=True)
    for line in res.stdout.decode("utf-8").splitlines():
        m = ldd_regex.match(line.strip())
        if m:
            libs.append(m.group(1))
        else:
            print("Ignoring lib: {}".format(line.strip()))
    return libs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("lovedirectory", help="The root of the love repo you built in")
    parser.add_argument("appdir", help="The output AppDir directory")
    parser.add_argument("--appimage", help="Create an AppImage too.")
    args = parser.parse_args()

    if not path.isdir(args.lovedirectory):
        sys.exit("Love directory does not exist.")
    lovedir = lambda x: path.join(args.lovedirectory, x)

    love_exe_path = lovedir("src/.libs/love")
    liblove_so_path = lovedir("src/.libs/liblove.so.0.0.0")

    if not path.isfile(love_exe_path):
        sys.exit(
            "Could not find src/.libs/love. You built an unsupported version or not at all."
        )
    if not path.isfile(liblove_so_path):
        sys.exit(
            "Could not find src/.libs/liblove.so.0.0.0. You built an unsupported version or not at all."
        )

    if path.isdir(args.appdir):
        print("AppDir already exists. Deleting..")
        shutil.rmtree(args.appdir)
    os.mkdir(args.appdir)
    appdir = lambda x: path.join(args.appdir, x)

    os.makedirs(appdir("usr/bin"), exist_ok=True)
    os.makedirs(appdir("usr/lib"), exist_ok=True)

    shutil.copy2(love_exe_path, appdir("usr/bin"))
    shutil.copy2(liblove_so_path, appdir("usr/lib/liblove.so.0"))
    shutil.copy2(lovedir("platform/unix/love.svg"), appdir("."))
    shutil.copy2(lovedir("license.txt"), appdir("."))

    wrapper_path = appdir("usr/bin/wrapper-love")
    with open(wrapper_path, "w") as f:
        f.write(wrapper)
    os.chmod(wrapper_path, 0o755)

    print("Downloading current AppRun..")
    apprun_url = "https://github.com/AppImage/AppImageKit/releases/download/continuous/AppRun-x86_64"
    apprun_path = appdir("AppRun")
    urlretrieve(apprun_url, apprun_path)
    os.chmod(apprun_path, 0o755)

    print("Building love.desktop")
    with open(lovedir("platform/unix/love.desktop")) as f:
        love_desktop = f.read()
    love_desktop_sub = re.sub(r"Exec=.*\n", "Exec=wrapper-love %F\n", love_desktop)
    if love_desktop == love_desktop_sub:
        sys.exit("Could not replace Exec field in desktop file")
    with open(appdir("love.desktop"), "w") as f:
        f.write(love_desktop_sub)

    print("Copying libs..")
    libs = []
    libs.extend(get_libs(love_exe_path))
    libs.extend(get_libs(liblove_so_path))

    for lib in libs:
        target = path.join(args.appdir, lib[1:])  # [1:] to strip leading slash
        os.makedirs(path.dirname(target), exist_ok=True)
        shutil.copy2(lib, target)

    if args.appimage != None:
        appimagetool = shutil.which("appimagetool")
        if appimagetool == None:
            sys.exit("To create an AppImage you need appimagetool in your PATH!")
        print("Building AppImage")
        res = subprocess.run(
            [appimagetool, args.appdir, args.appimage], capture_output=True
        )
        if res.returncode != 0:
            sys.exit(
                "appimagetool failed creating an AppImage:\n"
                + res.stderr.decode("utf-8")
            )

    print("Done")


if __name__ == "__main__":
    main()
