# love-appimages

I made this, because there are no official AppImages for versions before löve 11 and because I think even those are somewhat complicated (the love script in the root is unnecessary, because AppRun already does it), they could make packaging games with them a tiny bit easier and parameters are not handled correctly (e.g. `./love.AppImage --fused mygame.love` will not work).

My approach in gathering the shared libraries is not very clever. I just blindly include everything ldd identifies as a dependency. I would be glad if someone could help me clean this up competently. But considering some other sources of AppImages (such as [polyamory](https://github.com/megagrump/polyamory), which is otherwise really awesome) provide incomplete ones, I do not mind having mine be ~5MB bigger and give people trouble less often, when the whole point of AppImages is to not give people trouble because of missing libraries.

I also wanted to automate the process (so everyone could do it) and implicitely document it that way, which is done through the [build.py](build.py) script, which you can point to a löve repository after a successful build (see the bottom of this README on notes on building older versions).

The [Releases](https://github.com/pfirsich/love-appimages/releases) page provides AppImages that I built using that script.

## Creating an AppImage of Your Game from a löve AppImage
You can use this if you want to: [makelove](https://github.com/pfirsich/makelove) (coming in the next few days if not already there)

Please note that you will only be able to follow these steps if you are using Linux. This will also not work on WSL, because of a lack of FUSE support and therefore a lack of support for AppImages altogether.

With my AppImages your game will run in fused mode, if it's run from inside an AppImage. If you do not want this, edit `usr/bin/wrapper-love`.

Unless your game relies on a bug, you can pick the latest major release your game was made for (e.g. if your game was made for version 0.10.1, pick 0.10.2). Then be lucky and find the AppImage for that version on the [Releases](https://github.com/pfirsich/love-appimages/releases) page and download it.

Extract the AppImage:
```
chmod +x love_11_3.AppImage
./love_11_3.AppImage --appimage-extract
```
This will extract the AppImage into the `squashfs-root` subdirectory of your current working directory. That directory is called the `AppDir`.

Put your game's `.love` file into the `usr/bin` subdirectory.

You **must not** delete `license.txt`, as stated by the [Game Distribution](https://love2d.org/wiki/Game_Distribution) löve wiki page.

If you have a custom icon, delete `love.svg` and `.DirIcon` and place your icon in that directory. Supported file formats are `.png` and `.svg`.

### The `.desktop` File
Then just adjust and rename the love.desktop file to your liking (but do not end up with multiple .desktop files!):
- You should probably change `Name`, `Comment`.
- Remove `MimeType` (as your löve application will probably not open files passed to it) and `NoDisplay` (because you want it to show up in launchers).
- You may modify the parameters in `Exec` (`%f` to forward only a single parameter, or remove the parameter entirely if you don't want or need them), but you **must** call `wrapper-love` there.
- You probably want to adjust `Categories` to `Categories=Game;` (note the mandatory trailing semicolon!).
- If you have a custom icon, specify it's name (without the file extension!), e.g. `Icon=gameicon`.

Use this template if you like:
```
[Desktop Entry]
Name=Pain of Blood Destruction - Ultimate Savage Edition
Comment=Rescue the world with a piece of gum!
Exec=wrapper-love %F
Type=Application
Categories=Game;
Terminal=false
Icon=flowerpot
```

### Handling Shared Libraries
If your game wants to shared libraries via FFI, you need to put them to any path added to `LD_LIBRARY_PATH` (see here: [AppRun.c](https://github.com/AppImage/AppImageKit/blob/2d36ff7f6627f9a2e52039e3c4ef0928958f62ed/src/AppRun.c#L175), e.g.  `usr/lib`)

If your game wants to load Lua modules from shared libraries, you need to add them anywhere into your AppDir (I recommend `usr/lib` again) and add that path to `package.cpath`:
```lua
local APPDIR = os.getenv("APPDIR")
if APPDIR then
    package.cpath = package.cpath .. ";" .. APPDIR .. "/usr/lib/?.so"
end
```
The `APPDIR` environment variable is set by the `AppRun` executable.

### Packaging
To turn your AppDir into an AppImage again, download the [appimagetool](https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage) and simply invoke it like this to produce `MySuperGame.AppImage`:
```
appimagetool MyAppDir MySuperGame.AppImage
```

## Notes on Building Older Versions

Some older versions might not build right away and here I collected some notes on how to make it work (thanks of course to slime for all the help).
If you find remarks to add here or try out versions I have not tried building (see releases and `tested_versions` in [build.py](build.py)), feel free to create a pull request or create an issue!

### Building 0.10.2
Your distro might use luajit 2.1 for it's luajit dev packages, while löve was made for luajit 2.0. Some defines might have been removed, which will result in your compilation to fail after a regular checkout of the 0.10.2 tag.

It works for me if I do this:
```bash
cd src/libraries/luasocket/libluasocket
sed -i 's/luaL_reg/luaL_Reg/g' *
```

Alternatively, just download [the patch](fix_0_10_2.patch) and apply it:
```
git apply fix_0_10_2.patch
```

### Building 0.9.2
See here: https://bitbucket.org/rude/love/issues/1537/some-problems-when-compile-love-092

Summary: What I am recommending here is not safe. If you know how to do it better or actually observe these crashes, contact me.

To apply those changes, download [the patch](fix_0_9_2.patch) and apply it:
```
git apply fix_0_9_2.patch
```
