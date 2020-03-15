import argparse
import os
from os import path
import sys
import subprocess
import re
import shutil
from urllib.request import urlretrieve

tested_versions = ["11.3", "0.10.2", "0.9.2"]

ldd_regex = re.compile(r"^.* => (.*) \(0x[a-fA-F0-9]+\)$")

# https://github.com/AppImage/pkg2appimage/blob/master/excludelist
# https://discourse.appimage.org/t/will-a-new-appimage-run-on-older-distributions/84/3
# We assume that among other libs glibc and libstdc++ are installed on the user's system
# But those libraries should be backwards compatible, so you should build löve on,
# as the comment says "the oldest system you are targeting"
lib_whitelist = [
    "libluajit-5.1",
    "libmodplug",
    "libSDL2-2.0",
    "libatomic",
    "libfreetype",
    "libmpg123",
    "libogg",
    "libopenal",
    "libtheoradec",
    "libvorbis",
    "libvorbisfile",
    "libgcc_s",
    "libpng12",
    "libz",
    "libsndio",
    "libpng16",
    "libmng",  # 0.9.2
    "libjpg",  # 0.9.2
    "libtiff",  # 0.9.2
    "libIL",  # 0.9.2
    "libphysfs",  # 0.9.2
    "libwebp",  # 0.9.2
    "libjbig",  # 0.9.2
    "libjpeg",  # 0.9.2
]

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
    ignored = []
    res = subprocess.run(
        ["ldd", binary_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    for line in res.stdout.decode("utf-8").splitlines():
        m = ldd_regex.match(line.strip())
        if m:
            libs.append(m.group(1))
        else:
            ignored.append(line)
            print("Ignoring lib: {}".format(line.strip()))
    return libs, ignored


def get_liblove_name(ignored_libs):
    matches = [lib for lib in ignored_libs if "liblove" in lib]
    if len(matches) == 0:
        sys.exit("Did not find library dependence on liblove (what)")
    elif len(matches) > 1:
        sys.exit("Found multiple dependencies on liblove (what): {}".format(matches))
    return matches[0].strip().split()[0]


def strip_object(src_path, dst_path):
    res = subprocess.run(
        ["strip", "-s", "-o", dst_path, src_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if res.returncode != 0:
        sys.exit(
            "Could not strip object '{}':\n{}".format(
                src_path, res.stderr.decode("utf-8")
            )
        )


def main():
    tested_versions_str = ", ".join(tested_versions)
    parser = argparse.ArgumentParser(
        description="Currently tested with versions: {}".format(tested_versions_str)
    )
    parser.add_argument("lovedirectory", help="The root of the love repo you built in")
    parser.add_argument("appdir", help="The output AppDir directory")
    parser.add_argument("--builddirectory", help="The build directory relative to the love repo, in case it's not the repo root already")
    parser.add_argument("--appimage", help="Create an AppImage too")
    args = parser.parse_args()

    if not path.isdir(args.lovedirectory):
        sys.exit("Love directory does not exist.")

    lovedir = lambda x: path.join(args.lovedirectory, x)
    if args.builddirectory:
        builddir = lambda x: path.join(args.lovedirectory, args.builddirectory, x)
    else:
        builddir = lovedir

    love_exe_path = builddir("src/.libs/love")
    # liblove.so is actually a symlink to some .so file with a name that varies by löve version
    liblove_so_path = builddir("src/.libs/liblove.so")

    if not path.isfile(love_exe_path):
        sys.exit(
            "Could not find src/.libs/love. You built an unsupported version or not at all."
        )
    if not path.isfile(liblove_so_path):
        sys.exit(
            "Could not find src/.libs/liblove.so.0. You built an unsupported version or not at all."
        )

    if path.isdir(args.appdir):
        print("AppDir already exists. Deleting..")
        shutil.rmtree(args.appdir)
    os.mkdir(args.appdir)
    appdir = lambda x: path.join(args.appdir, x)

    os.makedirs(appdir("usr/bin"), exist_ok=True)
    os.makedirs(appdir("usr/lib"), exist_ok=True)

    strip_object(love_exe_path, appdir("usr/bin/love"))
    strip_object(liblove_so_path, appdir("usr/lib/liblove.so"))
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
    love_libs, love_libs_ignored = get_libs(love_exe_path)
    liblove_libs, _liblove_libs_ignored = get_libs(liblove_so_path)
    all_libs = love_libs + liblove_libs
    filtered_libs = list(
        filter(
            lambda l: any(path.basename(l).startswith(w + ".") for w in lib_whitelist),
            all_libs,
        )
    )
    for lib in filtered_libs:
        print("Including:", lib)
    for lib in all_libs:
        if not lib in filtered_libs:
            print("Excluded by filter:", lib)

    for lib in filtered_libs:
        target = path.join(args.appdir, lib[1:])  # [1:] to strip leading slash
        os.makedirs(path.dirname(target), exist_ok=True)
        shutil.copy2(lib, target)

    liblove_symlink_name = get_liblove_name(love_libs_ignored)
    print("Creating symlink '{}'".format(liblove_symlink_name))
    os.symlink("liblove.so", appdir("usr/lib/" + liblove_symlink_name))

    if args.appimage != None:
        appimagetool = shutil.which("appimagetool")
        if appimagetool == None:
            sys.exit("To create an AppImage you need appimagetool in your PATH!")
        print("Building AppImage")
        res = subprocess.run(
            [appimagetool, args.appdir, args.appimage],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if res.returncode != 0:
            sys.exit(
                "appimagetool failed creating an AppImage:\n"
                + res.stderr.decode("utf-8")
            )

    print("Done")


if __name__ == "__main__":
    main()
